import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


class JSONRPCError(Exception):
    def __init__(self, code: int, message: str, data: Optional[Any] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


@dataclass
class ResourceInfo:
    name: str
    uri: str
    description: str
    mime_type: str = "application/json"
    metadata: Dict[str, Any] = field(default_factory=dict)


class FileSystemMCPServer:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir).resolve()
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.resources = [
            ResourceInfo(
                name="resumes",
                uri="file://resumes",
                description="Resume files exposed for matching and indexing.",
                mime_type="application/json",
                metadata={"type": "directory"},
            ),
            ResourceInfo(
                name="directory_watch",
                uri="file://watch",
                description="Directory monitoring state for resume ingestion.",
                mime_type="application/json",
                metadata={"type": "watch"},
            ),
        ]

    def list_resources(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": resource.name,
                "uri": resource.uri,
                "description": resource.description,
                "mimeType": resource.mime_type,
                "metadata": resource.metadata,
            }
            for resource in self.resources
        ]

    def _to_relative_path(self, path: str) -> Path:
        candidate = (self.root_dir / path).resolve()
        if self.root_dir not in candidate.parents and candidate != self.root_dir:
            raise JSONRPCError(-32002, "Access denied outside configured root directory")
        return candidate

    def read_file(self, path: str) -> Dict[str, Any]:
        file_path = self._to_relative_path(path)
        if not file_path.exists() or not file_path.is_file():
            raise JSONRPCError(-32001, f"File not found: {path}")
        return {
            "path": str(file_path.relative_to(self.root_dir)),
            "content": file_path.read_text(encoding="utf-8", errors="replace"),
            "size": file_path.stat().st_size,
        }

    def list_directory(self, path: str = ".") -> Dict[str, Any]:
        directory = self._to_relative_path(path)
        if not directory.exists() or not directory.is_dir():
            raise JSONRPCError(-32001, f"Directory not found: {path}")
        entries = []
        for item in sorted(directory.iterdir()):
            entries.append(
                {
                    "name": item.name,
                    "path": str(item.relative_to(self.root_dir)),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                }
            )
        return {"path": str(directory.relative_to(self.root_dir)), "entries": entries}

    def watch_directory(self, path: str = ".", poll_interval: float = 1.0, file_pattern: str = "*") -> Dict[str, Any]:
        directory = self._to_relative_path(path)
        if not directory.exists() or not directory.is_dir():
            raise JSONRPCError(-32001, f"Directory not found: {path}")
        known_files = {p.name for p in directory.glob(file_pattern) if p.is_file()}
        return {
            "path": str(directory.relative_to(self.root_dir)),
            "poll_interval": poll_interval,
            "file_pattern": file_pattern,
            "status": "watching",
            "current_files": sorted(known_files),
        }

    def batch_process(
        self,
        path: str = ".",
        pattern: str = "*",
        operation: str = "read_text",
        recursive: bool = False,
        include_metadata: bool = False,
    ) -> Dict[str, Any]:
        directory = self._to_relative_path(path)
        if not directory.exists() or not directory.is_dir():
            raise JSONRPCError(-32001, f"Directory not found: {path}")

        matches = directory.rglob(pattern) if recursive else directory.glob(pattern)
        files = []
        for item in sorted(matches, key=lambda p: str(p)):
            if not item.is_file():
                continue
            payload = {"path": str(item.relative_to(self.root_dir))}
            if operation == "read_text":
                payload["content"] = item.read_text(encoding="utf-8", errors="replace")
            elif operation == "stat":
                payload["size"] = item.stat().st_size
            elif operation == "metadata":
                stat = item.stat()
                payload["metadata"] = {
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "extension": item.suffix,
                }
            else:
                raise JSONRPCError(-32602, f"Unsupported operation: {operation}")
            if include_metadata:
                stat = item.stat()
                payload["metadata"] = {
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "extension": item.suffix,
                }
            files.append(payload)

        return {
            "path": str(directory.relative_to(self.root_dir)),
            "success": True,
            "count": len(files),
            "files": files,
        }

    def handle_jsonrpc(self, message: Dict[str, Any]) -> Dict[str, Any]:
        request_id = message.get("id")
        method = message.get("method")
        params = message.get("params", {}) or {}

        if message.get("jsonrpc") != "2.0":
            raise JSONRPCError(-32600, "Invalid JSON-RPC version")
        if not method:
            raise JSONRPCError(-32600, "Missing method")

        try:
            if method == "resources/list":
                result = {"resources": self.list_resources()}
            elif method == "filesystem.read_file":
                result = self.read_file(params.get("path", "."))
            elif method == "filesystem.list_directory":
                result = self.list_directory(params.get("path", "."))
            elif method == "filesystem.watch_directory":
                result = self.watch_directory(
                    path=params.get("path", "."),
                    poll_interval=float(params.get("poll_interval", 1.0)),
                    file_pattern=params.get("file_pattern", "*"),
                )
            elif method == "filesystem.batch_process":
                result = self.batch_process(
                    path=params.get("path", "."),
                    pattern=params.get("pattern", "*"),
                    operation=params.get("operation", "read_text"),
                    recursive=bool(params.get("recursive", False)),
                    include_metadata=bool(params.get("include_metadata", False)),
                )
            else:
                raise JSONRPCError(-32601, f"Method not found: {method}")
            return {"jsonrpc": "2.0", "id": request_id, "result": result}
        except JSONRPCError as exc:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": exc.code, "message": exc.message, "data": exc.data},
            }
        except Exception as exc:  # pragma: no cover - defensive
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32603, "message": "Internal error", "data": str(exc)},
            }

    def serve_forever(self):
        while True:
            raw = input()
            if not raw:
                continue
            request = json.loads(raw)
            if isinstance(request, list):
                response = [self.handle_jsonrpc(item) for item in request]
            else:
                response = self.handle_jsonrpc(request)
            print(json.dumps(response))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Filesystem MCP server")
    parser.add_argument("--root-dir", default=".", help="Directory to expose as a filesystem resource")
    args = parser.parse_args()
    server = FileSystemMCPServer(root_dir=args.root_dir)
    server.serve_forever()
