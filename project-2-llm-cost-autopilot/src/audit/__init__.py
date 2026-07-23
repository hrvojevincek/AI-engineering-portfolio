"""Audit package: DB access, request logging, cost stats.

Layout:
  paths.py  — DB / migrations paths
  db.py     — connect, get_conn, migrations
  store.py  — log_request, fetch_*
  stats.py  — compute_savings (vs always gpt-4o)
"""
