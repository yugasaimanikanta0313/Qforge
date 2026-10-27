# TCS Enterprise Test Naming Conventions

## 1. Unit Test Naming Formula
Test function names must clearly articulate three aspects:
`test_<unit_or_method>_<condition_or_input>_<expected_behavior>`

### Examples:
- `test_calculate_tax_zero_income_returns_zero`
- `test_bubble_sort_unsorted_list_returns_ascending_order`
- `test_cache_manager_evicts_oldest_key_when_capacity_reached`
- `test_order_query_excludes_cancelled_records`

## 2. Prohibited Naming Patterns
- Generic names such as `test1`, `test_main`, `test_case`, or `test_function` are strictly rejected by the validator.
- Avoid vague descriptions like `test_handles_data` or `test_works`.

## 3. Parametrized Test Naming
When using `@pytest.mark.parametrize`, specify readable custom IDs:
```python
@pytest.mark.parametrize(
    "input_val, expected",
    [(1, 2), (0, 1), (-1, 0)],
    ids=["positive_integer", "zero_boundary", "negative_integer"]
)
def test_increment_integer(input_val, expected):
    assert increment(input_val) == expected
```
