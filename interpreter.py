"""
The Interpreter.

Job: walk the AST produced by the Parser and actually DO what it
says — this is where "5 + 3" turns into the number 8, and where
"print x;" actually prints something to the screen.

This is a "tree-walking" interpreter: it directly recurses over the
tree each time the program runs, rather than compiling to a faster
intermediate bytecode first (that's the next step up in sophistication,
covered in the second half of Crafting Interpreters).
"""

import time
from tokens import TokenType as TT
from ast_nodes import (
    Literal, Variable, Assign, Unary, Binary, Logical, Grouping, Call,
    ExpressionStmt, PrintStmt, VarStmt, BlockStmt, IfStmt, WhileStmt,
    FunctionStmt, ReturnStmt,
)
from environment import Environment
from errors import RuntimeErrorToy


class ReturnException(Exception):
    """Used internally to unwind the call stack on a `return` statement."""
    def __init__(self, value):
        self.value = value


class ToyFunction:
    """A user-defined function (created by `fun name(...) { ... }`)."""

    def __init__(self, declaration: FunctionStmt, closure: Environment):
        self.declaration = declaration
        self.closure = closure

    def arity(self):
        return len(self.declaration.params)

    def call(self, interpreter, arguments):
        env = Environment(self.closure)
        for param, arg in zip(self.declaration.params, arguments):
            env.define(param.lexeme, arg)

        try:
            interpreter.execute_block(self.declaration.body, env)
        except ReturnException as ret:
            return ret.value
        return None

    def __repr__(self):
        return f"<fn {self.declaration.name.lexeme}>"


class ClockFunction:
    """Built-in `clock()` function — returns seconds since epoch."""
    def arity(self):
        return 0

    def call(self, interpreter, arguments):
        return time.time()

    def __repr__(self):
        return "<native fn clock>"


class Interpreter:
    def __init__(self):
        self.globals = Environment()
        self.environment = self.globals
        self.globals.define("clock", ClockFunction())

    def interpret(self, statements: list):
        for stmt in statements:
            self._execute(stmt)

    # ------------------------------------------------------------------
    # Statement execution
    # ------------------------------------------------------------------

    def _execute(self, stmt):
        method = getattr(self, f"_exec_{type(stmt).__name__}")
        method(stmt)

    def _exec_ExpressionStmt(self, stmt: ExpressionStmt):
        self._evaluate(stmt.expression)

    def _exec_PrintStmt(self, stmt: PrintStmt):
        value = self._evaluate(stmt.expression)
        print(self._stringify(value))

    def _exec_VarStmt(self, stmt: VarStmt):
        value = None
        if stmt.initializer is not None:
            value = self._evaluate(stmt.initializer)
        self.environment.define(stmt.name.lexeme, value)

    def _exec_BlockStmt(self, stmt: BlockStmt):
        self.execute_block(stmt.statements, Environment(self.environment))

    def _exec_IfStmt(self, stmt: IfStmt):
        if self._is_truthy(self._evaluate(stmt.condition)):
            self._execute(stmt.then_branch)
        elif stmt.else_branch is not None:
            self._execute(stmt.else_branch)

    def _exec_WhileStmt(self, stmt: WhileStmt):
        while self._is_truthy(self._evaluate(stmt.condition)):
            self._execute(stmt.body)

    def _exec_FunctionStmt(self, stmt: FunctionStmt):
        function = ToyFunction(stmt, self.environment)
        self.environment.define(stmt.name.lexeme, function)

    def _exec_ReturnStmt(self, stmt: ReturnStmt):
        value = None
        if stmt.value is not None:
            value = self._evaluate(stmt.value)
        raise ReturnException(value)

    def execute_block(self, statements: list, env: Environment):
        previous = self.environment
        try:
            self.environment = env
            for stmt in statements:
                self._execute(stmt)
        finally:
            self.environment = previous

    # ------------------------------------------------------------------
    # Expression evaluation
    # ------------------------------------------------------------------

    def _evaluate(self, expr):
        method = getattr(self, f"_eval_{type(expr).__name__}")
        return method(expr)

    def _eval_Literal(self, expr: Literal):
        return expr.value

    def _eval_Grouping(self, expr: Grouping):
        return self._evaluate(expr.expression)

    def _eval_Variable(self, expr: Variable):
        return self.environment.get(expr.name)

    def _eval_Assign(self, expr: Assign):
        value = self._evaluate(expr.value)
        self.environment.assign(expr.name, value)
        return value

    def _eval_Logical(self, expr: Logical):
        left = self._evaluate(expr.left)
        if expr.operator.type == TT.OR:
            if self._is_truthy(left):
                return left
        else:  # AND
            if not self._is_truthy(left):
                return left
        return self._evaluate(expr.right)

    def _eval_Unary(self, expr: Unary):
        right = self._evaluate(expr.right)
        if expr.operator.type == TT.MINUS:
            self._check_number_operand(expr.operator, right)
            return -right
        if expr.operator.type == TT.BANG:
            return not self._is_truthy(right)
        return None

    def _eval_Binary(self, expr: Binary):
        left = self._evaluate(expr.left)
        right = self._evaluate(expr.right)
        op = expr.operator.type

        if op == TT.PLUS:
            if isinstance(left, float) and isinstance(right, float):
                return left + right
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            raise RuntimeErrorToy(expr.operator, "Operands must be two numbers or two strings.")
        if op == TT.MINUS:
            self._check_number_operands(expr.operator, left, right)
            return left - right
        if op == TT.STAR:
            self._check_number_operands(expr.operator, left, right)
            return left * right
        if op == TT.SLASH:
            self._check_number_operands(expr.operator, left, right)
            if right == 0:
                raise RuntimeErrorToy(expr.operator, "Division by zero.")
            return left / right
        if op == TT.GREATER:
            self._check_number_operands(expr.operator, left, right)
            return left > right
        if op == TT.GREATER_EQUAL:
            self._check_number_operands(expr.operator, left, right)
            return left >= right
        if op == TT.LESS:
            self._check_number_operands(expr.operator, left, right)
            return left < right
        if op == TT.LESS_EQUAL:
            self._check_number_operands(expr.operator, left, right)
            return left <= right
        if op == TT.EQUAL_EQUAL:
            return self._is_equal(left, right)
        if op == TT.BANG_EQUAL:
            return not self._is_equal(left, right)

        return None

    def _eval_Call(self, expr: Call):
        callee = self._evaluate(expr.callee)
        arguments = [self._evaluate(arg) for arg in expr.arguments]

        if not hasattr(callee, "call"):
            raise RuntimeErrorToy(expr.paren, "Can only call functions.")
        if len(arguments) != callee.arity():
            raise RuntimeErrorToy(
                expr.paren,
                f"Expected {callee.arity()} arguments but got {len(arguments)}."
            )
        return callee.call(self, arguments)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _is_truthy(self, value) -> bool:
        """nil and false are falsy; everything else (including 0) is truthy."""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        return True

    def _is_equal(self, a, b) -> bool:
        return a == b

    def _check_number_operand(self, operator, operand):
        if isinstance(operand, float):
            return
        raise RuntimeErrorToy(operator, "Operand must be a number.")

    def _check_number_operands(self, operator, left, right):
        if isinstance(left, float) and isinstance(right, float):
            return
        raise RuntimeErrorToy(operator, "Operands must be numbers.")

    def _stringify(self, value) -> str:
        if value is None:
            return "nil"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, float):
            if value.is_integer():
                return str(int(value))
            return str(value)
        return str(value)