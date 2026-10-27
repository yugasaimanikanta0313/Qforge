"""
QForge — Python AST Parser Service
Uses Python's built-in `ast` stdlib module to extract structural
metadata from submitted Python code. Zero external dependencies.
Output feeds into the complexity classifier and FAISS query vector.
"""
import ast
import logging

logger = logging.getLogger(__name__)


def parse_python(code: str) -> dict:
    """
    Parse Python source code and return a structural fingerprint dict.
    Raises SyntaxError if code is syntactically invalid.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        logger.warning(f"[AST_PYTHON] SyntaxError during parse: {e}")
        raise

    functions = []
    classes = []
    imports = []
    loops = 0
    nested_depth = 0

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            args = [a.arg for a in node.args.args]
            functions.append({
                "name": node.name,
                "args": args,
                "line": node.lineno,
                "is_async": isinstance(node, ast.AsyncFunctionDef),
            })
        elif isinstance(node, ast.ClassDef):
            classes.append({"name": node.name, "line": node.lineno})
        elif isinstance(node, ast.Import | ast.ImportFrom):
            if isinstance(node, ast.ImportFrom):
                imports.append(f"from {node.module} import ...")
            else:
                for alias in node.names:
                    imports.append(f"import {alias.name}")
        elif isinstance(node, ast.For | ast.While):
            loops += 1

    # Rough nesting depth heuristic
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            for child in ast.walk(node):
                if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef) and child is not node:
                    nested_depth = max(nested_depth, 2)

    fingerprint = {
        "code_type": "python_module",
        "function_count": len(functions),
        "class_count": len(classes),
        "import_count": len(imports),
        "loop_count": loops,
        "nested_depth": nested_depth,
        "functions": functions,
        "classes": classes,
        "imports": imports,
        "total_lines": code.count("\n") + 1,
    }

    logger.info(
        f"[AST_PYTHON] Parsed: {len(functions)} functions, {len(classes)} classes, "
        f"{loops} loops, {nested_depth} nesting depth"
    )
    return fingerprint
