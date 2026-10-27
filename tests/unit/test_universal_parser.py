"""
Unit tests for universal multi-language AST parser & syntax validator.
Covers: TypeScript, JavaScript, Java, Go, Rust, C#.
"""
import pytest
from backend.services.ast_parser.universal_parser import parse_universal, check_universal_syntax
from backend.agents.tools.ast_tool import run_ast_analysis

def test_parse_typescript():
    ts_code = """
    interface User {
        id: number;
        name: string;
    }

    function getUser(id: number): User | null {
        if (id <= 0) {
            return null;
        }
        return { id, name: "Alice" };
    }
    """
    res = parse_universal(ts_code, "typescript")
    assert res["language"] == "typescript"
    assert res["has_syntax_errors"] is False
    assert res["metrics"]["functions"] >= 1
    assert res["metrics"]["classes"] >= 1  # interface counts as class type
    assert res["complexity_score"] >= 2

def test_parse_javascript():
    js_code = """
    const calculateSum = (items) => {
        let total = 0;
        for (const item of items) {
            if (item.active) {
                total += item.price;
            }
        }
        return total;
    };
    """
    res = parse_universal(js_code, "javascript")
    assert res["language"] == "javascript"
    assert res["has_syntax_errors"] is False
    assert res["metrics"]["functions"] >= 1
    assert res["metrics"]["loops"] >= 1

def test_parse_java():
    java_code = """
    public class Calculator {
        public int add(int a, int b) {
            if (a < 0) {
                throw new IllegalArgumentException("Negative input");
            }
            return a + b;
        }
    }
    """
    res = parse_universal(java_code, "java")
    assert res["language"] == "java"
    assert res["has_syntax_errors"] is False
    assert res["metrics"]["classes"] >= 1
    assert res["metrics"]["functions"] >= 1

def test_parse_go():
    go_code = """
    package main

    func Divide(a, b float64) (float64, error) {
        if b == 0 {
            return 0, nil
        }
        return a / b, nil
    }
    """
    res = parse_universal(go_code, "go")
    assert res["language"] == "go"
    assert res["has_syntax_errors"] is False
    assert res["metrics"]["functions"] >= 1

def test_check_syntax_valid_and_invalid_js():
    valid_js = "function hello() { return 'world'; }"
    invalid_js = "function hello() { return 'world';"  # missing closing brace

    assert check_universal_syntax(valid_js, "javascript") == []
    errs = check_universal_syntax(invalid_js, "javascript")
    assert len(errs) > 0

def test_ast_tool_universal_dispatch():
    ts_code = "const greet = (name: string): string => `Hello ${name}`;"
    analysis = run_ast_analysis(ts_code, language="typescript")
    assert analysis["language"] == "typescript"
    assert "complexity_score" in analysis
