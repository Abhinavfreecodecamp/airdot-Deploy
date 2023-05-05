import inspect
from typing import Callable, Any, List, Dict
import tempfile, os
import ast
import re

from airdot.collection.collections import namespace, python_function_prop


def get_function_properties(func, imported_modules):
    props = python_function_prop()
    if not callable(func):
        raise Exception("Object is not a callable function")
    else:
        props.name = func.__name__
        props.source = get_function_source_code(func)
        props.argNames = get_func_args_name(func)
        props.argTypes = annotation_to_type_str(func.__annotations__)
        nsCollection = namespace()
        nsCollection = get_function_dep(func, nsCollection, imported_modules)
        props.namespaceFunctions = nsCollection.functions
        props.namespaceVars = nsCollection.vars
        props.namespaceVarsDesc = get_string_values(nsCollection.vars)
        props.namespaceImports = nsCollection.imports
        props.namespaceFroms = nsCollection.froms
        props.namespaceModules = list(set(nsCollection.allModules))
        props.customInitCode = nsCollection.customInitCode
    return props


def get_string_values(args: Dict[str, Any]):
    newDict: Dict[str, str] = {}
    for k, v in args.items():
        strVal = re.sub(r"\s+", " ", str(v))
        if type(v) is bytes:
            strVal = "Binary data"
        elif len(strVal) > 200:
            strVal = strVal[0:200] + "..."
        newDict[k] = strVal
    return newDict


def unindent(source: str) -> str:
    leadingWhitespaces = len(source) - len(source.lstrip())
    if leadingWhitespaces == 0:
        return source
    newLines = [line[leadingWhitespaces:] for line in source.split("\n")]
    return "\n".join(newLines)


def get_function_source_code(func: Callable = None):
    if not callable(func):
        return None
    return unindent(inspect.getsource(func))


def get_func_args_name(func: Callable = None):
    argSpec = inspect.getfullargspec(func)
    if argSpec.varargs:
        return ["..."]
    if argSpec.args:
        return argSpec.args
    noArgs: List[str] = []
    return noArgs


def annotation_to_type_str(annotations: Dict[str, Any]):
    annoStrs: Dict[str, str] = {}
    for name, tClass in annotations.items():
        try:
            if tClass == Any:
                annoStrs[name] = "Any"
            else:
                annoStrs[name] = tClass.__name__
        except:
            pass
    return annoStrs


def has_state(obj: Any) -> bool:
    try:
        return len(obj.__dict__) > 0
    except:
        return False


def collect_byte_obj(maybeFuncVar: Any, maybeFuncVarName: str, collection: namespace):
    tmpFilePath = os.path.join(tempfile.gettempdir(), "btyd.pkl")
    maybeFuncVar.save_model(tmpFilePath)
    with open(tmpFilePath, "rb") as f:
        collection.vars[maybeFuncVarName + "_state"] = f.read()
    collection.customInitCode.append(
        f"""
    with open('data/{maybeFuncVarName}_state.tmp', 'wb') as fo:
    with open('data/{maybeFuncVarName}_state.pkl', 'rb') as fi:
    fo.write(pickle.load(fi))
    {maybeFuncVarName} = {maybeFuncVar.__class__.__name__}()
    {maybeFuncVarName}.load_model('data/{maybeFuncVarName}_state.tmp')
    """.strip()
    )
    collection.froms[maybeFuncVar.__class__.__name__] = maybeFuncVar.__module__
    collection.imports["pickle"] = "pickle"
    collection.imports["btyd"] = "btyd"


def is_imported_module(imported_modules, module_name):
    for item in imported_modules:
        pkg_name, _ = item.split("==")
        if pkg_name == module_name:
            return True
    return False


def get_function_dep(func: Callable[..., Any], collection: namespace, imported_modules):
    if not callable(func):
        return collection
    collection = get_function_args(func, collection)
    globalsDict = func.__globals__  # type: ignore
    allNames = func.__code__.co_names + func.__code__.co_freevars
    for maybeFuncVarName in allNames:
        if maybeFuncVarName in globalsDict:
            maybeFuncVar = globalsDict[maybeFuncVarName]
            if "__module__" in dir(maybeFuncVar):
                if (
                    maybeFuncVar.__module__ == "__main__"
                ):  # the user's functionsprint('Users func')
                    argNames = list(maybeFuncVar.__code__.co_varnames or [])
                    funcSig = f"{maybeFuncVar.__name__}({', '.join(argNames)})"
                    if funcSig not in collection.functions:
                        collection.functions[funcSig] = inspect.getsource(maybeFuncVar)
                        get_function_dep(maybeFuncVar, collection, imported_modules)
                else:  # functions imported by the user from elsewhere\
                    if inspect.isclass(maybeFuncVar):
                        collection.froms[maybeFuncVarName] = maybeFuncVar.__module__  #
                        collection.allModules.append(maybeFuncVar.__module__)
                    elif callable(maybeFuncVar) and not has_state(maybeFuncVar):
                        collection.froms[maybeFuncVarName] = maybeFuncVar.__module__  #
                        collection.allModules.append(maybeFuncVar.__module__)
                    elif "btyd.fitters" in f"{maybeFuncVar.__module__}":
                        collection = collect_byte_obj(
                            maybeFuncVar, maybeFuncVarName, collection
                        )
                    elif isinstance(maybeFuncVar, object):
                        collection.froms[
                            maybeFuncVar.__class__.__name__
                        ] = maybeFuncVar.__module__
                        collection.allModules.append(maybeFuncVar.__module__)
                        collection.vars[maybeFuncVarName] = maybeFuncVar
                    else:
                        collection.froms[
                            maybeFuncVarName
                        ] = f"NYI: {maybeFuncVar.__module__}"
            elif str(maybeFuncVar).startswith("<module"):
                collection.imports[maybeFuncVarName] = maybeFuncVar.__name__
                collection.allModules.append(maybeFuncVar.__name__)
            elif inspect.isclass(maybeFuncVar):
                collection.froms[maybeFuncVarName] = maybeFuncVar.__module__  #
                collection.allModules.append(maybeFuncVar.__module__)
            else:
                collection.vars[maybeFuncVarName] = maybeFuncVar
    return collection


def is_valid_package(pkg_str: str):
    return len(pkg_str.split(".")) > 0


def collect_mod_name(func, modName: str, collection: namespace):
    if modName in func.__globals__:
        gMod = func.__globals__[modName]
        if hasattr(gMod, "__module__"):
            collection.froms[modName] = gMod.__module__
        else:
            collection.imports[modName] = gMod.__name__
            collection.allModules.append(func.__globals__[modName].__name__)
    return collection


def parse_ast_name_to_id(astName: Any):
    if hasattr(astName, "attr"):
        return astName.value.id
    else:
        return astName.id


def get_function_args(func: Callable[..., Any], collection: namespace):
    try:
        sigAst = ast.parse(inspect.getsource(func)).body[0]  # type: ignore
        for a in sigAst.args.args:  # type: ignore
            if a.annotation is None:  # type: ignore
                continue
            collection = collect_mod_name(func, parse_ast_name_to_id(a.annotation), collection=collection)  # type: ignore
        if sigAst.returns is not None:  # type: ignore
            collection = collect_mod_name(func, parse_ast_name_to_id(sigAst.returns), collection=collection)  # type: ignore
        return collection
    except Exception as err:
        strErr = f"{err}"
        if (
            strErr != "could not get source code"
        ):  # triggers when deploying pure sklearn model
            print(f"Warning: failed parsing type annotations: {err}")
