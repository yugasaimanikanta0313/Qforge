# TCS Enterprise SQL Best Practices & Query Validation Standards

## 1. SQL Query Formatting & Style
- Standard ANSI SQL reserved keywords must be UPPERCASE (`SELECT`, `FROM`, `WHERE`, `JOIN`, `GROUP BY`, `ORDER BY`).
- Table and column identifiers must be snake_case.
- Every join must explicitly declare join criteria (`ON a.id = b.a_id`). Avoid implicit Cartesian products (`FROM table_a, table_b`).
- Explicit column selection is mandatory in production queries; `SELECT *` is prohibited in enterprise pipelines.

## 2. Test Verification & Assertion Strategies
- Test assertion queries must validate expected row cardinalities using `SELECT COUNT(*)`.
- Data transformation accuracy must be verified using `EXCEPT` or `MINUS` set operations between actual and expected datasets.
- Queries performing aggregations (`SUM`, `AVG`, `COUNT`, `MAX`) must include checks for empty datasets and NULL inputs.

```sql
-- Verification Query: Validate active customer counts match expectation
SELECT 
    COUNT(*) AS total_rows,
    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active_rows
FROM customers
HAVING COUNT(*) > 0;
```

## 3. Join & Null Handling Verification
- Always test join conditions against tables containing `NULL` keys to ensure expected outer-join semantics.
- Use `COALESCE` or `IFNULL` to prevent unexpected null propagation in mathematical computations.
- Check filter predicates for edge boundaries (e.g. `BETWEEN date_start AND date_end`).
