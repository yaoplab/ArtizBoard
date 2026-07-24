"""Remove duplicate _catalogue_content (lines 690-1065, dead code)."""
import re

path = r"C:\projet\apps\admin\__main__.py"
with open(path, encoding="utf-8") as f:
    lines = f.readlines()

# Find both def _catalogue_content
first_start = None
second_start = None
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped == "def _catalogue_content(self):":
        if first_start is None:
            first_start = i
        else:
            second_start = i
            break

if first_start is None or second_start is None:
    print("Could not find two _catalogue_content methods")
    exit(1)

print(f"First: line {first_start+1}")
print(f"Second: line {second_start+1}")

# Remove lines from first_start to second_start-1
del lines[first_start:second_start]

with open(path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print(f"Removed lines {first_start+1}-{second_start}. New file: {len(lines)} lines")

# Verify compilation
import py_compile
py_compile.compile(path, doraise=True)
print("Compilation OK")
