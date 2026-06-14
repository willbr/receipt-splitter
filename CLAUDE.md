# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running

The app itself is a single static file: open `index.html` directly in a browser (or via any static file server) and reload to see changes. No build step.

An optional Flask server (`server.py`) adds server-side saving. It serves `index.html` at `/` and accepts `POST /api/save` (`{name, date, tsv}`), writing the TSV to `data/<date>_<name>.tsv`. The static app works fully without it — server saving is a progressive enhancement. Dependencies are declared inline (PEP 723), so run it with uv — no venv to manage:

```
uv run server.py    # http://127.0.0.1:5001  (5000 is taken by macOS AirPlay)
```

When the page is served over http (i.e. via this server), the app **autosaves** to the server on every change (debounced); opened as a `file://` it just skips that silently. Saved `.tsv` files under `data/` are gitignored.

## Architecture

The entire app is in `index.html` — HTML, CSS, and vanilla JS in one file. There are intentionally no dependencies and no module system.

Key things to know before editing:

- **Single source of truth: `store`.** `store = { activeId, receipts: { [id]: Receipt }, nextReceiptId }`. Each `Receipt` has `{ id, name, date, people: [{id, name}], items: [{id, label, qty, price, discount, assigned: [personId], isTotal}] }`. `discount` is an optional per-line amount (number or null) subtracted from `price`; `netPrice(it)` returns the effective price (`price - (discount||0)`, or null when unpriced) and is what `computeSplit()` splits on. `active()` returns the currently selected receipt; almost all mutations go through it.
- **Persistence is automatic.** Every state-changing action calls `save()` which writes the whole `store` to `localStorage` under `STORAGE_KEY` (`receipt-splitter-store-v2`). On boot, `load()` rehydrates it; if storage is empty or the schema doesn't match, an example receipt is seeded. Bumping the schema means changing the key (the v1 → v2 jump is why old data is silently ignored).
- **Render is full-redraw.** There's no diffing — `render()` rebuilds the items table, people list, summary, per-person cards, and header from scratch on every change. Keep this in mind when adding features: read from `active()`, push the change, call `render(); save();`.
- **`computeSplit()` is the single calculator.** It returns `{ owe, itemsByPerson, assignedTotal, unassignedTotal, unassignedItems, unpricedCount, declaredTotal }`. Both the summary and per-person renderers consume the same result — don't recompute.
- **Special rows.** An item is `isTotal` when its label matches `/^total\b/i`; such rows are excluded from the split and used to flag mismatches against the computed sum. Items with `price == null` are highlighted and excluded.
- **Theming.** All colors are CSS variables under `:root`, with a `@media (prefers-color-scheme: dark)` override. Never hardcode colors in new styles — add to the variable set if you need a new shade.
- **Defaults.** New receipts seed people from `DEFAULT_PEOPLE` (`['Will', 'Tim', 'Amy']`).

## TSV format

Tab-separated, columns are `[lineNo, label, qty, price, discount, assigned]`. The parser anchors on the **label** (the first non-numeric cell) rather than fixed positions, so a leading line-number column is optional and a line number merged into the name cell (`2 Tesco Apples`) is tolerated — pure-number cells before the label are dropped, cells after it are `qty, price, discount` in order, and a merged `<n> ` prefix is stripped from the label. Column 6 (assigned names) is exported for humans but ignored on import. It skips a header row containing `Item` plus `Price`/`Qty`/`Quantity`.

A leading `# name<tab>date` comment line carries the receipt name/date: `toTSV()` writes it, `parseTSVMeta()` reads it, and the LLM import prompt asks for it. **Importing:** `loadTSVAsNew()` (the primary "Load as new receipt" button) creates a fresh receipt named from that metadata line; `replaceCurrentWithTSV()` ("Replace current items") overwrites the active receipt's items, confirm-guarded when it's non-empty. Both go through `parseTSVOrWarn()` for the shared parse-error alerts. See `examples/2026-04-17_pub.tsv`. Export filename convention is `<date>_<name>.tsv`.
