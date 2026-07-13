"""
conftest.py — pytest configuration.

The calculation engine tests (test_interest, test_fees, test_repayment,
test_validation) are pure Python and do NOT need a database connection.

If you add DB integration tests later, configure a test DATABASE_URL here.
"""

import os

# Ensure tests that import app.config don't fail if .env doesn't exist yet.
# We provide a dummy DATABASE_URL only if none is set.
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test_jiinue"
