"""
The Scanner (a.k.a. Lexer).

Job: take raw source text (a string) and turn it into a flat list of
Tokens. It does NOT understand grammar or meaning yet — it just
recognizes "words" like numbers, identifiers, strings and symbols.

Example:
    "x = 5 + 3;"
    -> [IDENTIFIER(x), EQUAL, NUMBER(5), PLUS, NUMBER(3), SEMICOLON, EOF]
"""

from tokens import Token, TokenType, KEYWORDS
from errors import ScanError


class Scanner:
    def __init__(self, source: str):
        self.source = source
        self.tokens: list[Token] = []
        self.start = 0    # start of the current lexeme being scanned
        self.current = 0  # current character being looked at
        self.line = 1

    def scan_tokens(self) -> list[Token]:
        while not self._is_at_end():
            self.start = self.current
            self._scan_token()

        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _scan_token(self):
        c = self._advance()

        if c == "(":
            self._add_token(TokenType.LEFT_PAREN)
        elif c == ")":
            self._add_token(TokenType.RIGHT_PAREN)
        elif c == "{":
            self._add_token(TokenType.LEFT_BRACE)
        elif c == "}":
            self._add_token(TokenType.RIGHT_BRACE)
        elif c == ",":
            self._add_token(TokenType.COMMA)
        elif c == ";":
            self._add_token(TokenType.SEMICOLON)
        elif c == "+":
            self._add_token(TokenType.PLUS)
        elif c == "-":
            self._add_token(TokenType.MINUS)
        elif c == "*":
            self._add_token(TokenType.STAR)
        elif c == "/":
            if self._match("/"):
                # Line comment: skip to end of line
                while self._peek() != "\n" and not self._is_at_end():
                    self._advance()
            else:
                self._add_token(TokenType.SLASH)
        elif c == "=":
            self._add_token(TokenType.EQUAL_EQUAL if self._match("=") else TokenType.EQUAL)
        elif c == "!":
            self._add_token(TokenType.BANG_EQUAL if self._match("=") else TokenType.BANG)
        elif c == "<":
            self._add_token(TokenType.LESS_EQUAL if self._match("=") else TokenType.LESS)
        elif c == ">":
            self._add_token(TokenType.GREATER_EQUAL if self._match("=") else TokenType.GREATER)
        elif c in (" ", "\r", "\t"):
            pass  # ignore whitespace
        elif c == "\n":
            self.line += 1
        elif c == '"':
            self._string()
        elif c.isdigit():
            self._number()
        elif c.isalpha() or c == "_":
            self._identifier()
        else:
            raise ScanError(self.line, f"Unexpected character '{c}'")

    def _identifier(self):
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()
        text = self.source[self.start:self.current]
        token_type = KEYWORDS.get(text, TokenType.IDENTIFIER)
        self._add_token(token_type)

    def _number(self):
        while self._peek().isdigit():
            self._advance()

        if self._peek() == "." and self._peek_next().isdigit():
            self._advance()  # consume the "."
            while self._peek().isdigit():
                self._advance()

        value = float(self.source[self.start:self.current])
        self._add_token(TokenType.NUMBER, value)

    def _string(self):
        while self._peek() != '"' and not self._is_at_end():
            if self._peek() == "\n":
                self.line += 1
            self._advance()

        if self._is_at_end():
            raise ScanError(self.line, "Unterminated string")

        self._advance()  # consume the closing "
        value = self.source[self.start + 1:self.current - 1]
        self._add_token(TokenType.STRING, value)

    # -- low-level character helpers --------------------------------

    def _advance(self) -> str:
        c = self.source[self.current]
        self.current += 1
        return c

    def _match(self, expected: str) -> bool:
        if self._is_at_end() or self.source[self.current] != expected:
            return False
        self.current += 1
        return True

    def _peek(self) -> str:
        if self._is_at_end():
            return "\0"
        return self.source[self.current]

    def _peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return "\0"
        return self.source[self.current + 1]

    def _is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def _add_token(self, type_: TokenType, literal=None):
        text = self.source[self.start:self.current]
        self.tokens.append(Token(type_, text, literal, self.line))