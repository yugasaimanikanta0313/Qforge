# TCS Enterprise Python Coding Standards & Testing Guidelines

## 1. Code Style and Structure
- Follow PEP 8 style guide strictly.
- Type annotations are required on all public function and method signatures.
- Maximum line length is 100 characters.
- Imports must be grouped in order: standard library, third-party libraries, local application modules.

## 2. Test Architecture (AAA Pattern)
- Every unit test must strictly follow the Arrange-Act-Assert pattern.
- Tests must be stateless and idempotent. No test should depend on execution order or shared mutable state.
- Use explicit test fixtures via `@pytest.fixture` with appropriate scoping (`function`, `session`).

```python
import pytest

def test_user_authentication_success():
    # Arrange
    credentials = {"username": "enterprise_user", "token": "valid_token"}
    auth_service = AuthService()

    # Act
    is_authenticated = auth_service.authenticate(credentials)

    # Assert
    assert is_authenticated is True, "Expected valid credentials to authenticate successfully"
```

## 3. Boundary & Edge Case Coverage
Test suites must include:
1. Standard happy path validation.
2. Null and empty input checks (`None`, `""`, `[]`, `{}`).
3. Boundary limits (minimum, maximum, overflow conditions).
4. Error handling and exception verification using `pytest.raises(ExpectedException)`.

## 4. Assertion Guidelines
- Use descriptive custom messages on all assertion statements.
- Floating-point comparisons must utilize `pytest.approx()` with defined tolerances.
- Never write bare assertions (`assert x`) without clarifying context.
