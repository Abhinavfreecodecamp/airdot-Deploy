import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parents[2]))

import hashlib
import pickle
from google.cloud import storage
from typing import Dict, Tuple, Any, cast
import zstd
import pprint
import yaml

from google.cloud import storage
from google.oauth2 import service_account
from googleapiclient import discovery
from datetime import timedelta

SCHEMA_VERSION = 1
MAX_DESCRIPTION_SIZE = 5000
NULL_BYTE = b"\x00"

from airdot.helpers.minio_helper import minio_helper


def serializeZstd(obj) -> Tuple[bytes, str, int]:
    pklData = pickle.dumps(obj)
    contentHash = f"sha1:{hashlib.sha1(pklData).hexdigest()}"
    objSize = len(pklData)
    return (pklData, contentHash, objSize)


def isBinaryFile(content: bytes) -> bool:
    return NULL_BYTE in content

def decodeString(b: bytes) -> str:
    for encoding in ("ascii", "utf8", "latin1"):
        try:
            return b.decode(encoding)
        except UnicodeDecodeError:
            pass
    return b.decode("ascii", "ignore")

def describeObject(
    obj: Any, maxDepth: int, remainingCharacters=MAX_DESCRIPTION_SIZE
) -> Dict[str, Any]:
    objT = type(obj)
    if objT is dict and maxDepth > 0:
        ret = {}
        for k, v in obj.items():
            ret[k] = describeObject(v, maxDepth - 1, max(0, remainingCharacters))
            remainingCharacters -= len(str(ret[k]))
        return ret
    elif objT is bytes:
        if isBinaryFile(obj):
            obj = "Unknown binary file"
        else:
            obj = decodeString(obj)
            objT = type(obj)
    description = (
        obj[:remainingCharacters].strip()
        if type(obj) is str
        else pprint.pformat(obj, depth=1, width=100, compact=True)[
            :remainingCharacters
        ].strip()
    )
    return {
        "module": objT.__module__,
        "class": objT.__name__,
        "description": description,
    }

def repr_str(dumper: yaml.Dumper, data: str):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)

def toFileStubDict(contentHash: str, objDesc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "_": "MBFileStub",
        "contentHash": contentHash,
        "metadata": objDesc,
        "schemaVersion": SCHEMA_VERSION,
    }

def toYaml(contentHash: str, fileSize: int, objDesc: Dict[str, Any]) -> str:
    metadata: Dict[str, Any] = {"file_size": fileSize, "object": objDesc}

    obj = toFileStubDict(contentHash, metadata)
    yaml.add_representer(str, repr_str)
    return yaml.dump(obj, width=1000)

def putSecureData(bucket_id, open_id, token, data: bytes, desc: str, endpoint:str):
    try:
        minio_helper_obj = minio_helper(endpoint=endpoint)
        minio_helper_obj.create_bucket(bucket_name=bucket_id)
        minio_helper_obj.put_object(
            bucket=bucket_id,
            key=f"{open_id}/{desc}.pkl",
            data=data
        )
        return True
    except Exception as e:
        print("failed to upload data object. Please try again")
        return False

def uploadRuntimeObject(bucket_id, open_id, obj, desc: str, endpoint:str):
    (data, contentHash, objSize) = serializeZstd(obj)
    response = putSecureData(bucket_id, open_id, data, desc)
    if response:
        yamlObj = toYaml(contentHash, objSize, describeObject(obj, 1))
        return yamlObj  # need to think a way to save complete yamlObj
    else:
        return "None"


# uploading
def make_and_upload_data_files(bucket_id, open_id, pyState, endpoint):
    dataFiles: Dict[str, str] = {}
    if pyState.namespaceVars and pyState.namespaceVarsDesc:
        for nName, nVal in pyState.namespaceVars.items():
            dataFiles[f"{nName}.pkl"] = uploadRuntimeObject(
                bucket_id, open_id, nVal, nName, endpoint
            )
    return dataFiles
