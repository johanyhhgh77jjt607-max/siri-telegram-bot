"""
════════════════════
⥑   🔧 دوال مساعد٩                     ║
╚═══════════════════════════════════════╝"""
import re
from typing import Optional, List, Tuple


def extract_code_blocks(text: str) -> List[str]:
    patterns = [
        r"```python\n(.*?)```",
        r"```python\s*\n(.*?)```",
        r"```py\s*\n(.*?)```",
        r"```\s*\n(.*?)```",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return matches
    return [text] if text else []


def extract_code(text: str) -> str:
    blocks = extract_code_blocks(text)
    if not blocks:
        return text
    blocks.sort(key=len, reverse=True)
    return blocks[0].strip()


def extract_after_command(text: str, command: str, bot_name: str = "Yeahsowubot") -> Optional[str]:
    pattern = rf"{re.escape(command)}(?:@{re.escape(bot_name)})?\s*(.*)"
    match = re.match(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        remaining = match.group(1).strip()
        return remaining if remaining else None
    return None


def extract_code_from_message(message) -> Optional[str]:
    text = message.text or ""
    caption = message.caption or ""
    for source in [text, caption]:
        match = re.search(r"```(?:python|py)?\s*\n?(.*?)```", source, re.DOTALL)
        if match:
            return match.group(1).strip()
        for cmd in ["analyze", "fix", "explain", "optimize"]:
            remaining = extract_after_command(source, cmd)
            if remaining and not remaining.startswith("/"):
                return remaining
    return None


def extract_code_and_error(message) -> tuple:
    text = message.text or ""
    code = extract_code_from_message(message)
    error = None
    error_patterns = [
        r"(?:Error|خطأ|Exception|Traceback)[:\s]*(.*?)(?:\|$k)",
        r"(\w+Error:.*?)(?:\n|$)",
    ]
    for pattern in error_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            error = match.group(0).strip()
            break
    if not code and not text.startswith("/fix"):
        code = text
    return code, error


async def send_long_message(update, status_msg, text: str):
    max_len = 4000
    try:
        await status_msg.delete()
    except Exception:
        pass
    if len(text) <= max_len:
        try:
            await update.message.reply_text(text, parse_mode="Markdown")
        except Exception:
            await update.message.reply_text(text)
        return
    parts, current, in_code_block = [], "", False
    for line in text.split("\n"):
        if line.startswith("```"):
            in_code_block = not in_code_block
        if len(current) + len(line) + 1 > max_len:
            if in_code_block:
                current += "```"
                parts.append(current)
                current = "```python\n" + line + "\n"
            else:
                parts.append(current)
                current = line + "\n"
        else:
            current += line + "\n"
    if current:
        parts.append(current)
    for i, part in enumerate(parts):
        prefix = f"🄄 **جزء {i+1}/{len(parts)}**\n\n" if len(parts) > 1 else ""
        try:
            await update.message.reply_text(prefix + part, parse_mode="Markdown")
        except Exception:
            await update.message.reply_text(prefix + part)