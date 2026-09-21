from pathlib import Path

from src.filesystem_mcp_server import FileSystemMCPServer


def test_resources_list_and_read_file(tmp_path):
    root = tmp_path / "resumes"
    root.mkdir()
    resume = root / "alice.txt"
    resume.write_text("Python developer with Flask and SQL", encoding="utf-8")

    server = FileSystemMCPServer(root_dir=str(root))
    response = server.handle_jsonrpc({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "resources/list",
        "params": {},
    })
    assert response["result"]["resources"]

    read_response = server.handle_jsonrpc({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "filesystem.read_file",
        "params": {"path": "alice.txt"},
    })
    assert read_response["result"]["content"] == "Python developer with Flask and SQL"
