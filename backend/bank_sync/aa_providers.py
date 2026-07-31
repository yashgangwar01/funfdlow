"""
Setu Account Aggregator (AA) provider configuration.

This file is the single source of truth for supported AA entity handles.
Update this list when new AAs are onboarded to Setu's production environment.

Verified sandbox AA handles (from GET /v2/fips aaWiseSuccessRate on 2026-07-31):
  - onemoney
  - anumati

Production may include additional providers — add them here, not inline in code.
"""

AA_PROVIDERS = [
    {"handle": "onemoney",  "label": "OneMoney"},
    {"handle": "anumati",   "label": "Anumati"},
]

# Derived set for fast validation
VALID_AA_HANDLES = {p["handle"] for p in AA_PROVIDERS}
