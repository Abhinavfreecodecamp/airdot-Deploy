from typing import Any, List, Optional
import inspect, re, string, pandas


class SklearnPredictor:
    def __init__(
        self,
        skpredictor: Any,
        name: Optional[str] = None,
        python_version: Optional[str] = None,
        python_packages: Optional[List[str]] = None,
        system_packages: Optional[List[str]] = None,
        dataframe_mode: bool = False,
        example_dataframe: Optional[pandas.DataFrame] = None,
    ):
        self.skpredictor = skpredictor
        self.python_version = python_version
        self.python_packages = python_packages
        self.system_packages = system_packages
        self.dataframe_mode = dataframe_mode
        self.example_dataframe = example_dataframe
        if name:
            self.name = name
        else:
            self.name = self.guessModelName()

    def guessModelName(self):
        try:
            codeContexts = [f.code_context for f in inspect.stack()]
            for ccList in codeContexts:
                if not ccList:
                    continue
                for cc in ccList:
                    captures = re.search(r"\.(deploy|train)\(([^\s,)]+)", cc)
                    if captures:
                        return captures.group(2)
        except Exception as _:
            pass
        return None

    def guessNumArgs(self):
        for i in range(1, 25):
            try:
                args = [j for j in range(i)]
                self.skpredictor.predict([args])  # type: ignore
                return i
            except Exception:
                pass
        return None

    def makeDeployment(self):
        skpredictor = self.skpredictor

        varName = "skpredictor"
        if self.name:
            varName = self.name
        globals()[
            varName
        ] = skpredictor  # put the same value to globals so it acts more like a notebook cell

        guessedArgCount = self.guessNumArgs()
        if guessedArgCount:
            letters = list(string.ascii_lowercase)
            argNames = letters[0:guessedArgCount]
            argsWithTypes = ", ".join([f"{ltr}: float" for ltr in argNames])
            funcSource = "\n".join(
                [
                    f"def predict({argsWithTypes}) -> float:",
                    f"  return {varName}.predict([[{', '.join(argNames)}]])[0]",
                    f"",
                ]
            )
        else:
            funcSource = "\n".join(
                [
                    f"def predict(*args: Any):",
                    f"  return {varName}.predict([args])[0]",
                    f"",
                ]
            )

        exec(funcSource)
        deploy_function = locals()["predict"]

        return True
