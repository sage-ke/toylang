"""
The Parser.

Job: take the flat list of Tokens from the Scanner and build a tree
(the AST) that represents the program's structure and enforces
grammar rules.

This is a "recursive descent" parser: each grammar rule becomes a
method, and rules call each other in order of precedence (lowest to
highest binding power). Roughly, from loosest to tightest:

    program    -> declaration* EOF
    declaration-> funDecl | varDecl | statement
    statement  -> exprStmt | printStmt | block | ifStmt | whileStmt
                  | returnStmt
    expression -> assignment
    assignment -> IDENTIFIER "=" assignment | logic_or
    logic_or   -> logic_and ( "or" logic_and )*
    logic_and  -> equality ( "and" equality )*
    equality   -> comparison ( ( "!=" | "==" ) comparison )*
    comparison -> term ( ( "<" | "<=" | ">" | ">=" ) term )*
    term       -> factor ( ( "+" | "-" ) factor )*
    factor     -> unary ( ( "*" | "/" ) unary )*
    unary      -> ( "!" | "-" ) unary | call
    call       -> primary ( "(" arguments? ")" )*
    primary    -> NUMBER | STRING | "true" | "false" | "nil"
                  | "(" expression ")" | IDENTIFIER
"""

from tokens import TokenType as TT
from ast_nodes import (
    Expr, Literal, Variable, Assign, Unary, Binary, Logical, Grouping, Call,
    Stmt, ExpressionStmt, PrintStmt, VarStmt, BlockStmt, IfStmt, WhileStmt,
    FunctionStmt, ReturnStmt,
)
from errors import ParseError


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> list:
        """Parse the whole program into a list of statements."""
        statements = []
        while not self._is_at_end():
            statements.append(self._declaration())
        return statements

    # ------------------------------------------------------------------
    # Declarations & statements
    # ------------------------------------------------------------------

    def _declaration(self) -> Stmt:
        if self._match(TT.FUN):
            return self._function("function")
        if self._match(TT.VAR):
            return self._var_declaration()
        return self._statement()

    def _function(self, kind: str) -> FunctionStmt:
        name = self._consume(TT.IDENTIFIER, f"Expect {kind} name.")
        self._consume(TT.LEFT_PAREN, f"Expect '(' after {kind} name.")
        params = []
        if not self._check(TT.RIGHT_PAREN):
            while True:
                params.append(self._consume(TT.IDENTIFIER, "Expect parameter name."))
                if not self._match(TT.COMMA):
                    break
        self._consume(TT.RIGHT_PAREN, "Expect ')' after parameters.")
        self._consume(TT.LEFT_BRACE, f"Expect '{{' before {kind} body.")
        body = self._block()
        return FunctionStmt(name, params, body)

    def _var_declaration(self) -> Stmt:
        name = self._consume(TT.IDENTIFIER, "Expect variable name.")
        initializer = None
        if self._match(TT.EQUAL):
            initializer = self._expression()
        self._consume(TT.SEMICOLON, "Expect ';' after variable declaration.")
        return VarStmt(name, initializer)

    def _statement(self) -> Stmt:
        if self._match(TT.PRINT):
            return self._print_statement()
        if self._match(TT.IF):
            return self._if_statement()
        if self._match(TT.WHILE):
            return self._while_statement()
        if self._match(TT.FOR):
            return self._for_statement()
        if self._match(TT.RETURN):
            return self._return_statement()
        if self._match(TT.LEFT_BRACE):
            return BlockStmt(self._block())
        return self._expression_statement()

    def _print_statement(self) -> Stmt:
        value = self._expression()
        self._consume(TT.SEMICOLON, "Expect ';' after value.")
        return PrintStmt(value)

    def _if_statement(self) -> Stmt:
        self._consume(TT.LEFT_PAREN, "Expect '(' after 'if'.")
        condition = self._expression()
        self._consume(TT.RIGHT_PAREN, "Expect ')' after if condition.")
        then_branch = self._statement()
        else_branch = None
        if self._match(TT.ELSE):
            else_branch = self._statement()
        return IfStmt(condition, then_branch, else_branch)

    def _while_statement(self) -> Stmt:
        self._consume(TT.LEFT_PAREN, "Expect '(' after 'while'.")
        condition = self._expression()
        self._consume(TT.RIGHT_PAREN, "Expect ')' after condition.")
        body = self._statement()
        return WhileStmt(condition, body)

    def _for_statement(self) -> Stmt:
        """
        Parses:  for ( initializer ; condition ; increment ) body

        Desugars into an equivalent while-loop, e.g.

            for (var i = 0; i < 5; i = i + 1) { print i; }

        becomes

            {
                var i = 0;
                while (i < 5) {
                    { print i; }
                    i = i + 1;
                }
            }

        No new AST node or interpreter logic is needed — the parser
        just builds the while-loop shape directly out of existing
        pieces (VarStmt, WhileStmt, BlockStmt, ExpressionStmt).
        """
        self._consume(TT.LEFT_PAREN, "Expect '(' after 'for'.")

        # ---- initializer: `var x = 0;` or `x = 0;` or `;` (nothing) ----
        if self._match(TT.SEMICOLON):
            initializer = None
        elif self._match(TT.VAR):
            initializer = self._var_declaration()  # consumes its own ';'
        else:
            initializer = self._expression_statement()  # consumes its own ';'

        # ---- condition: defaults to `true` if omitted ----
        condition = None
        if not self._check(TT.SEMICOLON):
            condition = self._expression()
        self._consume(TT.SEMICOLON, "Expect ';' after loop condition.")
        if condition is None:
            condition = Literal(True)

        # ---- increment: runs at the end of each iteration ----
        increment = None
        if not self._check(TT.RIGHT_PAREN):
            increment = self._expression()
        self._consume(TT.RIGHT_PAREN, "Expect ')' after for clauses.")

        body = self._statement()

        # Build from the inside out:
        # 1. If there's an increment, run it after the body each iteration.
        if increment is not None:
            body = BlockStmt([body, ExpressionStmt(increment)])

        # 2. Wrap body + condition into a while loop.
        body = WhileStmt(condition, body)

        # 3. If there's an initializer, run it once before the loop starts.
        if initializer is not None:
            body = BlockStmt([initializer, body])

        return body

    def _return_statement(self) -> Stmt:
        keyword = self._previous()
        value = None
        if not self._check(TT.SEMICOLON):
            value = self._expression()
        self._consume(TT.SEMICOLON, "Expect ';' after return value.")
        return ReturnStmt(keyword, value)

    def _block(self) -> list:
        statements = []
        while not self._check(TT.RIGHT_BRACE) and not self._is_at_end():
            statements.append(self._declaration())
        self._consume(TT.RIGHT_BRACE, "Expect '}' after block.")
        return statements

    def _expression_statement(self) -> Stmt:
        expr = self._expression()
        self._consume(TT.SEMICOLON, "Expect ';' after expression.")
        return ExpressionStmt(expr)

    # ------------------------------------------------------------------
    # Expressions, lowest to highest precedence
    # ------------------------------------------------------------------

    def _expression(self) -> Expr:
        return self._assignment()

    def _assignment(self) -> Expr:
        expr = self._or()

        if self._match(TT.EQUAL):
            equals = self._previous()
            value = self._assignment()
            if isinstance(expr, Variable):
                return Assign(expr.name, value)
            raise ParseError(equals, "Invalid assignment target.")

        return expr

    def _or(self) -> Expr:
        expr = self._and()
        while self._match(TT.OR):
            operator = self._previous()
            right = self._and()
            expr = Logical(expr, operator, right)
        return expr

    def _and(self) -> Expr:
        expr = self._equality()
        while self._match(TT.AND):
            operator = self._previous()
            right = self._equality()
            expr = Logical(expr, operator, right)
        return expr

    def _equality(self) -> Expr:
        expr = self._comparison()
        while self._match(TT.BANG_EQUAL, TT.EQUAL_EQUAL):
            operator = self._previous()
            right = self._comparison()
            expr = Binary(expr, operator, right)
        return expr

    def _comparison(self) -> Expr:
        expr = self._term()
        while self._match(TT.GREATER, TT.GREATER_EQUAL, TT.LESS, TT.LESS_EQUAL):
            operator = self._previous()
            right = self._term()
            expr = Binary(expr, operator, right)
        return expr

    def _term(self) -> Expr:
        expr = self._factor()
        while self._match(TT.PLUS, TT.MINUS):
            operator = self._previous()
            right = self._factor()
            expr = Binary(expr, operator, right)
        return expr

    def _factor(self) -> Expr:
        expr = self._unary()
        while self._match(TT.STAR, TT.SLASH):
            operator = self._previous()
            right = self._unary()
            expr = Binary(expr, operator, right)
        return expr

    def _unary(self) -> Expr:
        if self._match(TT.BANG, TT.MINUS):
            operator = self._previous()
            right = self._unary()
            return Unary(operator, right)
        return self._call()

    def _call(self) -> Expr:
        expr = self._primary()
        while True:
            if self._match(TT.LEFT_PAREN):
                expr = self._finish_call(expr)
            else:
                break
        return expr

    def _finish_call(self, callee: Expr) -> Expr:
        arguments = []
        if not self._check(TT.RIGHT_PAREN):
            while True:
                arguments.append(self._expression())
                if not self._match(TT.COMMA):
                    break
        paren = self._consume(TT.RIGHT_PAREN, "Expect ')' after arguments.")
        return Call(callee, paren, arguments)

    def _primary(self) -> Expr:
        if self._match(TT.FALSE):
            return Literal(False)
        if self._match(TT.TRUE):
            return Literal(True)
        if self._match(TT.NIL):
            return Literal(None)
        if self._match(TT.NUMBER, TT.STRING):
            return Literal(self._previous().literal)
        if self._match(TT.IDENTIFIER):
            return Variable(self._previous())
        if self._match(TT.LEFT_PAREN):
            expr = self._expression()
            self._consume(TT.RIGHT_PAREN, "Expect ')' after expression.")
            return Grouping(expr)

        raise ParseError(self._peek(), "Expect expression.")

    # ------------------------------------------------------------------
    # Token stream helpers
    # ------------------------------------------------------------------

    def _match(self, *types) -> bool:
        for t in types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _check(self, type_) -> bool:
        if self._is_at_end():
            return False
        return self._peek().type == type_

    def _advance(self):
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        return self._peek().type == TT.EOF

    def _peek(self):
        return self.tokens[self.current]

    def _previous(self):
        return self.tokens[self.current - 1]

    def _consume(self, type_, message: str):
        if self._check(type_):
            return self._advance()
        raise ParseError(self._peek(), message)
    