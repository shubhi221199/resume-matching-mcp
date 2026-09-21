# Resume Matching Workflow

```mermaid
flowchart TD
    A[Job description input] --> B[ResumeMatchingAgent]
    B --> C[MCPClient.list_resources]
    C --> D[FileSystemMCPServer.resources/list]
    B --> E[MCPClient.batch_process]
    E --> F[FileSystemMCPServer.filesystem.batch_process]
    F --> G[Read raw resume files]
    G --> H[Rank candidates by keyword match]
    H --> I[Return sorted matches]
```

The agent interacts with the filesystem through an MCP client instead of importing file-system helpers directly. This keeps the matching logic decoupled from local file access and makes it easier to add additional MCP servers later.
