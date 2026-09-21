from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


class MCPClient:
    def __init__(self, server: Any):
        self.server = server

    def list_resources(self) -> List[Dict[str, Any]]:
        response = self.server.handle_jsonrpc({
            "jsonrpc": "2.0",
            "id": "resources-list",
            "method": "resources/list",
            "params": {},
        })
        return response.get("result", {}).get("resources", [])

    def read_resume(self, path: str) -> Dict[str, Any]:
        response = self.server.handle_jsonrpc({
            "jsonrpc": "2.0",
            "id": f"read-{path}",
            "method": "filesystem.read_file",
            "params": {"path": path},
        })
        if "error" in response:
            raise RuntimeError(response["error"]["message"])
        return response["result"]

    def batch_process(self, path: str = ".", pattern: str = "*", operation: str = "read_text") -> List[Dict[str, Any]]:
        response = self.server.handle_jsonrpc({
            "jsonrpc": "2.0",
            "id": "batch-process",
            "method": "filesystem.batch_process",
            "params": {
                "path": path,
                "pattern": pattern,
                "operation": operation,
                "recursive": False,
                "include_metadata": True,
            },
        })
        if "error" in response:
            raise RuntimeError(response["error"]["message"])
        return response["result"].get("files", [])


@dataclass
class ResumeMatchResult:
    candidate: str
    score: float
    reasons: List[str] = field(default_factory=list)


class ResumeMatchingAgent:
    def __init__(self, client: MCPClient, job_description: str):
        self.client = client
        self.job_description = job_description.lower()

    def _score_resume(self, text: str) -> tuple[float, List[str]]:
        lowered = text.lower()
        tokens = [item for item in ["python", "flask", "sql", "backend", "developer", "engineer"] if item in lowered]
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
            match = {
                "candidate": item.get("path", "unknown"),
                "score": score,
                "reasons": reasons,
            }
            if score > 0:
                matches.append(match)

        matches.sort(key=lambda record: record["score"], reverse=True)
        return {
            "status": "completed",
            "resources": [r["name"] for r in resources],
            "matches": matches,
            "job_description": self.job_description,
        }


if __name__ == "__main__":
    root = Path("resumes")
    root.mkdir(exist_ok=True)

    server = None
    try:
        from filesystem_mcp_server import FileSystemMCPServer

        server = FileSystemMCPServer(root_dir=str(root))
    except Exception:
        server = FileSystemMCPServer(root_dir=".")

    client = MCPClient(server=server)
    agent = ResumeMatchingAgent(client, job_description="Python backend engineer with Flask and SQL")
    print(json.dumps(agent.run(), indent=2))
