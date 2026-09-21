from src.filesystem_mcp_server import FileSystemMCPServer


def test_batch_process_reads_all_files(tmp_path):
    root = tmp_path / "resumes"
    root.mkdir()
    (root / "a.txt").write_text("Python backend", encoding="utf-8")
    (root / "b.txt").write_text("UI design", encoding="utf-8")

    server = FileSystemMCPServer(root_dir=str(root))
    response = server.handle_jsonrpc({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "filesystem.batch_process",
        "params": {"path": ".", "pattern": "*.txt", "operation": "read_text", "include_metadata": True},
    })

    assert response["result"]["success"] is True
    assert response["result"]["count"] == 2
    assert len(response["result"]["files"]) == 2
