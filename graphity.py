"""Graphity v2 — Analyse structurelle pour éditions ciblées.

Usage: python graphity.py [fichier] [--method METHODE]

Affiche:
- Structure complète (classes, méthodes, lignes)
- Taille de chaque méthode (lignes)
- Dépendances (quelles méthodes appellent quoi)
- Legacy wrappers à migrer
- Dernière modification

Options:
  --method NAME    Détail d'une méthode spécifique (affiche son code)
  --legacy         Liste toutes les lignes avec des wrappers legacy
"""

import sys, re, os
from pathlib import Path
from datetime import datetime
from collections import defaultdict


def analyze(filepath, show_method=None, show_legacy=False):
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()

    total = len(lines)
    mtime = datetime.fromtimestamp(os.path.getmtime(filepath))

    # Parse structure
    classes = []
    methods = []
    current_class = None
    current_method = None
    method_lines = {}
    method_calls = defaultdict(set)  # who calls what
    legacy_spots = []
    raw_flet_spots = []

    for i, line in enumerate(lines, 1):
        # Class
        m = re.match(r'^\s*class\s+(\w+)', line)
        if m:
            current_class = m.group(1)
            cls = {"name": current_class, "line": i, "methods": []}
            classes.append(cls)

        # Method
        m = re.match(r'^\s+def\s+(\w+)\(', line)
        if m and current_class:
            current_method = m.group(1)
            method_lines[current_method] = [i, i]  # start, end
            methods.append({"class": current_class, "name": current_method, "line": i})
            if classes:
                classes[-1]["methods"].append({"name": current_method, "line": i})

        # Track method end
        if current_method:
            method_lines[current_method][1] = i
            if line.strip() == '' or (line.strip() and not line.startswith((' ', '\t'))):
                # Check if blank line is followed by non-indented code
                pass

        # Legacy wrappers
        for pattern in ['safe_handler(', 'textfield(label=', 'headline(', 'body(',
                        'section_header(', 'button(variant=', 'card(title=', 'kpi_card(',
                        'spacer(ds.space_, ds.space_']:
            if pattern in line and not line.strip().startswith('#'):
                legacy_spots.append((i, line.strip()[:80]))
                break

        # Raw Flet
        for pattern in ['ft.TextField(', 'ft.FilledButton(', 'ft.TextButton(',
                        'ft.Dropdown(', 'ft.Container(', 'ft.AlertDialog(',
                        'ft.IconButton(']:
            if pattern in line:
                raw_flet_spots.append(i)

        # Method calls (self.X() or internal function calls)
        m = re.search(r'self\.(\w+)\(', line)
        if m and current_method:
            method_calls[current_method].add(m.group(1))

    # Print report
    rel = Path(filepath).name
    print(f"  {rel}  |  {total} lignes  |  {len(classes)} classes  |  {len(methods)} méthodes  |  modifié {mtime.strftime('%H:%M')}")
    print(f"  Legacy: {len(legacy_spots)}  |  Raw Flet: {len(raw_flet_spots)}")
    print()

    for cls in classes:
        nmethods = len(cls["methods"])
        cls_lines = sum(method_lines[m["name"]][1] - method_lines[m["name"]][0]
                       for m in cls["methods"])
        print(f"  class {cls['name']}  L{cls['line']}  ({nmethods} méthodes)")
        for m in cls["methods"]:
            lstart, lend = method_lines[m["name"]]
            size = lend - lstart
            calls = method_calls.get(m["name"], set())
            call_str = f" -> {', '.join(sorted(calls)[:5])}" if calls else ""
            print(f"    .{m['name']}()  L{lstart}  [{size}l]{call_str}")
        print()

    if show_legacy:
        print(f"\n--- Legacy wrappers ({len(legacy_spots)}) ---")
        for l, code in legacy_spots:
            print(f"  L{l}: {code}")

    if show_method:
        print(f"\n--- Méthode: {show_method} ---")
        for m in methods:
            if m["name"] == show_method:
                start = m["line"] - 1
                # Find end (next def at same indentation)
                end = start + 1
                while end < total:
                    stripped = lines[end].strip()
                    if stripped.startswith('def ') and not lines[end].startswith((' ', '\t')):
                        break
                    if re.match(r'^\s{2}def\s', lines[end]) or re.match(r'^\s{4}def\s', lines[end]) or re.match(r'^\s{0}def\s', lines[end]):
                        break
                    end += 1
                size = end - start
                print(f"  Lignes {start+1}-{end} ({size} lignes):")
                for j in range(start, min(end, start+40)):
                    print(f"  {j+1:4d}: {lines[j].rstrip()}")
                if end - start > 40:
                    print(f"  ... ({end - start - 40} lignes de plus)")
                break


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?", default=r"apps\admin\__main__.py")
    parser.add_argument("--method", "-m", help="Afficher une méthode spécifique")
    parser.add_argument("--legacy", action="store_true", help="Lister les wrappers legacy")
    args = parser.parse_args()

    analyze(args.file, args.method, args.legacy)
