# QForge Enterprise Python Coding Standards

## Test Function Naming
- All test functions must be prefixed with `test_`
- Use descriptive names: `test_sort_empty_list`, `test_cache_eviction_on_max_size`
- Never use generic names like `test1`, `test_function`

## Test Structure (AAA Pattern)
Each test must follow Arrange → Act → Assert:
```python
def test_bubble_sort_sorted_input():
    # Arrange
    input_data = [1, 2, 3, 4, 5]
    expected = [1, 2, 3, 4, 5]
    # Act
    result = bubble_sort(input_data)
    # Assert
    assert result == expected, f"Expected {expected}, got {result}"
```

## Required Test Coverage
Every function must have tests for:
1. Happy path (valid, expected input)
2. Empty input (`[]`, `""`, `None`)
3. Single element input
4. Boundary values (min/max integers, empty strings)
5. Invalid type input where applicable

## Import Standards
- All imports at the top of the test file
- Use `import pytest` for fixtures and markers
- Use `pytest.mark.parametrize` for repetitive test cases

## Assertion Standards
- All assertions must have descriptive error messages
- Use `assert result == expected, "description"` not just `assert result == expected`
- For floating point: use `pytest.approx()` instead of direct equality

## SQL Test Standards
- SQL assertion tests must use `COUNT(*)` or `EXCEPT` comparisons
- Validate both row counts and specific column values
- Always test with NULL values in join columns
- Test edge cases: empty result sets, duplicate rows

## Documentation
- Add a single-line docstring to each test explaining what scenario it validates
- Group related tests in classes with descriptive class names
