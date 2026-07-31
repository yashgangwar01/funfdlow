/**
 * AA Provider configuration for the frontend dropdown.
 *
 * These are populated from the backend's GET /api/v1/bank-sync/aa-providers/ endpoint.
 * This file contains the static fallback list in case the API call fails.
 * Update aa_providers.py on the backend — do NOT maintain this list separately.
 *
 * Confirmed valid Setu sandbox handles (2026-07-31):
 *   onemoney, anumati
 */
export const AA_PROVIDERS = [
  { handle: 'onemoney', label: 'OneMoney' },
  { handle: 'anumati',  label: 'Anumati'  },
];
