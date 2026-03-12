# Dice Roller MCP Server

A Model Context Protocol (MCP) server that provides dice rolling, coin flipping,
and D&D mechanics for AI assistants like Claude Desktop.

## Purpose

This MCP server gives AI assistants a full suite of randomization and tabletop
RPG tools — from simple coin flips to full D&D ability score generation.

## Features

### Tools Included

- **`coin_flip`** - Flip one or more coins, returns Heads/Tails results with summary
- **`roll_dice`** - Roll any dice using standard XdY notation (e.g. 2d6, 1d20, 4d8)
- **`dnd_ability_scores`** - Generate a full D&D ability score set (4d6 drop lowest)
- **`dnd_attack_roll`** - Roll a d20 attack with modifier + advantage/disadvantage
- **`dnd_damage_roll`** - Roll damage dice with optional flat modifier
- **`dnd_saving_throw`** - Roll a saving throw and compare against a DC
- **`roll_with_advantage`** - Roll any dice twice, take the higher result
- **`roll_with_disadvantage`** - Roll any dice twice, take the lower result
- **`roll_initiative`** - Roll d20 initiative with DEX modifier
- **`random_number`** - Generate a random number between any two values

## Prerequisites

- Docker Desktop with MCP Toolkit enabled
- Docker MCP CLI plugin (`docker mcp` command)

## Installation

See the step-by-step instructions provided with the files.

## Usage Examples

In Claude Desktop, you can ask:
- "Flip a coin"
- "Roll 2d6"
- "Roll 4d8 damage with +3 modifier"
- "Generate D&D ability scores for my new character"
- "Roll an attack with advantage and +5 modifier"
- "Roll initiative with DEX modifier of +2"
- "Make a saving throw against DC 14 with +3 modifier"
- "Give me a random number between 1 and 50"

## Architecture

```
Claude Desktop → MCP Gateway → Dice Roller MCP Server
                                      ↓
                               Python random module
```

## Development

### Local Testing

```bash
# Run directly
python dice_roller_server.py

# Test MCP protocol
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python dice_roller_server.py
```

### Adding New Tools

1. Add the function to `dice_roller_server.py`
2. Decorate with `@mcp.tool()`
3. Update the catalog entry with the new tool name
4. Rebuild the Docker image

## Troubleshooting

**Tools Not Appearing**
- Verify Docker image built successfully: `docker images | grep dice-roller`
- Check catalog and registry files
- Ensure Claude Desktop config includes `custom.yaml`
- Restart Claude Desktop completely

## Security

- Runs as non-root user inside Docker
- No API keys or secrets required
- No external network calls — all logic is local

## License

MIT License