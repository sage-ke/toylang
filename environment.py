"""
Environment: keeps track of variable names -> values.

Each block/function call gets its own Environment, which points back
to its "enclosing" (parent) environment. Looking up a variable checks
the current scope first, then walks outward — this is how a variable
defined outside a function is still visible inside it, and how a
local variable inside a block temporarily "shadows" an outer one.
"""

from errors import RuntimeErrorToy


class Environment:
    def __init__(self, enclosing: "Environment" = None):
        self.values = {}
        self.enclosing = enclosing

    def define(self, name: str, value):
        """Create a new variable in THIS scope (var x = ...)."""
        self.values[name] = value

    def get(self, name_token):
        name = name_token.lexeme
        if name in self.values:
            return self.values[name]
        if self.enclosing is not None:
            return self.enclosing.get(name_token)
        raise RuntimeErrorToy(name_token, f"Undefined variable '{name}'.")

    def assign(self, name_token, value):
        """Assign to an EXISTING variable (x = ...), searching outward."""
        name = name_token.lexeme
        if name in self.values:
            self.values[name] = value
            return
        if self.enclosing is not None:
            self.enclosing.assign(name_token, value)
            return
        raise RuntimeErrorToy(name_token, f"Undefined variable '{name}'.")