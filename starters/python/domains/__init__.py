"""domains: independent business-capability packages.

Each subpackage (users, tasks, ...) may depend on core, but never on a
sibling domain. See tools/boundary_check.py and .importlinter for the
enforced rule.
"""
