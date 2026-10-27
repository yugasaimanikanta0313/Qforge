"""
QForge — SQL AST Parser Service
Uses sqlglot to parse and fingerprint SQL queries.
Extracts structure for complexity scoring and FAISS similarity search.
"""
import logging
import sqlglot
from sqlglot import expressions as exp

logger = logging.getLogger(__name__)


def parse_sql(query: str) -> dict:
    """
    Parse a SQL query and return a structural fingerprint dict.
    Supports most ANSI SQL dialects via sqlglot's auto-detection.
    """
    try:
        statements = sqlglot.parse(query)
    except sqlglot.errors.SqlglotError as e:
        logger.warning(f"[AST_SQL] Parse error: {e}")
        raise

    if not statements:
        return {"code_type": "sql_empty", "error": "No parseable statements found"}

    stmt = statements[0]  # Analyze the first statement

    tables = []
    joins = []
    subqueries = 0
    aggregations = []
    where_clauses = 0

    for node in stmt.walk():
        if isinstance(node, exp.Table) and node.name:
            tables.append(node.name)
        elif isinstance(node, exp.Join):
            join_type = node.args.get("kind", "INNER")
            joins.append(str(join_type))
        elif isinstance(node, exp.Subquery):
            subqueries += 1
        elif isinstance(node, exp.Anonymous | exp.Count | exp.Sum | exp.Avg | exp.Max | exp.Min):
            aggregations.append(type(node).__name__.upper())
        elif isinstance(node, exp.Where):
            where_clauses += 1

    # Determine query type
    if isinstance(stmt, exp.Select):
        query_type = "SELECT"
    elif isinstance(stmt, exp.Insert):
        query_type = "INSERT"
    elif isinstance(stmt, exp.Update):
        query_type = "UPDATE"
    elif isinstance(stmt, exp.Delete):
        query_type = "DELETE"
    elif isinstance(stmt, exp.Create):
        query_type = "CREATE"
    else:
        query_type = type(stmt).__name__.upper()

    fingerprint = {
        "code_type": f"sql_{query_type.lower()}",
        "query_type": query_type,
        "table_count": len(set(tables)),
        "tables": list(set(tables)),
        "join_count": len(joins),
        "join_types": joins,
        "subquery_count": subqueries,
        "aggregation_count": len(aggregations),
        "aggregations": list(set(aggregations)),
        "where_clause_count": where_clauses,
        "total_lines": query.count("\n") + 1,
    }

    logger.info(
        f"[AST_SQL] Parsed {query_type}: tables={len(set(tables))}, "
        f"joins={len(joins)}, subqueries={subqueries}"
    )
    return fingerprint
