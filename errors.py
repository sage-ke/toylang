"""
Custom exceptions so we can give readable error messages instead of raw
Python tracebacks.
"""


class ToyLangError(Exception):
    """Base class for all errors raised by the interpreter pipeline."""
    pass


class ScanError(ToyLangError):
    def __init__(self, line: int, message: str):
        super().__init__(f"[line {line}] Scan error: {message}")
        self.line = line
        self.message = message


class ParseError(ToyLangError):
    def __init__(self, token, message: str):
        loc = "end" if token.type.name == "EOF" else f"'{token.lexeme}'"
        super().__init__(f"[line {token.line}] Parse error at {loc}: {message}")
        self.token = token
        self.message = message


class RuntimeErrorToy(ToyLangError):
    """Named to avoid clashing with Python's built-in RuntimeError."""
    def __init__(self, token, message: str):
        super().__init__(f"[line {token.line}] Runtime error: {message}")
        self.token = token
        self.message = message