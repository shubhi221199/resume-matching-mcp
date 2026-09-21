from src.filesystem_mcp_server import FileSystemMCPServer
from src.matching_agent import ResumeMatchingAgent
from src.mcp_client import MCPClient, MultiMCPClient


class DemoWebMCPServer:
    def __init__(self):
        self.resources = [{"name": "web_search", "uri": "web://search", "description": "Search the web for role context"}]

    def handle_jsonrpc(self, message):
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "result": {
                "query": message.get("params", {}).get("query", ""),
                "results": [{"title": "Python backend role", "summary": "Strong backend engineering with Flask."}],
            },
        }


class DemoDatabaseMCPServer:
    def __init__(self):
        self.resources = [{"name": "database", "uri": "db://profiles", "description": "Database metadata for candidate profiles"}]

    def handle_jsonrpc(self, message):
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "result": {
                "records": [{"candidate": "alice.txt", "source": "db"}],
            },
        }


def test_multiple_mcp_servers_are_supported(tmp_path):
    root = tmp_path / "resumes"
    root.mkdir()
    (root / "alice.txt").write_text("Python developer with Flask and SQL", encoding="utf-8")

    filesystem_server = FileSystemMCPServer(root_dir=str(root))
    web_server = DemoWebMCPServer()
    db_server = DemoDatabaseMCPServer()

    client = MultiMCPClient([
        MCPClient(server=filesystem_server),
        MCPClient(server=web_server),
        MCPClient(server=db_server),
    ])

    resources = client.list_resources()
    assert any(item["name"] == "resumes" for item in resources)
    assert any(item["name"] == "web_search" for item in resources)
    assert any(item["name"] == "database" for item in resources)

    web_results = client.call_server("web_search", {"query": "Python backend engineer"})
    assert web_results["results"][0]["title"] == "Python backend role"

    agent = ResumeMatchingAgent(client, job_description="Python backend engineer with Flask and SQL")
    result = agent.run()
    assert result["status"] == "completed"
    assert result["multi_server"] is True
