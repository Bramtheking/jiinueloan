"""
conftest.py — pytest configuration.

The calculation engine tests (test_interest, test_fees, test_repayment,
test_validation) are pure Python and do NOT need a database connection.

If you add DB integration tests later, configure a test DATABASE_URL here.
"""

import os


if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "postgresql://postgres:password@localhost:5432/jiinue_loans"
