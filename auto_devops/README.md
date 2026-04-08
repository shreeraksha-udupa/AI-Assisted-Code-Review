# Auto-DevOps: Self-Healing Code Reviewer

An enterprise-grade AI agent that automatically reviews code diffs, understands
repository-wide context via RAG, and proposes + applies fixes autonomously.

Powered by **Groq** (LLM inference) + **ChromaDB** (vector store) + **sentence-transformers** (embeddings).

## Architecture

```
GitHub Repo
    │
    ▼
[Ingestion Layer]  ←  Clone → Chunk → Embed → ChromaDB
    │
    ▼
[Trigger Layer]    ←  Diff / PR input
    │
    ▼
[Agentic Pipeline] ←  8-step orchestrator
   Step 1: Analyze diff
   Step 2: RAG retrieval from ChromaDB
   Step 3: Cross-file reasoning
   Step 4: Groq LLM review → structured JSON
   Step 5: Create Git branch
   Step 6: Apply fix
   Step 7: Run tests
   Step 8: Accept or reject fix
    │
    ▼
[Output]           ←  JSON report + explanation
```

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Get a Groq API key (free)

Sign up at https://console.groq.com — free tier gives you plenty of tokens.

```bash
cp .env.example .env
# Edit .env and paste your GROQ_API_KEY
```

### 3. Ingest a repository (first-time setup)

```bash
python main.py --repo https://github.com/pallets/flask --ingest
```

This clones the repo, chunks all source files, creates local embeddings, and stores
them in a local ChromaDB vector database. No API calls needed for this step.

### 4. Review a diff

```bash
# Use the included sample diff (SQL injection + token leak)
python main.py --diff sample.diff

# Or provide your own
python main.py --diff path/to/your/changes.diff
```

### 5. Full run (ingest + review)

```bash
python main.py --repo https://github.com/yourorg/yourrepo --ingest --diff pr_42.diff
```

## Groq Model Options

Edit `config/settings.py` to switch models:

| Model | Speed | Context | Best for |
|-------|-------|---------|----------|
| `llama-3.3-70b-versatile` | Fast | 128k | Best quality (default) |
| `llama-3.1-8b-instant` | Fastest | 128k | Quick reviews, low latency |
| `mixtral-8x7b-32768` | Fast | 32k | Good balance |

## Output

The agent produces `review_report.json` containing:

```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "decision": "fix_accepted",
  "explanation": "Fix applied to auth.py...",
  "overall_risk": "critical",
  "summary": "SQL injection vulnerability introduced in login function",
  "issues": [
    {
      "issue_type": "security",
      "severity": "critical",
      "file": "app/auth.py",
      "explanation": "String interpolation in SQL query enables injection attacks",
      "why_this_matters": "Allows attackers to bypass authentication or dump the database",
      "suggested_fix": "Use parameterized queries: db.execute(query, (username, password))"
    }
  ],
  "rag_context_used": [
    {"path": "app/db.py", "relevance": 0.91},
    {"path": "app/models.py", "relevance": 0.87}
  ],
  "fix_applied": true,
  "tests_passed": true,
  "branch_created": true
}
```

## Project Structure

```
auto_devops/
├── config/
│   └── settings.py          # Groq model, ChromaDB path, embed model
├── ingestion/
│   ├── repo_cloner.py        # Git clone + file discovery
│   ├── chunker.py            # Code-aware file chunker
│   └── embedder.py           # Embed chunks → ChromaDB (local, no API)
├── retrieval/
│   └── retriever.py          # Query ChromaDB, return top-K context
├── review/
│   ├── diff_parser.py        # Parse unified diffs
│   └── reviewer.py           # Groq LLM code reviewer
├── agent/
│   ├── orchestrator.py       # 8-step agentic loop
│   └── git_ops.py            # Branch creation, patch apply
├── tests/
│   └── test_runner.py        # Runs pytest/npm or simulates
├── output/
│   └── reporter.py           # Final JSON + explainability report
├── main.py                   # CLI entrypoint
├── sample.diff               # Demo diff with SQL injection + token leak
├── .env.example              # Copy to .env and add GROQ_API_KEY
└── requirements.txt
```

## How RAG Works Here

When a diff arrives, the system retrieves the top-5 most semantically similar
code chunks from ChromaDB using local `sentence-transformers` embeddings —
no extra API call needed. The Groq LLM then sees both the diff AND the related
files, enabling cross-file impact analysis just like a senior engineer would do.

## CLI Reference

| Flag | Default | Description |
|------|---------|-------------|
| `--repo` | `https://github.com/pallets/flask` | GitHub URL to clone and index |
| `--dest` | `./repo` | Local clone path |
| `--diff` | (sample diff) | Path to a unified .diff file |
| `--ingest` | off | Clone repo and build vector DB |
| `--report` | `./review_report.json` | Output report path |
