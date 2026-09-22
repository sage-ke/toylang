"""
AST (Abstract Syntax Tree) node definitions.

The parser builds a tree of these objects to represent the structure
of the program. Each class is a plain data container — the actual
"doing" happens later in interpreter.py, which walks this tree.

There are two families:
  - Expr nodes: things that produce a VALUE (5 + 3, x, "hello")
  - Stmt nodes: things that DO something (print x;, var x = 5;, if...)
"""

from dataclasses import dataclass, field
from typing import Any


# ----------------------------------------------------------------------
# Expressions (produce a value)
# ----------------------------------------------------------------------

class Expr:
    pass


@dataclass
class Literal(Expr):
    value: Any  # a number, string, True/False, or None


@dataclass
class Variable(Expr):
    name: Any  # Token


@dataclass
class Assign(Expr):
    name: Any     # Token
    value: Expr


@dataclass
class Unary(Expr):
    operator: Any  # Token
    right: Expr


@dataclass
class Binary(Expr):
    left: Expr
    operator: Any  # Token
    right: Expr


@dataclass
class Logical(Expr):
    left: Expr
    operator: Any  # Token ("and" / "or")
    right: Expr


@dataclass
class Grouping(Expr):
    expression: Expr


@dataclass
class Call(Expr):
    callee: Expr
    paren: Any        # Token, for error reporting
    arguments: list


# ----------------------------------------------------------------------
# Statements (do something)
# ----------------------------------------------------------------------

class Stmt:
    pass


@dataclass
class ExpressionStmt(Stmt):
    expression: Expr


@dataclass
class PrintStmt(Stmt):
    expression: Expr


@dataclass
class VarStmt(Stmt):
    name: Any          # Token
    initializer: Expr  # may be None


@dataclass
class BlockStmt(Stmt):
    statements: list


@dataclass
class IfStmt(Stmt):
    condition: Expr
    then_branch: Stmt
    else_branch: Stmt  # may be None


@dataclass
class WhileStmt(Stmt):
    condition: Expr
    body: Stmt


@dataclass
class FunctionStmt(Stmt):
    name: Any          # Token
    params: list       # list of Tokens
    body: list         # list of Stmt


@dataclass
class ReturnStmt(Stmt):
    keyword: Any       # Token, for error reporting
    value: Expr        # may be None