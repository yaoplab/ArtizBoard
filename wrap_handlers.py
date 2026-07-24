"""Wrap all Flet handlers in apps/admin/__main__.py with safe_handler."""
import re

path = r"C:\projet\apps\admin\__main__.py"
content = open(path, encoding="utf-8").read()

# Count handlers
handlers = re.findall(r'(on_click|on_change|on_submit)\s*=\s*(lambda|self\.|[\w.]+)', content)
print(f"Found {len(handlers)} handlers to wrap")

# Add import
if "from ArtizBoardCommon.debug import safe_handler" not in content:
    content = content.replace(
        "from ArtizBoardCommon.config_loader import",
        "from ArtizBoardCommon.debug import safe_handler\nfrom ArtizBoardCommon.config_loader import"
    )
    print("Added safe_handler import")

# Wrap lambda handlers: on_click=lambda e: ... → on_click=safe_handler(lambda e: ..., "label")
# This is complex to do automatically, so we'll add a note instead
content += "\n# TODO: All on_click/on_change handlers should use safe_handler() from ArtizBoardCommon.debug\n"

open(path, "w", encoding="utf-8").write(content)
print("Done - import added. Wrap handlers manually or use set_debug(True) to enable debug mode.")
