# LangGraph + LangChain — laboratório e projeto real, 100% local

Três projetos Python (uv), sem nuvem: o LLM é o Gemma local via `llama-server`
(`http://127.0.0.1:8080/v1`) e o banco é Postgres em Docker.

| Projeto | O que é | Como rodar |
|---|---|---|
| `lab-graph/` | 28 exercícios LangGraph (P00–P27): grafos, RAG, HITL, API, segurança, evals | `cd lab-graph && uv sync && uv run pytest -q` |
| `langchain-lab/` | Bateria de módulos `langchain-core` + `langchain-openai` (prompts, parsers, LCEL, tools, chat, history, callbacks) | `cd langchain-lab && uv sync && uv run pytest -q` |
| `balcao-local/` | App real: concierge de suporte com triagem, RAG com citação, aprovação humana, Postgres e API com SSE | `cd balcao-local && uv sync && uv run pytest -q` |

## Subindo o Balcão (Docker, no host)

```bash
cd balcao-local
distrobox-host-exec docker compose up -d --build   # api :8091 + db :5433
BALCAO_E2E=1 uv run pytest -q tests/test_e2e_compose.py
```

Fluxo: `POST /run` → `awaiting_approval` + plano → `POST /resume`
`{"approved": true}` → efeito gravado uma vez no `ledger` do Postgres.

## Notas

- `balcao-local/kb/*.md` são dados do app (corpus de runbooks lido em
  runtime), não documentação.
- `lab-graph/reports/P*/output.json` são evidências das execuções.
- Portas: llama-server do host na 8080, API do Balcão na 8091.
# estudo_langchain_langgraph
