# QForge Framework — Enterprise Software Validation Platform

> **Classification:** Technical Design Document v1.0  
> **Prepared by:** Principal Enterprise Software Architect, Tata Consultancy Services  
> **Domain:** Agentic Workflows · Scalable Cloud Topologies · AI-Augmented Testing  

---

## Executive Summary
**QForge** is a **Hybrid Multi-Model, Local-First Multi-Agent RAG Platform** engineered to automate enterprise software validation pipelines without compromising data sovereignty. The system ingests raw source code and database queries, routes them through a deterministic **LangGraph** agent orchestration loop, and delivers compilation-verified test suites and real-time streaming telemetry — all while selectively partitioning sensitive compute to an on-premises edge tier and complex reasoning to a governed cloud tier.

---

## Architecture Flow

```
                      ┌──────────────────────┐
                      │   Client / IDE / UI  │
                      └──────────┬───────────┘
                                 │ WebSocket
                                 ▼
                      ┌──────────────────────┐
                      │     ROUTER NODE      │
                      │  - AST Fingerprint   │
                      │  - FAISS Guidelines  │
                      │  - Complexity Score  │
                      └──────────┬───────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 │                               │
                 ▼ [Score < 7]                   ▼ [Score >= 7 + Egress Policy]
       ┌───────────────────┐           ┌───────────────────┐
       │   Local Ollama    │           │ Cloud Gemini API  │
       │  (Qwen2.5-Coder)  │           │ (Gemini 2.5 Flash)│
       └─────────┬─────────┘           └─────────┬─────────┘
                 │                               │
                 └───────────────┬───────────────┘
                                 ▼
                      ┌──────────────────────┐
                      │    GENERATOR NODE    │
                      │  Synthesize Tests    │
                      └──────────┬───────────┘
                                 │
                                 ▼
                      ┌──────────────────────┐
                      │    VALIDATOR NODE    │◄──────┐
                      │  - AST Syntax Check  │       │
                      │  - Semantic Audit    │       │ Self-Heal Loop
                      └──────────┬───────────┘       │ (Max 3 cycles)
                                 │                   │
                     ┌───────────┴───────────┐       │
                     ▼                       ▼       │
               [Checks PASS]           [Checks FAIL] ─┘
                     │
                     ▼
             Verified Artifact
             + MongoDB Audit Log
```

---

## Key Capabilities

1. **Local-First Privacy Firewall**:
   - Embeddings are generated entirely on-premises using **BAAI/bge-small-en-v1.5** via `sentence-transformers`. Raw code never leaves local memory for embeddings.
   - Guideline matching runs locally against an in-memory **FAISS** index.
   - PII and proprietary literals are stripped and anonymized by the **Egress Guard** prior to any cloud transmission.

2. **Self-Healing Agentic Loop**:
   - The cyclic edge between the `Validator Node` and `Generator Node` is guarded by a configurable `MAX_REPAIR_CYCLES` threshold (default: 3).
   - If syntax or logical issues arise, the validator injects the explicit error trace back into the generator for immediate repair.

3. **Full-Duplex Telemetry**:
   - WebSocket streaming (`/ws/qforge/{session_id}`) delivers real-time node transitions, token deltas, and lifecycle updates directly to the frontend dashboard.

---

## Project Structure

```
qforge/
├── README.md
├── pyproject.toml
├── .env.example
├── docker-compose.yml
├── Makefile
├── run.py
├── demo_run.py
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── api/v1/
│   │   ├── router.py
│   │   ├── endpoints/ (sessions.py, audit.py, health.py, websocket.py)
│   │   └── schemas/ (session.py, audit.py, stream.py)
│   ├── core/ (lifespan.py, dependencies.py, session_manager.py, exceptions.py, logging.py)
│   ├── agents/ (graph.py, state.py, nodes/, prompts/, tools/)
│   ├── services/ (ast_parser/, llm/, vector_store/, egress_guard/, db/)
├── data/
│   ├── guidelines/ (tcs_python_coding_standards.md, tcs_sql_best_practices.md, ...)
│   └── faiss_index/ (guidelines.index, chunk_metadata.json)
├── tests/
│   ├── conftest.py
│   ├── unit/ (test_router_node.py, test_validator_node.py, test_ast_parser.py, test_egress_policy.py)
│   ├── integration/ (test_websocket_stream.py, test_agent_graph.py)
│   └── e2e/ (test_full_pipeline.py)
└── frontend/
    ├── package.json
    ├── vite.config.ts
    └── src/ (components/, hooks/, store/, pages/, api/, types/)
```

---

## Quickstart

### 1. Environment Setup
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Build Offline Vector Store
```bash
python -m backend.services.vector_store.index_builder
```

### 3. Run Test Suite
```bash
pytest tests/unit tests/integration -v
```

### 4. Run Server
```bash
python run.py
```
FastAPI documentation available at `http://localhost:8000/docs`.
WebSocket streaming available at `ws://localhost:8000/ws/qforge/{session_id}`.
