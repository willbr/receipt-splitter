# Start the receipt splitter server at http://127.0.0.1:5001
# Dependencies are declared inline in server.py (PEP 723); uv handles them.
Set-Location $PSScriptRoot
uv run server.py @args
