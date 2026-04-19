# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running

There is no build system, package manager, or test suite. The app is a single static file. To work on it, open `index.html` directly in a browser (or via any static file server). Reload to see changes.

## Architecture

The entire app is in `index.html` — HTML, CSS, and vanilla JS in one file. There are intentionally no dependencies and no module system.

Key things to know before editing:

- **Single source of truth: `store`.** `store = { activeId, receipts: { [id]: Receipt }, nextReceiptId }`. Each `Receipt` has `{ id, name, date, people: [{id, name}], items: [{id, label, qty, price, assigned: [personId], isTotal}] }`. `active()` returns the currently selected receipt; almost all mutations go through it.
- **Persistence is automatic.** Every state-changing action calls `save()` which writes the whole `store` to `localStorage` under `STORAGE_KEY` (`receipt-splitter-store-v2`). On boot, `load()` rehydrates it; if storage is empty or the schema doesn't match, an example receipt is seeded. Bumping the schema means changing the key (the v1 → v2 jump is why old data is silently ignored).
- **Render is full-redraw.** There's no diffing — `render()` rebuilds the items table, people list, summary, per-person cards, and header from scratch on every change. Keep this in mind when adding features: read from `active()`, push the change, call `render(); save();`.
- **`computeSplit()` is the single calculator.** It returns `{ owe, itemsByPerson, assignedTotal, unassignedTotal, unassignedItems, unpricedCount, declaredTotal }`. Both the summary and per-person renderers consume the same result — don't recompute.
- **Special rows.** An item is `isTotal` when its label matches `/^total\b/i`; such rows are excluded from the split and used to flag mismatches against the computed sum. Items with `price == null` are highlighted and excluded.
- **Theming.** All colors are CSS variables under `:root`, with a `@media (prefers-color-scheme: dark)` override. Never hardcode colors in new styles — add to the variable set if you need a new shade.
- **Defaults.** New receipts seed people from `DEFAULT_PEOPLE` (`['Will', 'Tim', 'Amy']`).

## TSV format

Tab-separated, columns are `[lineNo, label, qty, price]`. The parser is tolerant of 2- to 4-column rows and skips a header row containing `Item` plus `Price`/`Qty`/`Quantity`. See `examples/2026-04-17_pub.tsv`. Export filename convention is `<date>_<name>.tsv`.
