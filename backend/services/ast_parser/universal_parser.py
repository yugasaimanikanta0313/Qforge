"""
QForge — Universal Tree-Sitter AST Parser
Provides AST parsing, complexity scoring, and syntax checking across all major languages:
  - TypeScript & JavaScript
  - Java
  - Go
  - Rust
  - C# (.NET)
  - Generic / Heuristic Fallback
"""
import logging
from typing import Dict, Any, List
from tree_sitter import Language, Parser

logger = logging.getLogger(__name__)

# Initialize language parsers lazily
_PARSERS: Dict[str, Parser] = {}


def _get_parser(language: str) -> Parser:
    lang = language.lower()
    if lang in _PARSERS:
        return _PARSERS[lang]

    parser = None
    try:
        if lang in ("typescript", "ts", "tsx"):
            import tree_sitter_typescript as ts_ts
            parser = Parser(Language(ts_ts.language_typescript()))
        elif lang in ("javascript", "js", "jsx"):
            import tree_sitter_javascript as ts_js
            parser = Parser(Language(ts_js.language()))
        elif lang == "java":
            import tree_sitter_java as ts_java
            parser = Parser(Language(ts_java.language()))
        elif lang == "go":
            import tree_sitter_go as ts_go
            parser = Parser(Language(ts_go.language()))
        elif lang == "rust":
            import tree_sitter_rust as ts_rust
            parser = Parser(Language(ts_rust.language()))
        elif lang in ("csharp", "c#", "cs"):
            import tree_sitter_c_sharp as ts_cs
            parser = Parser(Language(ts_cs.language()))
    except Exception as e:
        logger.warning(f"[AST] Failed to initialize tree-sitter parser for {language}: {e}")

    if parser:
        _PARSERS[lang] = parser
        return parser
    return None


def parse_universal(code: str, language: str) -> Dict[str, Any]:
    """
    Parses source code in any supported language and computes AST metrics & complexity.
    """
    lang = language.lower()
    parser = _get_parser(lang)

    if not parser:
        return _heuristic_analysis(code, lang)

    try:
        encoded = code.encode("utf-8")
        tree = parser.parse(encoded)
        root = tree.root_node

        has_error = root.has_error

        # Traverse AST and gather metrics
        functions = 0
        classes = 0
        branches = 0
        loops = 0

        # Node type matchers by language
        func_types = {
            "function_declaration", "method_declaration", "arrow_function",
            "function_item", "method_definition", "function_expression"
        }
        class_types = {
            "class_declaration", "interface_declaration", "struct_item",
            "record_declaration", "enum_declaration", "trait_item"
        }
        branch_types = {
            "if_statement", "switch_statement", "match_expression",
            "ternary_expression", "conditional_expression", "catch_clause"
        }
        loop_types = {
            "for_statement", "while_statement", "do_statement", "for_in_statement"
        }

        def traverse(node):
            nonlocal functions, classes, branches, loops
            ntype = node.type
            if ntype in func_types:
                functions += 1
            elif ntype in class_types:
                classes += 1
            elif ntype in branch_types:
                branches += 1
            elif ntype in loop_types:
                loops += 1

            for child in node.children:
                traverse(child)

        traverse(root)

        # Compute normalized complexity score (0-10)
        raw_score = 1 + (functions * 1.5) + (classes * 2) + (branches * 1.5) + (loops * 1.5)
        complexity_score = min(10, max(1, int(round(raw_score))))

        return {
            "code_type": f"{lang}_source",
            "language": lang,
            "complexity_score": complexity_score,
            "has_syntax_errors": has_error,
            "metrics": {
                "functions": functions,
                "classes": classes,
                "branches": branches,
                "loops": loops,
                "lines_of_code": len(code.strip().splitlines()),
            },
            "root_type": root.type,
        }
    except Exception as e:
        logger.error(f"[AST] Universal parser failed for {language}: {e}")
        return _heuristic_analysis(code, lang)


def _heuristic_analysis(code: str, language: str) -> Dict[str, Any]:
    """Lightweight fallback analysis for unsupported languages or parse errors."""
    lines = code.strip().splitlines()
    loc = len(lines)
    branches = code.count("if ") + code.count("else") + code.count("switch") + code.count("case")
    loops = code.count("for ") + code.count("while ")
    classes = code.count("class ") + code.count("struct ") + code.count("interface ")
    functions = code.count("def ") + code.count("func ") + code.count("fn ") + code.count("function ")

    score = 1 + int(loc / 25) + (branches * 1) + (classes * 2)
    complexity_score = min(10, max(1, score))

    return {
        "code_type": f"{language}_source",
        "language": language,
        "complexity_score": complexity_score,
        "has_syntax_errors": False,
        "metrics": {
            "functions": max(1, functions),
            "classes": classes,
            "branches": branches,
            "loops": loops,
            "lines_of_code": loc,
        },
        "heuristic": True,
    }


def check_universal_syntax(code: str, language: str) -> List[str]:
    """Checks for syntax errors using tree-sitter root_node.has_error or bracket balancing."""
    lang = language.lower()
    parser = _get_parser(lang)

    if not code or not code.strip():
        return ["Source code is empty"]

    if parser:
        try:
            tree = parser.parse(code.encode("utf-8"))
            if tree.root_node.has_error:
                # Find error node location
                def find_error(node):
                    if node.type == "ERROR" or node.is_missing:
                        return f"SyntaxError at line {node.start_point.row + 1}, column {node.start_point.column + 1} (near '{code[node.start_byte:node.end_byte][:30]}')"
                    for child in node.children:
                        err = find_error(child)
                        if err:
                            return err
                    return "SyntaxError in code structure"

                err_desc = find_error(tree.root_node)
                return [f"{language.capitalize()} {err_desc}"]
            return []
        except Exception as e:
            return [f"{language.capitalize()} parse error: {e}"]

    # Heuristic bracket check
    stack = []
    pairs = {')': '(', '}': '{', ']': '['}
    for i, ch in enumerate(code):
        if ch in "({[":
            stack.append(ch)
        elif ch in ")}]":
            if not stack or stack[-1] != pairs[ch]:
                return [f"Unbalanced bracket '{ch}' at position {i}"]
            stack.pop()

    if stack:
        return [f"Unclosed open bracket '{stack[-1]}' in source"]

    return []
