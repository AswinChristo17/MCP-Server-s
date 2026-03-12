# Excalidraw MCP Server

A lightweight Model Context Protocol (MCP) server that converts topics and explanations
into structured visual diagrams and injects them into the Excalidraw web app.

## Purpose

This MCP server generates structured Excalidraw JSON (title blocks, concept blocks,
arrows) from natural language topics, and produces browser injection scripts that
the official Playwright MCP server can use to render the diagram live in excalidraw.com.

## Architecture

```
Claude Desktop
     |
     v
MCP Gateway
     |
     +---------> excalidraw-mcp-server  (generates JSON + inject script)
     |
     +---------> mcp/playwright         (navigates browser + evaluates script)
                      |
                      v
               https://excalidraw.com   (diagram appears here)
```

No browser or Playwright dependencies are installed in the custom excalidraw image.
All browser automation is delegated to the official `mcp/playwright` image.

## Features

- **`generate_excalidraw_json`** — Generate Excalidraw JSON from a topic, concept list, and optional relationships
- **`get_inject_script`** — Convert any Excalidraw JSON into a ready-to-paste `browser_evaluate` script
- **`generate_and_get_script`** — One-shot tool: generate JSON and inject script in a single call
- **`list_tools`** — Show all available tools and usage

## Prerequisites

- Docker Desktop with MCP Toolkit enabled
- Docker MCP CLI plugin (`docker mcp` command)
- Official `mcp/playwright` image available for browser automation

## Installation

See the step-by-step installation instructions provided alongside these files.

## Usage Examples

In Claude Desktop you can ask:

- "Generate an Excalidraw diagram explaining how TCP/IP works"
- "Create a visual note for: topic=Machine Learning, concepts=Data, Model, Training, Evaluation, relationships=Data->Model, Model->Training, Training->Evaluation"
- "Use the Excalidraw MCP to draw a concept map about photosynthesis and open it in the browser"

### Typical flow in Claude Desktop

1. Call `generate_and_get_script` with your topic and concepts.
2. Ask Claude to use the Playwright MCP to open https://excalidraw.com.
3. Ask Claude to evaluate the returned script via `browser_evaluate`.
4. The diagram appears automatically in the browser.

### Concept and relationship format

**concepts** (one per line):
```
Data Collection
Model Architecture
Training Loop
Evaluation Metrics
Deployment
```

**relationships** (one per line, use `->` separator):
```
Data Collection -> Model Architecture
Model Architecture -> Training Loop
Training Loop -> Evaluation Metrics
Evaluation Metrics -> Deployment
```

## Development

### Local Testing

```bash
# Run directly (no Docker needed for quick tests)
python excalidraw_server.py

# Test MCP protocol
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python excalidraw_server.py
```

### Rebuild after changes

```bash
docker build -t excalidraw-mcp-server .
```

## Troubleshooting

**Tools not appearing in Claude Desktop**
- Verify image built: `docker images | grep excalidraw`
- Check catalog and registry files are correctly edited
- Ensure Claude Desktop config includes `--catalog=/mcp/catalogs/custom.yaml`
- Restart Claude Desktop fully (Quit, not just close window)

**window.excalidrawAPI not available**
- The inject script waits up to 10 seconds for the API to become available
- Make sure `browser_wait_for_load_state` with `networkidle` was called before `browser_evaluate`
- Try refreshing the page and running the script again

**Diagram looks blank or elements overlap**
- Try providing explicit concepts instead of relying on auto-generated ones
- Reduce the number of concepts to ≤9 for the best layout

## Security

- No API keys or secrets required
- Server runs as non-root user inside Docker
- No external network calls made by this server

## License

MIT License