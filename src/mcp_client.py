from __future__ import annotations

from typing import Any, Dict, List


class MCPClient:
    def __init__(self, server: Any):
        self.server = server

    @staticmethod
    def _normalize_resource(resource: Any) -> Dict[str, Any]:
        if isinstance(resource, dict):
            return resource
        if hasattr(resource, "name"):
            return {
                "name": getattr(resource, "name"),
                "uri": getattr(resource, "uri", ""),
                "description": getattr(resource, "description", ""),
                "mimeType": getattr(resource, "mime_type", "application/json"),
                "metadata": getattr(resource, "metadata", {}),
            }
        return {"name": str(resource)}

    def list_resources(self) -> List[Dict[str, Any]]:
        if hasattr(self.server, "resources") and isinstance(self.server.resources, list):
            return [self._normalize_resource(item) for item in self.server.resources]

        response = self.server.handle_jsonrpc({
            "jsonrpc": "2.0",
            "id": "resources-list",
            "method": "resources/list",
            "params": {},
        })
        return [self._normalize_resource(item) for item in response.get("result", {}).get("resources", [])]

    def call(self, method: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
        if hasattr(self.server, method) and callable(getattr(self.server, method)):
            return getattr(self.server, method)(**(params or {}))

        payload = {
            "jsonrpc": "2.0",
            "id": method,
            "method": method,
            "params": params or {},
        }
        response = self.server.handle_jsonrpc(payload)
        if "error" in response:
            raise RuntimeError(response["error"]["message"])
        return response.get("result", {})

    def read_resume(self, path: str) -> Dict[str, Any]:
        return self.call("filesystem.read_file", {"path": path})

    def batch_process(self, path: str = ".", pattern: str = "*", operation: str = "read_text") -> List[Dict[str, Any]]:
        result = self.call(
            "filesystem.batch_process",
            {
                "path": path,
                "pattern": pattern,
                "operation": operation,
                "recursive": False,
                "include_metadata": True,
            },
        )
        return result.get("files", [])


class MultiMCPClient:
    def __init__(self, clients: List[MCPClient]):
        self.clients = clients

    def list_resources(self) -> List[Dict[str, Any]]:
        resources: List[Dict[str, Any]] = []
        for client in self.clients:
            resources.extend(client.list_resources())
        return resources

    def call_server(self, server_name: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
        for client in self.clients:
            resources = client.list_resources()
            if any(resource.get("name") == server_name for resource in resources):
                if hasattr(client.server, server_name) and callable(getattr(client.server, server_name)):
                    return getattr(client.server, server_name)(**(params or {}))
                return client.call(server_name, params or {})
        raise RuntimeError(f"No MCP server registered with resource name: {server_name}")

    def batch_process(self, path: str = ".", pattern: str = "*", operation: str = "read_text") -> List[Dict[str, Any]]:
        for client in self.clients:
            try:
                return client.batch_process(path=path, pattern=pattern, operation=operation)
            except Exception:
                continue
        return []
