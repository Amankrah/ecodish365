"""Offline ETL utilities for the §3.5 LCA matcher.

Modules here build deterministic JSON artefacts under
`environmental_impact_model/data/` from official ADEME workbooks. They are
NOT loaded at runtime by the matcher or the API — only the JSON outputs are.
This keeps the production install footprint small (no openpyxl in the
runtime call path) and the artefacts version-pinnable.
"""
