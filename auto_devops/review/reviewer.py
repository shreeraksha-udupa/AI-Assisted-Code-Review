import json
import re
from groq import Groq
from retrieval.retriever import retrieve_context
from config.settings import GROQ_API_KEY, MODEL

client = Groq(api_key=GROQ_API_KEY)

REVIEW_SYSTEM_PROMPT = """
You are an expert code reviewer and security engineer.
You will be given:
1. A code diff (the changes being reviewed)
2. Related code from the same repository (retrieved via RAG for cross-file context)

Your job is to identify REAL issues and propose fixes. You MUST respond with valid JSON only.
No markdown fences. No explanation outside the JSON. Start your response with { and end with }.

IMPORTANT RULES:
- Only report genuine, concrete issues. Do NOT invent or hallucinate problems.
- If the code diff looks clean, safe, and correct, return an EMPTY issues array and set overall_risk to "safe".
- Do not flag style preferences, minor naming choices, or hypothetical future risks as issues.
- A diff that adds docstrings, refactors formatting, or improves readability is SAFE unless logic is broken.

JSON schema:
{
  "issues": [
    {
      "issue_type": "bug | security | performance | style",
      "severity": "critical | high | medium | low",
      "file": "path/to/file.py",
      "line_hint": "approximate line or range",
      "explanation": "Clear explanation of the problem",
      "why_this_matters": "Impact if not fixed (e.g., SQL injection allows attackers to...)",
      "suggested_fix": "The corrected code snippet"
    }
  ],
  "overall_risk": "critical | high | medium | low | safe",
  "summary": "One-sentence summary of the review"
}

If no issues are found, return exactly:
{"issues": [], "overall_risk": "safe", "summary": "No issues found. The code changes look correct and safe."}
"""


def review_diff(diff_text: str, collection=None) -> dict:
    """
    RAG-augmented code review:
    1. Retrieve repo-wide context from ChromaDB (RAG)
    2. Send diff + context to Groq LLM for structured analysis
    """
    # RAG: retrieve semantically similar code from vector DB
    retrieval_query = f"Code related to these changes:\n{diff_text[:800]}"
    context_chunks = retrieve_context(retrieval_query, collection=collection)

    context_block = "\n\n---\n".join([
        f"[{c['path']} lines {c['start_line']}-{c['end_line']} | relevance: {c['relevance_score']}]\n{c['text']}"
        for c in context_chunks
    ])

    user_message = f"""## Code diff to review:
```
{diff_text}
```

## Related code from repository (RAG context):
{context_block}

Review the diff for bugs, security issues, and performance problems.
Use the repository context to understand cross-file impact.
Respond with JSON only. No markdown, no backticks, just raw JSON starting with {{.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": REVIEW_SYSTEM_PROMPT},
            {"role": "user",   "content": user_message}
        ],
        temperature=0.1,       # low temp for consistent structured output
        max_tokens=4096,
    )

    raw = response.choices[0].message.content.strip()

    # Strip accidental markdown fences if model adds them
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Last resort: extract the outermost JSON object
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"LLM returned non-JSON:\n{raw}")