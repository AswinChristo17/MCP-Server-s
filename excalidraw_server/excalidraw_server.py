#!/usr/bin/env python3
"""
Excalidraw MCP Server - Generates structured Excalidraw JSON diagrams from topics.
"""

import sys
import json
import logging
import math
import gzip
import base64
from mcp.server.fastmcp import FastMCP

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("excalidraw-server")

# Initialize MCP server
mcp = FastMCP("excalidraw")

# === CONSTANTS ===
EXCALIDRAW_VERSION = 2
APP_STATE_VERSION = 2

# Element sizing
TITLE_WIDTH = 400
TITLE_HEIGHT = 70
TITLE_FONT_SIZE = 24

CONCEPT_WIDTH = 200
CONCEPT_HEIGHT = 60
CONCEPT_FONT_SIZE = 16

DETAIL_WIDTH = 180
DETAIL_HEIGHT = 50
DETAIL_FONT_SIZE = 13

CANVAS_START_X = 100
CANVAS_START_Y = 100
H_GAP = 60   # horizontal gap between columns
V_GAP = 40   # vertical gap between rows


# === UTILITY FUNCTIONS ===

def make_id(seed: int) -> str:
    """Generate a simple deterministic ID string."""
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    result = ""
    n = seed + 1000
    while n > 0:
        result = chars[n % len(chars)] + result
        n = n // len(chars)
    return result.zfill(8)


def make_rectangle(eid, x, y, width, height, label, font_size=16, bg_color="#e8f4f8", stroke_color="#1a73e8"):
    """Build a rectangle element dict."""
    return {
        "id": eid,
        "type": "rectangle",
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "angle": 0,
        "strokeColor": stroke_color,
        "backgroundColor": bg_color,
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roughness": 1,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": {"type": 3},
        "seed": hash(eid) % 100000,
        "version": 1,
        "versionNonce": 0,
        "isDeleted": False,
        "boundElements": [],
        "updated": 1,
        "link": None,
        "locked": False,
        "label": {
            "text": label,
            "fontSize": font_size,
            "fontFamily": 1,
            "textAlign": "center",
            "verticalAlign": "middle"
        }
    }


def make_text(eid, x, y, text, font_size=16, color="#000000"):
    """Build a standalone text element dict."""
    return {
        "id": eid,
        "type": "text",
        "x": x,
        "y": y,
        "width": len(text) * font_size * 0.6,
        "height": font_size + 8,
        "angle": 0,
        "strokeColor": color,
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 0,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": None,
        "seed": hash(eid) % 100000,
        "version": 1,
        "versionNonce": 0,
        "isDeleted": False,
        "boundElements": [],
        "updated": 1,
        "link": None,
        "locked": False,
        "text": text,
        "fontSize": font_size,
        "fontFamily": 1,
        "textAlign": "left",
        "verticalAlign": "top",
        "containerId": None,
        "originalText": text,
        "lineHeight": 1.25
    }


def make_arrow(eid, start_id, end_id, sx, sy, ex, ey):
    """Build an arrow element between two elements."""
    return {
        "id": eid,
        "type": "arrow",
        "x": sx,
        "y": sy,
        "width": abs(ex - sx),
        "height": abs(ey - sy),
        "angle": 0,
        "strokeColor": "#1a73e8",
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roughness": 1,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": {"type": 2},
        "seed": hash(eid) % 100000,
        "version": 1,
        "versionNonce": 0,
        "isDeleted": False,
        "boundElements": [],
        "updated": 1,
        "link": None,
        "locked": False,
        "points": [[0, 0], [ex - sx, ey - sy]],
        "lastCommittedPoint": None,
        "startBinding": {"elementId": start_id, "focus": 0, "gap": 6},
        "endBinding": {"elementId": end_id, "focus": 0, "gap": 6},
        "startArrowhead": None,
        "endArrowhead": "arrow"
    }


def build_excalidraw_scene(elements):
    """Wrap elements in a full Excalidraw file envelope."""
    return {
        "type": "excalidraw",
        "version": EXCALIDRAW_VERSION,
        "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {
            "gridSize": None,
            "viewBackgroundColor": "#ffffff"
        },
        "files": {}
    }


def parse_topic_to_structure(topic: str, concepts_raw: str, relationships_raw: str):
    """Parse inputs supporting both comma-separated and newline-separated values."""
    concepts = []
    if concepts_raw.strip():
        raw = concepts_raw.strip()
        lines = raw.splitlines() if "\n" in raw else raw.split(",")
        for line in lines:
            line = line.strip().lstrip("-\u2022*").strip()
            if line:
                concepts.append(line)

    relationships = []
    if relationships_raw.strip():
        raw = relationships_raw.strip()
        lines = raw.splitlines() if "\n" in raw else raw.split(",")
        for line in lines:
            line = line.strip().lstrip("-\u2022*").strip()
            if "->" in line:
                parts = line.split("->", 1)
                src = parts[0].strip()
                tgt = parts[1].strip()
                if src and tgt:
                    relationships.append((src, tgt))

    return topic.strip(), concepts, relationships


def generate_diagram_elements(title: str, concepts: list, relationships: list):
    """Generate Excalidraw element list from structured data."""
    elements = []
    id_counter = [0]

    def next_id():
        id_counter[0] += 1
        return make_id(id_counter[0])

    # --- Title block ---
    title_id = next_id()
    title_x = CANVAS_START_X
    title_y = CANVAS_START_Y
    title_el = make_rectangle(
        title_id, title_x, title_y,
        TITLE_WIDTH, TITLE_HEIGHT,
        title, TITLE_FONT_SIZE,
        bg_color="#1a73e8", stroke_color="#0d47a1"
    )
    # Override label color to white for dark background
    title_el["label"]["color"] = "#ffffff"
    elements.append(title_el)

    # --- Concept blocks ---
    concept_ids = {}
    concept_positions = {}

    cols = min(3, max(1, len(concepts)))
    row_start_y = title_y + TITLE_HEIGHT + V_GAP + 40

    for i, concept in enumerate(concepts):
        col = i % cols
        row = i // cols
        cx = CANVAS_START_X + col * (CONCEPT_WIDTH + H_GAP)
        cy = row_start_y + row * (CONCEPT_HEIGHT + V_GAP)

        cid = next_id()
        concept_ids[concept.lower()] = cid
        concept_positions[concept.lower()] = (cx, cy)

        el = make_rectangle(
            cid, cx, cy,
            CONCEPT_WIDTH, CONCEPT_HEIGHT,
            concept, CONCEPT_FONT_SIZE,
            bg_color="#e8f4f8", stroke_color="#1a73e8"
        )
        elements.append(el)

        # Arrow from title to first row of concepts
        if row == 0:
            arrow_id = next_id()
            sx = title_x + TITLE_WIDTH // 2
            sy = title_y + TITLE_HEIGHT
            ex = cx + CONCEPT_WIDTH // 2
            ey = cy
            elements.append(make_arrow(arrow_id, title_id, cid, sx, sy, ex, ey))

    # --- Relationship arrows between concepts ---
    for (src, tgt) in relationships:
        src_key = src.lower()
        tgt_key = tgt.lower()

        # Find best-matching concept keys
        src_id = None
        tgt_id = None
        src_pos = None
        tgt_pos = None

        for key in concept_ids:
            if src_key in key or key in src_key:
                src_id = concept_ids[key]
                src_pos = concept_positions[key]
        for key in concept_ids:
            if tgt_key in key or key in tgt_key:
                tgt_id = concept_ids[key]
                tgt_pos = concept_positions[key]

        if src_id and tgt_id and src_pos and tgt_pos:
            arrow_id = next_id()
            sx = src_pos[0] + CONCEPT_WIDTH
            sy = src_pos[1] + CONCEPT_HEIGHT // 2
            ex = tgt_pos[0]
            ey = tgt_pos[1] + CONCEPT_HEIGHT // 2
            elements.append(make_arrow(arrow_id, src_id, tgt_id, sx, sy, ex, ey))

    return elements


# === MCP TOOLS ===

@mcp.tool()
async def generate_excalidraw_json(topic: str = "", concepts: str = "", relationships: str = "") -> str:
    """Generate Excalidraw JSON for a topic with key concepts and optional relationships."""
    logger.info(f"generate_excalidraw_json called: topic={topic!r}")

    if not topic.strip():
        return "❌ Error: 'topic' is required. Provide a title for the diagram."

    try:
        title, concept_list, rel_list = parse_topic_to_structure(topic, concepts, relationships)

        if not concept_list:
            # Auto-generate placeholder concepts if none provided
            concept_list = [
                f"{title} Overview",
                "Key Points",
                "How It Works",
                "Use Cases",
                "Summary"
            ]

        elements = generate_diagram_elements(title, concept_list, rel_list)
        scene = build_excalidraw_scene(elements)
        json_str = json.dumps(scene, indent=2)

        return f"""✅ Excalidraw JSON generated for topic: "{title}"
📊 Elements: {len(elements)} (title block + {len(concept_list)} concept blocks + arrows)

JSON (paste into Excalidraw or use inject_into_excalidraw tool):
```json
{json_str}
```"""

    except Exception as e:
        logger.error(f"Error generating Excalidraw JSON: {e}", exc_info=True)
        return f"❌ Error generating diagram: {str(e)}"


@mcp.tool()
async def get_inject_script(excalidraw_json: str = "") -> str:
    """Return a JavaScript snippet to inject Excalidraw JSON into an open excalidraw.com tab via window.excalidrawAPI."""
    logger.info("get_inject_script called")

    if not excalidraw_json.strip():
        return "❌ Error: 'excalidraw_json' is required. Pass the JSON string produced by generate_excalidraw_json."

    try:
        # Validate the JSON
        parsed = json.loads(excalidraw_json)
        if parsed.get("type") != "excalidraw":
            return "❌ Error: JSON does not appear to be valid Excalidraw format (missing type: excalidraw)."

        script = f"""async (page) => {{
  // Step 1: Write scene into localStorage before the app reads it
  await page.evaluate((sceneJson) => {{
    const scene = JSON.parse(sceneJson);
    // Excalidraw reads from this localStorage key on startup
    localStorage.setItem("excalidraw", JSON.stringify(scene.elements));
    localStorage.setItem("excalidraw-state", JSON.stringify(scene.appState));
  }}, {json.dumps(excalidraw_json)});

  // Step 2: Reload so Excalidraw picks up the localStorage data
  await page.reload({{ waitUntil: "networkidle" }});

  // Step 3: Confirm elements loaded
  const count = await page.evaluate(() => {{
    try {{
      const els = JSON.parse(localStorage.getItem("excalidraw") || "[]");
      return els.length;
    }} catch(e) {{
      return -1;
    }}
  }});

  return "SUCCESS: Scene loaded with " + count + " elements. Check the browser tab.";
}}"""

        return f"""✅ Injection script ready.

Steps to use with the Playwright MCP server:
1. Use browser_navigate to go to https://excalidraw.com
2. Wait for networkidle
3. Call browser_evaluate with the script below (it writes to localStorage then reloads)

--- SCRIPT START ---
{script}
--- SCRIPT END ---"""

    except json.JSONDecodeError as e:
        return f"❌ Error: Invalid JSON provided: {str(e)}"
    except Exception as e:
        logger.error(f"Error building inject script: {e}", exc_info=True)
        return f"❌ Error: {str(e)}"


@mcp.tool()
async def generate_and_get_script(topic: str = "", concepts: str = "", relationships: str = "") -> str:
    """One-shot: generate Excalidraw JSON for a topic and return the browser injection script."""
    logger.info(f"generate_and_get_script called: topic={topic!r}")

    if not topic.strip():
        return "❌ Error: 'topic' is required."

    try:
        title, concept_list, rel_list = parse_topic_to_structure(topic, concepts, relationships)

        if not concept_list:
            concept_list = [
                f"{title} Overview",
                "Key Points",
                "How It Works",
                "Use Cases",
                "Summary"
            ]

        elements = generate_diagram_elements(title, concept_list, rel_list)
        scene = build_excalidraw_scene(elements)
        json_str = json.dumps(scene)

        script = f"""async (page) => {{
  await page.evaluate((sceneJson) => {{
    const scene = JSON.parse(sceneJson);
    localStorage.setItem("excalidraw", JSON.stringify(scene.elements));
    localStorage.setItem("excalidraw-state", JSON.stringify(scene.appState));
  }}, {json.dumps(json_str)});

  await page.reload({{ waitUntil: "networkidle" }});

  const count = await page.evaluate(() => {{
    try {{
      const els = JSON.parse(localStorage.getItem("excalidraw") || "[]");
      return els.length;
    }} catch(e) {{ return -1; }}
  }});

  return "SUCCESS: Scene loaded with " + count + " elements. Check the browser tab.";
}}"""

        return f"""✅ Diagram ready for "{title}"
📊 {len(elements)} elements ({len(concept_list)} concept blocks + arrows)

To render it:
1. browser_navigate → https://excalidraw.com
2. browser_wait_for_load_state → networkidle
3. browser_evaluate → paste the script below

--- INJECT SCRIPT ---
{script}
--- END SCRIPT ---"""

    except Exception as e:
        logger.error(f"Error in generate_and_get_script: {e}", exc_info=True)
        return f"❌ Error: {str(e)}"



@mcp.tool()
async def get_excalidraw_url(excalidraw_json: str = "") -> str:
    """Encode Excalidraw JSON into a direct URL that opens the diagram in excalidraw.com."""
    logger.info("get_excalidraw_url called")

    if not excalidraw_json.strip():
        return "❌ Error: excalidraw_json is required."

    try:
        parsed = json.loads(excalidraw_json)
        if parsed.get("type") != "excalidraw":
            return "❌ Error: JSON does not appear to be valid Excalidraw format."

        compressed = gzip.compress(excalidraw_json.encode("utf-8"), compresslevel=9)
        encoded = base64.urlsafe_b64encode(compressed).decode("ascii").rstrip("=")
        url = f"https://excalidraw.com/#json={encoded}"

        return f"""✅ Excalidraw URL ready!

Open this URL in the browser to see your diagram:
{url}

With Playwright MCP use:
  browser_navigate → {url}"""

    except json.JSONDecodeError as e:
        return f"❌ Error: Invalid JSON: {str(e)}"
    except Exception as e:
        logger.error(f"Error encoding URL: {e}", exc_info=True)
        return f"❌ Error: {str(e)}"


@mcp.tool()
async def generate_excalidraw_url(topic: str = "", concepts: str = "", relationships: str = "") -> str:
    """One-shot: generate diagram and return a direct excalidraw.com URL. Best tool to use."""
    logger.info(f"generate_excalidraw_url called: topic={topic!r}")

    if not topic.strip():
        return "❌ Error: topic is required."

    try:
        title, concept_list, rel_list = parse_topic_to_structure(topic, concepts, relationships)

        if not concept_list:
            concept_list = [
                f"{title} Overview",
                "Key Points",
                "How It Works",
                "Use Cases",
                "Summary"
            ]

        elements = generate_diagram_elements(title, concept_list, rel_list)
        scene = build_excalidraw_scene(elements)
        json_str = json.dumps(scene)

        compressed = gzip.compress(json_str.encode("utf-8"), compresslevel=9)
        encoded = base64.urlsafe_b64encode(compressed).decode("ascii").rstrip("=")
        url = f"https://excalidraw.com/#json={encoded}"

        return f"""✅ Diagram ready for "{title}"
📊 {len(elements)} elements ({len(concept_list)} concept blocks + arrows)

🌐 Open this URL to view the diagram:
{url}

With Playwright MCP:
  browser_navigate → {url}"""

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return f"❌ Error: {str(e)}"


@mcp.tool()
async def list_tools() -> str:
    """List all available Excalidraw MCP tools and their usage."""
    return """📊 Excalidraw MCP Server - Available Tools

⭐ RECOMMENDED WORKFLOW (simplest):
  1. generate_excalidraw_url(topic, concepts, relationships)
     → returns a direct excalidraw.com URL with diagram embedded
  2. Playwright MCP: browser_navigate to that URL
     → diagram appears instantly, no injection needed

TOOLS:

1. generate_excalidraw_url  ⭐ USE THIS FIRST
   One-shot: generate diagram and return a direct excalidraw.com URL.
   Params:
   - topic (required): Title/subject of the diagram
   - concepts: Comma or newline separated concept labels
   - relationships: Comma or newline separated "Source -> Target" pairs

2. generate_excalidraw_json
   Generate raw Excalidraw JSON (for saving as .excalidraw file).
   Params: topic, concepts, relationships

3. get_excalidraw_url
   Encode existing Excalidraw JSON into a direct URL.
   Params: excalidraw_json (required)

4. get_inject_script
   Generate a browser_evaluate script (fallback method).
   Params: excalidraw_json (required)

5. generate_and_get_script
   One-shot JSON + inject script (fallback method).
   Params: topic, concepts, relationships

6. list_tools
   Show this help message."""


# === SERVER STARTUP ===
if __name__ == "__main__":
    logger.info("Starting Excalidraw MCP server...")
    try:
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)