from __future__ import annotations

from typing import Any, Dict, List


class DemoWebMCPServer:
    def __init__(self):
        self.resources = [
            {
                "name": "web_search",
                "uri": "web://search",
                "description": "Search the web for role context and market signals.",
            }
        ]

    def handle_jsonrpc(self, message: Dict[str, Any]) -> Dict[str, Any]:
        params = message.get("params", {})
        query = params.get("query", "")
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "result": {
                "query": query,
                "results": [{
                    "title": "Python backend engineering role",
                    "summary": "Strong Python, Flask, and SQL experience is highly valued.",
                }],
            },
        }


class DemoDatabaseMCPServer:
    def __init__(self):
        self.resources = [
            {
                "name": "database",
                "uri": "db://profiles",
                "description": "Candidate metadata stored in a database.",
            }
        ]

    def handle_jsonrpc(self, message: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "result": {
                "records": [{"candidate": "alice.txt", "source": "database"}],
            },
        }
