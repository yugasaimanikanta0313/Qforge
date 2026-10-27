"""
QForge — AST Parser Tool
Wraps AST parsing services as a callable agent tool.
"""
from typing import Dict, Any
from backend.services.ast_parser.python_parser import parse_python
from backend.services.ast_parser.sql_parser import parse_sql
from backend.services.ast_parser.universal_parser import parse_universal


def run_ast_analysis(code: str, language: str = "python") -> Dict[str, Any]:
    """
    Invokable tool for AST structure analysis across all languages.
    Extracts syntax tree metrics, complexity indicators, and token fingerprints.
    """
    lang = language.lower()
    if lang == "python":
        return parse_python(code)
    elif lang == "sql":
        return parse_sql(code)
    else:
        return parse_universal(code, lang)
