from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

from .config import DEFAULT_JOB_DESCRIPTION, KEYWORDS
from .mcp_client import MCPClient, MultiMCPClient


@dataclass
class ResumeMatchResult:
    candidate: str
    score: float
    reasons: List[str] = field(default_factory=list)


class ResumeMatchingAgent:
    def __init__(self, client: MCPClient | MultiMCPClient, job_description: str = DEFAULT_JOB_DESCRIPTION):
        self.client = client
        self.job_description = job_description.lower()

    def _score_resume(self, text: str) -> tuple[float, List[str]]:
        lowered = text.lower()
        tokens = [keyword for keyword in KEYWORDS if keyword in lowered]
        score = (len(tokens) * 20) + min(20, len(lowered.split()) * 0.2)
        reasons = [f"matched keyword: {token}" for token in tokens]
        return round(score, 2), reasons

    def run(self) -> Dict[str, Any]:
        resources = self.client.list_resources()
        files = self.client.batch_process(path=".", pattern="*", operation="read_text")
        matches: List[Dict[str, Any]] = []

        for item in files:
            content = item.get("content", "")
            score, reasons = self._score_resume(content)
            if score > 0:
                matches.append({
                    "candidate": item.get("path", "unknown"),
                    "score": score,
                    "reasons": reasons,
                })

        matches.sort(key=lambda record: record["score"], reverse=True)
        external_context = {}
        if hasattr(self.client, "call_server"):
            try:
                external_context = self.client.call_server("web_search", {"query": self.job_description})
            except Exception:
                external_context = {}

        return {
            "status": "completed",
            "resources": [r["name"] for r in resources],
            "matches": matches,
            "job_description": self.job_description,
            "multi_server": hasattr(self.client, "clients"),
            "external_context": external_context,
        }


if __name__ == "__main__":
    import argparse
    from .filesystem_mcp_server import FileSystemMCPServer

    parser = argparse.ArgumentParser(description="Match resumes against a job description")
    parser.add_argument("--job-description", help="Job requirements to match against")
    args = parser.parse_args()
    job_description = args.job_description or input(
        f"Enter job description [{DEFAULT_JOB_DESCRIPTION}]: "
    ).strip() or DEFAULT_JOB_DESCRIPTION

    root = Path("data/resumes")
    root.mkdir(parents=True, exist_ok=True)
    server = FileSystemMCPServer(root_dir=str(root))
    client = MCPClient(server=server)
    agent = ResumeMatchingAgent(client, job_description=job_description)
    print(json.dumps(agent.run(), indent=2))
