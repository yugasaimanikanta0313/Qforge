"""
Unit tests for GitHub Client & Nested File Tree Builder.
"""
from backend.services.github.client import build_nested_file_tree
from backend.api.v1.endpoints.github import _parse_repo_string

def test_parse_repo_string():
    owner, repo = _parse_repo_string("pallets/flask")
    assert owner == "pallets"
    assert repo == "flask"

    owner2, repo2 = _parse_repo_string("https://github.com/facebook/react.git")
    assert owner2 == "facebook"
    assert repo2 == "react"

def test_build_nested_file_tree():
    sample_files = [
        {"path": "src/index.ts", "filename": "index.ts", "language": "typescript"},
        {"path": "src/utils/math.ts", "filename": "math.ts", "language": "typescript"},
        {"path": "package.json", "filename": "package.json", "language": "json"},
    ]
    tree = build_nested_file_tree(sample_files)
    assert len(tree) == 2  # 'package.json' and 'src' folder

    # Find 'src' folder
    src_dir = next(n for n in tree if n["name"] == "src")
    assert src_dir["type"] == "directory"
    assert len(src_dir["children"]) == 2  # 'index.ts' and 'utils' folder
