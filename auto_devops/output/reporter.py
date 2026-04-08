import json
from datetime import datetime


def generate_report(agent_state: dict, output_path: str = "./review_report.json") -> str:
    """
    Save the full agent state as a structured JSON report with explainability.
    """
    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "decision": agent_state.get("decision"),
        "explanation": agent_state.get("explanation"),
        "overall_risk": agent_state.get("review", {}).get("overall_risk"),
        "summary": agent_state.get("review", {}).get("summary"),
        "issues": agent_state.get("review", {}).get("issues", []),
        "rag_context_used": [
            {"path": c["path"], "relevance": c["relevance_score"]}
            for c in agent_state.get("context_chunks", [])
        ],
        "fix_applied": agent_state.get("fix_applied"),
        "tests_passed": agent_state.get("tests_passed"),
        "branch_created": agent_state.get("branch_created"),
    }

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n[reporter] Report saved → {output_path}")
    return json.dumps(report, indent=2)
