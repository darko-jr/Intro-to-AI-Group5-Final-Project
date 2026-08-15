#!/usr/bin/env python3
"""
Consolidate top-level imports in a Jupyter notebook into a single import cell.

Usage:
    python scripts/consolidate_imports.py path/to/notebook.ipynb

This script:
 - Backs up the original notebook to notebook.ipynb.bak
 - Collects top-level "import ..." and "from ... import ..." lines (only lines starting at column 0)
 - Collects "from __future__ import ..." lines and keeps them at the top of the new import cell
 - Removes those lines from other code cells
 - Inserts a new code cell with the combined imports before the first existing code cell
 - Leaves indented imports (inside functions/blocks) and magic lines (starting with '%') alone

Note: run this in the repo checkout (so paths resolve). Review the .bak file if something goes wrong.
"""
import nbformat
import re
import sys
import os
from nbformat.v4 import new_code_cell

IMPORT_RE = re.compile(r'^(?:import\s+.+|from\s+[A-Za-z0-9_.]+\s+import\s+.+)$')
FUTURE_RE = re.compile(r'^from\s+__future__\s+import\s+.+$')


def consolidate_notebook(path, in_place=True):
    nb = nbformat.read(path, as_version=nbformat.NO_CONVERT)
    backup_path = path + '.bak'
    # create backup
    if not os.path.exists(backup_path):
        nbformat.write(nb, backup_path)
        print(f"Backup written to {backup_path}")

    future_imports = []
    imports_set = []
    imports_seen = set()

    for cell in nb.cells:
        if cell.get('cell_type') != 'code' or not isinstance(cell.get('source', ''), str):
            continue
        lines = cell['source'].splitlines()
        new_lines = []
        for line in lines:
            stripped = line.rstrip()
            # Keep blank lines and magic/! commands
            if not stripped:
                new_lines.append(line)
                continue
            if stripped.startswith('%') or stripped.startswith('!'):
                new_lines.append(line)
                continue
            # Only consider imports that start at column 0 (no indentation)
            if line.startswith(' ') or line.startswith('\t'):
                new_lines.append(line)
                continue
            if FUTURE_RE.match(stripped):
                if stripped not in future_imports:
                    future_imports.append(stripped)
                # remove from cell
                continue
            if IMPORT_RE.match(stripped):
                if stripped not in imports_seen:
                    imports_seen.add(stripped)
                    imports_set.append(stripped)
                # remove from cell
                continue
            new_lines.append(line)
        cell['source'] = '\n'.join(new_lines)

    if not future_imports and not imports_set:
        print("No top-level imports found to consolidate.")
        return False

    import_cell_lines = []
    import_cell_lines.extend(future_imports)
    if future_imports:
        import_cell_lines.append('')
    import_cell_lines.extend(imports_set)
    import_cell_source = '\n'.join(import_cell_lines)

    # Insert before first code cell
    insert_idx = 0
    for i, cell in enumerate(nb.cells):
        if cell.get('cell_type') == 'code':
            insert_idx = i
            break
        insert_idx = i + 1

    nb.cells.insert(insert_idx, new_code_cell(import_cell_source))

    nbformat.write(nb, path)
    print(f"Consolidated imports written to {path} (original backed up at {backup_path}).")
    return True


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python scripts/consolidate_imports.py path/to/notebook.ipynb")
        sys.exit(2)
    path = sys.argv[1]
    if not os.path.exists(path):
        print(f"Notebook not found: {path}")
        sys.exit(1)
    ok = consolidate_notebook(path)
    sys.exit(0 if ok else 1)
