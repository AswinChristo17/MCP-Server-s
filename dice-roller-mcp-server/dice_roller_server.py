#!/usr/bin/env python3
"""
Dice Roller MCP Server - Coin flips, DnD dice, and custom dice rolling mechanics.
"""

import sys
import logging
import random
from mcp.server.fastmcp import FastMCP

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("dice-roller-server")

# Initialize MCP server
mcp = FastMCP("dice-roller")


# === UTILITY FUNCTIONS ===

def parse_dice_notation(notation: str):
    """Parse XdY notation into (count, sides). Returns (count, sides) or raises ValueError."""
    notation = notation.strip().lower()
    if "d" not in notation:
        raise ValueError(f"Invalid dice notation: {notation}. Use XdY format (e.g. 2d6).")
    parts = notation.split("d")
    count = int(parts[0]) if parts[0] else 1
    sides = int(parts[1])
    if count < 1 or count > 100:
        raise ValueError("Dice count must be between 1 and 100.")
    if sides < 2 or sides > 10000:
        raise ValueError("Dice sides must be between 2 and 10000.")
    return count, sides


# === MCP TOOLS ===

@mcp.tool()
async def coin_flip(flips: str = "1") -> str:
    """Flip one or more coins and return heads or tails results."""
    logger.info(f"coin_flip called with flips={flips}")
    try:
        count = int(flips.strip()) if flips.strip() else 1
        if count < 1 or count > 100:
            return "❌ Error: Number of flips must be between 1 and 100."
        results = [random.choice(["Heads", "Tails"]) for _ in range(count)]
        heads = results.count("Heads")
        tails = results.count("Tails")
        if count == 1:
            emoji = "🪙 Heads!" if results[0] == "Heads" else "🪙 Tails!"
            return emoji
        result_str = ", ".join(results)
        return f"""🪙 Coin Flip Results ({count} flips):
{result_str}

📊 Summary: {heads} Heads, {tails} Tails"""
    except ValueError:
        return f"❌ Error: Invalid number of flips: {flips}"
    except Exception as e:
        logger.error(f"Error in coin_flip: {e}")
        return f"❌ Error: {str(e)}"


@mcp.tool()
async def roll_dice(notation: str = "1d6") -> str:
    """Roll dice using standard XdY notation (e.g. 2d6, 1d20, 4d8)."""
    logger.info(f"roll_dice called with notation={notation}")
    try:
        count, sides = parse_dice_notation(notation if notation.strip() else "1d6")
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls)
        roll_str = ", ".join(str(r) for r in rolls)
        if count == 1:
            return f"🎲 d{sides} → **{total}**"
        return f"""🎲 {count}d{sides}:
Rolls: [{roll_str}]
Total: {total}"""
    except ValueError as e:
        return f"❌ Error: {str(e)}"
    except Exception as e:
        logger.error(f"Error in roll_dice: {e}")
        return f"❌ Error: {str(e)}"


@mcp.tool()
async def dnd_ability_scores() -> str:
    """Roll a full set of 6 D&D ability scores using the 4d6 drop-lowest method."""
    logger.info("dnd_ability_scores called")
    try:
        abilities = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
        results = []
        for ability in abilities:
            rolls = [random.randint(1, 6) for _ in range(4)]
            total = sum(sorted(rolls)[1:])  # drop lowest
            rolls_str = ", ".join(str(r) for r in rolls)
            dropped = min(rolls)
            results.append(f"  {ability:<14} {total:>2}  (rolled: [{rolls_str}], dropped: {dropped})")
        scores = [int(r.split()[1]) for r in results]
        total_modifier = sum((s - 10) // 2 for s in scores)
        output = "\n".join(results)
        return f"""⚔️ D&D Ability Scores (4d6 drop lowest):

{output}

📊 Total Modifier: {'+' if total_modifier >= 0 else ''}{total_modifier}"""
    except Exception as e:
        logger.error(f"Error in dnd_ability_scores: {e}")
        return f"❌ Error: {str(e)}"


@mcp.tool()
async def dnd_attack_roll(modifier: str = "0", advantage: str = "") -> str:
    """Roll a D&D attack roll (d20) with optional modifier and advantage/disadvantage."""
    logger.info(f"dnd_attack_roll called with modifier={modifier}, advantage={advantage}")
    try:
        mod = int(modifier.strip()) if modifier.strip() else 0
        adv = advantage.strip().lower()
        roll1 = random.randint(1, 20)
        roll2 = random.randint(1, 20)

        if adv in ("advantage", "adv", "a"):
            chosen = max(roll1, roll2)
            adv_label = f" (Advantage: rolled {roll1} & {roll2})"
        elif adv in ("disadvantage", "dis", "d"):
            chosen = min(roll1, roll2)
            adv_label = f" (Disadvantage: rolled {roll1} & {roll2})"
        else:
            chosen = roll1
            adv_label = ""

        total = chosen + mod
        crit = " 💥 CRITICAL HIT!" if chosen == 20 else ""
        fumble = " 💀 CRITICAL FAIL!" if chosen == 1 else ""
        mod_str = f"{'+' if mod >= 0 else ''}{mod}" if mod != 0 else ""

        return f"""🎯 Attack Roll{adv_label}:
d20: {chosen}{mod_str} = **{total}**{crit}{fumble}"""
    except ValueError:
        return f"❌ Error: Invalid modifier: {modifier}"
    except Exception as e:
        logger.error(f"Error in dnd_attack_roll: {e}")
        return f"❌ Error: {str(e)}"


@mcp.tool()
async def dnd_damage_roll(dice: str = "1d6", modifier: str = "0") -> str:
    """Roll D&D damage dice with an optional flat modifier (e.g. 2d6, modifier 3)."""
    logger.info(f"dnd_damage_roll called with dice={dice}, modifier={modifier}")
    try:
        count, sides = parse_dice_notation(dice if dice.strip() else "1d6")
        mod = int(modifier.strip()) if modifier.strip() else 0
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls) + mod
        roll_str = ", ".join(str(r) for r in rolls)
        mod_str = f" {'+' if mod >= 0 else ''}{mod}" if mod != 0 else ""
        return f"""⚔️ Damage Roll ({count}d{sides}{mod_str}):
Rolls: [{roll_str}]{mod_str}
Total Damage: {total}"""
    except ValueError as e:
        return f"❌ Error: {str(e)}"
    except Exception as e:
        logger.error(f"Error in dnd_damage_roll: {e}")
        return f"❌ Error: {str(e)}"


@mcp.tool()
async def dnd_saving_throw(modifier: str = "0", dc: str = "15") -> str:
    """Roll a D&D saving throw against a difficulty class (DC)."""
    logger.info(f"dnd_saving_throw called with modifier={modifier}, dc={dc}")
    try:
        mod = int(modifier.strip()) if modifier.strip() else 0
        difficulty = int(dc.strip()) if dc.strip() else 15
        roll = random.randint(1, 20)
        total = roll + mod
        mod_str = f"{'+' if mod >= 0 else ''}{mod}" if mod != 0 else ""
        passed = total >= difficulty
        result_label = "✅ PASSED!" if passed else "❌ FAILED!"
        return f"""🛡️ Saving Throw (DC {difficulty}):
d20: {roll}{mod_str} = {total}
{result_label}"""
    except ValueError:
        return f"❌ Error: Invalid modifier or DC value."
    except Exception as e:
        logger.error(f"Error in dnd_saving_throw: {e}")
        return f"❌ Error: {str(e)}"


@mcp.tool()
async def roll_with_advantage(notation: str = "1d20") -> str:
    """Roll any dice twice and return the higher result (advantage mechanic)."""
    logger.info(f"roll_with_advantage called with notation={notation}")
    try:
        count, sides = parse_dice_notation(notation if notation.strip() else "1d20")
        rolls1 = [random.randint(1, sides) for _ in range(count)]
        rolls2 = [random.randint(1, sides) for _ in range(count)]
        total1, total2 = sum(rolls1), sum(rolls2)
        chosen = max(total1, total2)
        return f"""🟢 Roll with Advantage ({notation}):
Roll 1: [{', '.join(str(r) for r in rolls1)}] = {total1}
Roll 2: [{', '.join(str(r) for r in rolls2)}] = {total2}
✅ Result: {chosen}"""
    except ValueError as e:
        return f"❌ Error: {str(e)}"
    except Exception as e:
        logger.error(f"Error in roll_with_advantage: {e}")
        return f"❌ Error: {str(e)}"


@mcp.tool()
async def roll_with_disadvantage(notation: str = "1d20") -> str:
    """Roll any dice twice and return the lower result (disadvantage mechanic)."""
    logger.info(f"roll_with_disadvantage called with notation={notation}")
    try:
        count, sides = parse_dice_notation(notation if notation.strip() else "1d20")
        rolls1 = [random.randint(1, sides) for _ in range(count)]
        rolls2 = [random.randint(1, sides) for _ in range(count)]
        total1, total2 = sum(rolls1), sum(rolls2)
        chosen = min(total1, total2)
        return f"""🔴 Roll with Disadvantage ({notation}):
Roll 1: [{', '.join(str(r) for r in rolls1)}] = {total1}
Roll 2: [{', '.join(str(r) for r in rolls2)}] = {total2}
⚠️ Result: {chosen}"""
    except ValueError as e:
        return f"❌ Error: {str(e)}"
    except Exception as e:
        logger.error(f"Error in roll_with_disadvantage: {e}")
        return f"❌ Error: {str(e)}"


@mcp.tool()
async def roll_initiative(dex_modifier: str = "0") -> str:
    """Roll D&D initiative (d20 + DEX modifier)."""
    logger.info(f"roll_initiative called with dex_modifier={dex_modifier}")
    try:
        mod = int(dex_modifier.strip()) if dex_modifier.strip() else 0
        roll = random.randint(1, 20)
        total = roll + mod
        mod_str = f"{'+' if mod >= 0 else ''}{mod}" if mod != 0 else ""
        return f"⚡ Initiative Roll: d20({roll}){mod_str} = **{total}**"
    except ValueError:
        return f"❌ Error: Invalid DEX modifier: {dex_modifier}"
    except Exception as e:
        logger.error(f"Error in roll_initiative: {e}")
        return f"❌ Error: {str(e)}"


@mcp.tool()
async def random_number(min_val: str = "1", max_val: str = "100") -> str:
    """Generate a random number between min and max (inclusive)."""
    logger.info(f"random_number called with min={min_val}, max={max_val}")
    try:
        lo = int(min_val.strip()) if min_val.strip() else 1
        hi = int(max_val.strip()) if max_val.strip() else 100
        if lo > hi:
            return f"❌ Error: min ({lo}) must be less than or equal to max ({hi})."
        result = random.randint(lo, hi)
        return f"🎲 Random number between {lo} and {hi}: **{result}**"
    except ValueError:
        return f"❌ Error: Invalid min/max values."
    except Exception as e:
        logger.error(f"Error in random_number: {e}")
        return f"❌ Error: {str(e)}"


# === SERVER STARTUP ===
if __name__ == "__main__":
    logger.info("Starting Dice Roller MCP server...")
    try:
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)