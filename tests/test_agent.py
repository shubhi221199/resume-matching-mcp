from src.filesystem_mcp_server import FileSystemMCPServer
from src.mcp_client import MCPClient
from src.matching_agent import ResumeMatchingAgent


def test_agent_ranks_resume_matches(tmp_path):
    root = tmp_path / "resumes"
    root.mkdir()
    (root / "alice.txt").write_text("Python developer with Flask and SQL", encoding="utf-8")
    (root / "bob.txt").write_text("Designer with Figma and UX", encoding="utf-8")

    server = FileSystemMCPServer(root_dir=str(root))
    client = MCPClient(server=server)
    agent = ResumeMatchingAgent(client, job_description="Python backend engineer with Flask and SQL")

    result = agent.run()
    assert result["status"] == "completed"
    assert result["matches"][0]["candidate"].startswith("alice")
