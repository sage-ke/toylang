# toylang

A tree-walking interpreter for a small toy language, written in Python.
Built as a learning project following the structure of *Crafting
Interpreters* by Robert Nystrom (free at craftinginterpreters.com).

## What it can do right now

- Numbers, strings, booleans, `nil`
- Arithmetic: `+ - * /`, comparisons: `< <= > >= == !=`
- Variables: `var x = 5;`
- Blocks and scope: `{ ... }`
- Control flow: `if / else`, `while`, `for`
- Functions: `fun name(a, b) { return a + b; }`, including recursion
- A built-in `clock()` function
- Comments: `// like this`
- Both a REPL (`python main.py`) and running a script file

## Running it

```bash
# Interactive REPL
python main.py

# Run a script
python main.py examples/hello.toy
```

## How the pieces fit together

```
source text
    │
    ▼
scanner.py     -- breaks text into Tokens (lexing)
    │
    ▼
parser.py      -- builds an AST (ast_nodes.py) from the tokens
    │
    ▼
interpreter.py -- walks the AST and executes it, using
                  environment.py to store variables
```

Build/read order if you want to understand the code:
`tokens.py` -> `scanner.py` -> `ast_nodes.py` -> `parser.py` ->
`environment.py` -> `interpreter.py` -> `main.py`

## Where to go next

Roughly in order of difficulty:

1. **Add more operators**: modulo (`%`), logical negation edge cases,
   string comparison.
2. ~~Add `for` loops~~ — done. See `_for_statement()` in `parser.py`:
   it's implemented purely by desugaring into a `while` loop, no
   interpreter changes needed.
3. **Add lists/arrays** — a new literal syntax `[1, 2, 3]`, a new AST
   node, and indexing (`list[0]`).
4. **Add closures properly** — functions already capture their
   defining environment (`self.closure` in `ToyFunction`), so try
   writing a function that returns another function and see it work.
5. **Add classes** — the biggest jump. Crafting Interpreters covers
   this in detail (chapters on classes and inheritance).
6. **Move to a bytecode VM** — once the tree-walker feels comfortable,
   the second half of Crafting Interpreters rewrites the same
   language as a bytecode compiler + virtual machine (in C — you could
   port the ideas to Rust for extra challenge). This is where you
   learn how real language runtimes get fast.

## A note on error handling

Errors are raised as custom exceptions (`errors.py`) and caught in
`main.py`, so a bad program prints something like:

```
[line 3] Runtime error: Undefined variable 'foo'.
```

instead of a raw Python traceback — this mirrors how real compilers
report errors with line numbers.
