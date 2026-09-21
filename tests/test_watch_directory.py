from src.filesystem_mcp_server import FileSystemMCPServer


def test_watch_directory_reports_current_files(tmp_path):
    root = tmp_path / "watch_dir"
    root.mkdir()
    (root / "resume1.txt").write_text("Backend developer", encoding="utf-8")

    server = FileSystemMCPServer(root_dir=str(root))
    response = server.handle_jsonrpc({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "filesystem.watch_directory",
        "params": {"path": ".", "poll_interval": 1.0, "file_pattern": "*.txt"},
    })

    assert response["result"]["status"] == "watching"
    assert "resume1.txt" in response["result"]["current_files"]
