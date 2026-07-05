"""AI data-ingestion layer for CLIMATRIX.

Turns "the client reshapes their data to fit the app" into "the app fits the
client's data": accept any input, understand it, map it to the canonical schema
GROUNDED in the real emission-factor catalog (never hallucinated), ask targeted
clarifying questions, score confidence, and commit only human-reviewed rows.

This package is being built incrementally per Ana's master design. First piece:
the factor catalog retrieval index (catalog.py) — the anti-hallucination core.
"""
