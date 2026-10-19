# TechNova AI

A company knowledge assistant with a FastAPI API and a responsive browser frontend. Ask questions, inspect source documents, search the knowledge library, and revisit or export conversations.

## Run locally

Requires Python 3.12 (recommended; core application also supports 3.11+).

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000**. FastAPI serves the frontend and API together; no Node build or CORS configuration is needed. API documentation is at `/docs`; readiness is at `/health`. Launch from the repository root. Use a single worker for AI mode, which holds a local vector index and graph in memory.

### Answer modes

- **Local (default):** BM25 search → access filtering → parent expansion → deduplicated exact passages and sources. No credentials, model downloads, or external services. The interface identifies this as “Local search.” A citation confirms the passage's origin; it does not claim AI verification. Unmatched questions return an explicit no-results answer.
- **Groq:** your existing LangGraph pipeline routes/rewrites queries, retrieves dense + BM25 results, fuses results, reranks, expands parents, generates with Groq, verifies grounding, and retries once if necessary. Provider failures return a retryable API error and never silently switch to local mode.

To enable the full AI pipeline:

```bash
pip install -r requirements-ai.txt
```

Set `RAG_MODE=groq` and `GROQ_API_KEY` in `.env`, then restart. The first startup downloads `all-MiniLM-L6-v2` and `cross-encoder/ms-marco-MiniLM-L-6-v2` from Hugging Face, builds a Chroma index, and requires internet access and disk space. Groq uses `openai/gpt-oss-120b` for routing, rewriting, and generation, and `openai/gpt-oss-20b` for verification. `GROQ_BASE_URL` can point to a compatible proxy. AI mode fails startup if its key, dependencies, models, or documents are missing.

## Knowledge and access

Knowledge documents live in `data/raw/`. Add UTF-8 Markdown with the same front matter as the existing documents, then restart to reindex. Malformed or duplicate document IDs fail startup rather than silently skipping content. Empty libraries are supported in local mode. A changed corpus gets a separate Chroma collection so removed documents cannot remain searchable.

`ACCESS_LEVEL` is set **on the server**, never accepted from API callers. `EMPLOYEE` is the default. Managers also see manager documents. `AI_ENGINEER`, `DEVOPS`, and `SECURITY` see employee/manager documents plus their own specialty; `ADMIN` sees all documents. Listing, search, document details, local retrieval, hybrid retrieval, and parent expansion enforce these permissions. Unavailable document IDs return 404.

This is a **single workspace application**. With no `TECHNOVA_API_KEY`, anyone who can reach the server can use its configured workspace role. Set a strong shared `TECHNOVA_API_KEY` before exposing the service, use HTTPS, and enter the key through Workspace settings in the browser. Protected API calls use `X-API-Key`; the key stays in tab-scoped session storage. For multiple users or workspaces, put the application behind identity-aware authentication and bind roles per authenticated user before deployment. `/health`, static assets, and API schema documentation are public.

Conversations are saved in browser local storage (the latest 30). They are not synced between browsers. Each question is independent; the UI conversation log is not sent to the model. Delete history from the sidebar or export it as Markdown. Avoid using a shared browser for sensitive questions. Full AI traces are written to `logs/rag_traces.jsonl`; apply your deployment's log retention and access policy.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Readiness after successful knowledge initialization |
| GET | `/api/status` | Mode, server role, available document and department counts |
| POST | `/api/query` | `{ "query": "How many annual leave days do employees get?" }` |
| GET | `/api/documents?search=leave&department=HR` | Search accessible documents |
| GET | `/api/documents/{document_id}` | Read an accessible source |

Queries must contain 1–2,000 characters (whitespace-only input is rejected). Request bodies cannot supply an access role. The API limits simultaneous expensive queries (`QUERY_LIMIT`, default 2), returning 429 while busy. Graph invocations are serialized to keep trace state isolated.

## Validate

```bash
pip install -r requirements-dev.txt
pytest -q
node --check frontend/app.js
node --check frontend/api.js
```

Tests exercise the real corpus and API, access filtering, authentication, empty data, validation, source links, provider errors, and concurrency backpressure. Legacy `app/scripts/` files are development experiments and are not the automated test suite. Run `RUN_AI_INTEGRATION=1 pytest -q` after installing AI dependencies to exercise the real models and LangGraph with synthetic Groq SDK responses (the default suite skips this test). Live Groq generation requires a working provider key.

## Structure

- `app/main.py`: FastAPI application factory and typed API contracts.
- `app/services/knowledge.py`: corpus initialization and adapters to the existing retrieval and graph code.
- `app/core/`: environment configuration and optional workspace authentication.
- `app/ingestion`, `app/retrieval`, `app/query`, `app/generation`, `app/graph`, `app/evaluation`: original RAG components.
- `frontend/`: browser application; centralized API calls, accessible dialogs, responsive layout, and safe text rendering.
- `tests/`: deterministic API and access tests; no provider key required.
