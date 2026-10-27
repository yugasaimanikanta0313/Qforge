"""
QForge — Repair Prompts
Repair-loop prompt templates: error trace injection, constraint reinforcement, and syntax self-healing.
"""

REPAIR_PROMPT = """You are an expert QA engineer performing code repair. A previous test suite was REJECTED by the validator.

ORIGINAL CODE BEING TESTED:
```{language}
{raw_input}
```

REJECTED TEST SUITE (contains errors):
```{language}
{generated_test_suite}
```

VALIDATION ERRORS FOUND:
{validation_errors}

ENTERPRISE GUIDELINES:
{context_chunks}

TASK: Fix ALL the errors listed above and return a corrected, complete, runnable test suite.
- Fix every error explicitly listed
- Keep all valid tests that already pass
- Ensure all imports are correct
- Ensure syntax is valid {language}

OUTPUT FORMAT: Raw corrected code only. No markdown fences. No explanation.
"""

VALIDATOR_PROMPT = """You are a strict code quality auditor. Analyze the following test suite for errors.

LANGUAGE: {language}
TEST SUITE TO VALIDATE:
```{language}
{generated_test_suite}
```

Check for:
1. Syntax errors (invalid {language} syntax)
2. Missing imports
3. Undefined variables or functions referenced
4. Test functions that would immediately fail due to structural issues
5. SQL assertions that are logically broken

Respond ONLY with valid JSON:
{{
  "status": "PASS" or "FAIL",
  "errors": ["<error description 1>", "<error description 2>"],
  "summary": "<one sentence assessment>"
}}

If no errors found, return: {{"status": "PASS", "errors": [], "summary": "Test suite is valid and ready for execution."}}
Respond ONLY with the JSON object. No markdown.
"""
