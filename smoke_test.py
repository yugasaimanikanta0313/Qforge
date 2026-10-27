import sys
sys.path.insert(0, r'D:\QForge')

from backend.config import settings
print("Config loaded OK")
print(f"  ollama_router_model    = {settings.ollama_router_model}")
print(f"  ollama_generator_model = {settings.ollama_generator_model}")
print(f"  gemini_model           = {settings.gemini_model}")
print(f"  max_repair_cycles      = {settings.max_repair_cycles}")
print(f"  complexity_threshold   = {settings.complexity_threshold}")
print(f"  mongodb_db_name        = {settings.mongodb_db_name}")

from backend.services.ast_parser.python_parser import parse_python
result = parse_python("def hello(x): return x + 1")
print(f"AST Python parser OK -- {result['function_count']} function(s) detected")

from backend.services.ast_parser.sql_parser import parse_sql
sql_result = parse_sql("SELECT id, name FROM users WHERE active = 1")
print(f"AST SQL parser OK -- query_type={sql_result['query_type']}, tables={sql_result['tables']}")

from backend.services.vector_store.faiss_store import FaissVectorStore
vs = FaissVectorStore()
vs.build_from_directory("data/guidelines")
results = vs.search("test function naming conventions", top_k=3)
print(f"FAISS store OK -- {len(results)} chunks retrieved")
print(f"  Top chunk preview: {results[0][:80]}..." if results else "  No chunks (check guidelines dir)")

print()
print("ALL MODULE CHECKS PASSED")
