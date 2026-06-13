#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["flask>=3.0"]
# ///
"""Minimal Flask server for Receipt Splitter.

Serves the static app and saves receipts as TSV files under ``data/``.

    uv run server.py

Then open http://127.0.0.1:5001 — the app autosaves here on every change.
(Port 5001 because macOS Control Center / AirPlay Receiver occupies 5000.)
"""
import os
import re

from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

app = Flask(__name__, static_folder=None)


def safe_name(name):
    """Slugify a receipt name to match the front-end download convention."""
    slug = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")
    return slug or "untitled"


def safe_date(date):
    """Keep an ISO date as-is, otherwise fall back to 'undated'."""
    return date if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date or "") else "undated"


@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/api/save", methods=["POST"])
def save():
    data = request.get_json(silent=True) or {}
    tsv = data.get("tsv")
    if not isinstance(tsv, str) or not tsv.strip():
        return jsonify(ok=False, error="No TSV content provided."), 400

    filename = f"{safe_date(data.get('date'))}_{safe_name(data.get('name'))}.tsv"
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, filename)

    # Defence in depth: the sanitised name should already be safe, but make sure
    # a crafted value can never write outside data/.
    if os.path.dirname(os.path.abspath(path)) != DATA_DIR:
        return jsonify(ok=False, error="Invalid filename."), 400

    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(tsv if tsv.endswith("\n") else tsv + "\n")

    return jsonify(ok=True, file=filename)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
