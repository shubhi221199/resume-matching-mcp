import json
from pathlib import Path

from filesystem_mcp_server import FileSystemMCPServer
from matching_agent import MCPClient, ResumeMatchingAgent


def test_jsonrpc_resources_and_batch_process(tmp_path):
    root = tmp_path / "resumes"
    root.mkdir()
    (root / "alice.pdf").write_text("Alice resume text")
    (root / "bob.pdf").write_text("Bob resume text")

    server = FileSystemMCPServer(root_dir=str(root))
    list_response = server.handle_jsonrpc({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "resources/list",
        "params": {}
    })

    assert list_response["result"]["resources"]
    batch_response = server.handle_jsonrpc({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "filesystem.batch_process",
        "params": {
            "pattern": "*.pdf",
            "operation": "read_text",
            "include_metadata": True,
            "recursive": False
        }
    })

    assert batch_response["result"]["success"] is True
    assert len(batch_response["result"]["files"]) == 2


def test_agent_uses_mcp_client_and_matches_resumes(tmp_path):
    root = tmp_path / "resumes"
    root.mkdir()
    (root / "alice.txt").write_text("Python developer with Flask and SQL")
    (root / "bob.txt").write_text("Frontend UI designer with Figma")

    server = FileSystemMCPServer(root_dir=str(root))
    client = MCPClient(server=server)
    agent = ResumeMatchingAgent(client, job_description="Python backend engineer with Flask and SQL")

    results = agent.run()

    assert results["status"] == "completed"
    assert any(item["candidate"].startswith("alice") for item in results["matches"])
