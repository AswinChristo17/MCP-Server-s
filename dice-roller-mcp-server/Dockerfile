FROM python:3.11-slim

# MCP REQUIRED LABELS 🔥
LABEL docker-mcp=true
LABEL docker-mcp-name=dice-roller
LABEL docker-mcp-tool-type=mcp
LABEL docker-mcp-transport=stdio

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY dice_roller_server.py .

RUN useradd -m -u 1000 mcpuser && \
    chown -R mcpuser:mcpuser /app

USER mcpuser

CMD ["python", "dice_roller_server.py"]