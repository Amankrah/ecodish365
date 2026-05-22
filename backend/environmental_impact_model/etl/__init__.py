"""Offline ETL utilities for the §3.5 LCA matcher.

Modules here build deterministic JSON artefacts under
`environmental_impact_model/data/` from official ADEME workbooks. They are
NOT loaded at runtime by the matcher or the API — only the JSON outputs are.
Offline literature copies (PDF/DOCX), if present, are documented in
`environmental_impact_model/data/README.md` and are not consumed at runtime.
This keeps the production install footprint small (no openpyxl in the
runtime call path) and the artefacts version-pinnable.
"""
