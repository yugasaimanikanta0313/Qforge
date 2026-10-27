"""
QForge Unit Tests — AST Parser Service
Validates AST syntax analysis and fingerprint extraction for Python and SQL.
"""
import pytest
from backend.services.ast_parser.python_parser import parse_python
from backend.services.ast_parser.sql_parser import parse_sql


def test_python_parser_basic_function():
    code = """
def multiply(x, y):
    return x * y
"""
    res = parse_python(code)
    assert res["function_count"] == 1
    assert res["functions"][0]["name"] == "multiply"
    assert res["class_count"] == 0
    assert res["code_type"] == "python_module"


def test_python_parser_class_and_decorators():
    code = """
class DataService:
    @property
    def name(self):
        return "data"

    async def fetch(self):
        return []
"""
    res = parse_python(code)
    assert res["class_count"] == 1
    assert res["classes"][0]["name"] == "DataService"
    assert any(f["is_async"] for f in res["functions"])


def test_sql_parser_select_query():
    query = """
SELECT u.id, u.username, o.total 
FROM users u 
INNER JOIN orders o ON u.id = o.user_id 
WHERE u.active = 1
"""
    res = parse_sql(query)
    assert res["query_type"] == "SELECT"
    assert res["table_count"] == 2
    assert "users" in res["tables"]
    assert "orders" in res["tables"]
    assert res["join_count"] == 1
    assert res["where_clause_count"] == 1


def test_sql_parser_aggregations():
    query = "SELECT COUNT(id), AVG(salary), MAX(bonus) FROM employees GROUP BY department"
    res = parse_sql(query)
    assert res["aggregation_count"] >= 3
    assert "COUNT" in res["aggregations"]
    assert "AVG" in res["aggregations"]
    assert "MAX" in res["aggregations"]
