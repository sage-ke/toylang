"""
Token type definitions.

A Token is a single meaningful chunk of source code, e.g. the text
"123" becomes a Token(NUMBER, "123", 123).
"""

from enum import Enum, auto


class TokenType(Enum):
    # Single-character tokens
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    COMMA = auto()
    SEMICOLON = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()

    # One or two character tokens
    EQUAL = auto()
    EQUAL_EQUAL = auto()
    BANG = auto()
    BANG_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()

    # Literals
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()

    # Keywords
    AND = auto()
    OR = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    TRUE = auto()
    FALSE = auto()
    NIL = auto()
    PRINT = auto()
    VAR = auto()
    FUN = auto()
    RETURN = auto()

    EOF = auto()


KEYWORDS = {
    "and": TokenType.AND,
    "or": TokenType.OR,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "nil": TokenType.NIL,
    "print": TokenType.PRINT,
    "var": TokenType.VAR,
    "fun": TokenType.FUN,
    "return": TokenType.RETURN,
}


class Token:
    def __init__(self, type_: TokenType, lexeme: str, literal, line: int):
        self.type = type_
        self.lexeme = lexeme
        self.literal = literal
        self.line = line

    def __repr__(self):
        return f"Token({self.type.name}, {self.lexeme!r}, {self.literal!r})"