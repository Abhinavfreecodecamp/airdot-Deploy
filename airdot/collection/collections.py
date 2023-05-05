# python imports
from typing import Dict, List, Any, Optional
from datetime import datetime


class namespace:
    def __init__(self):
        self.functions: Dict[str, str] = {}
        self.vars: Dict[str, Any] = {}
        self.imports: Dict[str, str] = {}
        self.froms: Dict[str, str] = {"*": "typing"}
        self.allModules: List[str] = []
        self.customInitCode: List[str] = []


class python_function_prop:
    excludeFromDict: List[str] = ["errors"]

    def __init__(self):
        self.source: Optional[str] = None
        self.name: Optional[str] = None
        self.argNames: Optional[List[str]] = None
        self.argTypes: Optional[Dict[str, str]] = None
        self.namespaceVarsDesc: Optional[Dict[str, str]] = None
        self.namespaceFunctions: Optional[Dict[str, str]] = None
        self.namespaceImports: Optional[Dict[str, str]] = None
        self.namespaceFroms: Optional[Dict[str, str]] = None
        self.namespaceModules: Optional[List[str]] = None
        self.errors: Optional[List[str]] = None
        self.namespaceVars: Optional[Dict[str, Any]] = None
        self.customInitCode: Optional[List[str]] = None


class authentication:
    def __init__(self) -> None:
        self.refresh_token: Optional[str] = None
        self.token_time: Optional[datetime] = datetime(2000, 1, 1)


class source_file_props:
    def __init__(self, name: str, contents: str):
        self.name = name
        self.contents = contents

    def asDict(self):
        return {"name": self.name, "contents": self.contents}
