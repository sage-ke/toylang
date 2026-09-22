"""
Entry point.

Usage:
    python main.py               -> starts an interactive REPL
    python main.py examples/hello.toy   -> runs a script file
"""

import sys
from scanner import Scanner
from parser import Parser
from interpreter import Interpreter
from errors import ToyLangError

interpreter = Interpreter()


def run(source: str):
    try:
        tokens = Scanner(source).scan_tokens()
        statements = Parser(tokens).parse()
        interpreter.interpret(statements)
    except ToyLangError as e:
        print(e)


def run_file(path: str):
    with open(path, "r") as f:
        source = f.read()
    run(source)


def run_repl():
    print("toylang REPL — type 'exit' to quit")
    while True:
        try:
            line = input("> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if line.strip() in ("exit", "quit"):
            break
        if not line.strip():
            continue
        run(line)


if __name__ == "__main__":
    if len(sys.argv) > 2:
        print("Usage: python main.py [script.toy]")
        sys.exit(1)
    elif len(sys.argv) == 2:
        run_file(sys.argv[1])
    else:
        run_repl()