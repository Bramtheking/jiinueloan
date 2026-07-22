"""
Add: loan_guarantors, member_deposits, ledger_accounts, assets tables.
Safe to run multiple times (uses IF NOT EXISTS / ON CONFLICT).

BEFORE running this, execute these 3 lines in phpPgAdmin SQL tab as superuser:
  ALTER TABLE loan_products ADD COLUMN IF NOT EXISTS allocation_order VARCHAR(100) DEFAULT 'penalty,interest,principal';
  ALTER TABLE loan_product_fees ADD COLUMN IF NOT EXISTS fee_basis VARCHAR(50) DEFAULT 'principal';
  ALTER TABLE ledger_accounts ADD COLUMN IF NOT EXISTS account_type VARCHAR(50);
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from app.config import settings
from sqlalchemy import create_engine, text

engine = create_engine(settings.database_url)
db_user = "wykqfeio_wykqfeio"

# ── Step 1: Create new tables ─────────────────────────────────────────────────
with engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ledger_accounts (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            account_type VARCHAR(50),
            description VARCHAR(500),
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ledger_accounts_id ON ledger_accounts(id)"))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS loan_guarantors (
            id SERIAL PRIMARY KEY,
            loan_id INTEGER NOT NULL REFERENCES loans(id) ON DELETE CASCADE,
            member_id INTEGER NOT NULL REFERENCES members(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_loan_guarantors_id ON loan_guarantors(id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_loan_guarantors_loan_id ON loan_guarantors(loan_id)"))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS member_deposits (
            id SERIAL PRIMARY KEY,
            member_id INTEGER NOT NULL REFERENCES members(id),
            amount NUMERIC(15,2) NOT NULL,
            deposit_date DATE NOT NULL,
            description TEXT,
            is_locked INTEGER NOT NULL DEFAULT 0,
            related_loan_id INTEGER REFERENCES loans(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_member_deposits_id ON member_deposits(id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_member_deposits_member_id ON member_deposits(member_id)"))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS assets (
            id SERIAL PRIMARY KEY,
            member_id INTEGER NOT NULL REFERENCES members(id),
            asset_name VARCHAR(255) NOT NULL,
            asset_type VARCHAR(100) NOT NULL,
            description TEXT,
            estimated_value NUMERIC(15,2) NOT NULL,
            valuation_date DATE NOT NULL,
            reference_number VARCHAR(255),
            is_pledged BOOLEAN NOT NULL DEFAULT FALSE,
            pledged_loan_id INTEGER REFERENCES loans(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_assets_id ON assets(id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_assets_member_id ON assets(member_id)"))

    conn.commit()
    print("✓ Tables created/verified")

# ── Step 2: Seed ledger accounts ──────────────────────────────────────────────
with engine.connect() as conn:
    defaults = [
        ("Jiinue Loan Account", "loan_disbursement", "Main loan disbursement and repayment account"),
        ("Member Deposit General Account", "member_deposit", "Member deposits and security holdings"),
        ("Interest Income Account", "interest_income", "Interest income from loans"),
        ("Fee Income Account", "fee_income", "Fee income from loan processing"),
        ("Penalty Income Account", "penalty_income", "Late payment and other penalty income"),
        ("Savings Account", "savings", "Member savings"),
    ]
    for name, atype, desc in defaults:
        conn.execute(text(
            "INSERT INTO ledger_accounts (name, account_type, description) VALUES (:n, :t, :d) ON CONFLICT (name) DO NOTHING"
        ), {"n": name, "t": atype, "d": desc})

    try:
        existing = conn.execute(text("SELECT DISTINCT account_name FROM ledger_transactions")).fetchall()
        for (name,) in existing:
            conn.execute(text(
                "INSERT INTO ledger_accounts (name) VALUES (:n) ON CONFLICT (name) DO NOTHING"
            ), {"n": name})
    except Exception:
        pass

    conn.commit()
    print("✓ Ledger accounts seeded")

# ── Step 3: Grants (server only, skip locally) ────────────────────────────────
with engine.connect() as conn:
    try:
        for table in ["ledger_accounts", "loan_guarantors", "member_deposits", "assets"]:
            conn.execute(text(f'GRANT ALL PRIVILEGES ON TABLE {table} TO "{db_user}"'))
        for seq in ["ledger_accounts_id_seq", "loan_guarantors_id_seq", "member_deposits_id_seq", "assets_id_seq"]:
            conn.execute(text(f'GRANT USAGE, SELECT, UPDATE ON SEQUENCE {seq} TO "{db_user}"'))
        conn.commit()
        print("✓ Permissions granted")
    except Exception:
        conn.rollback()
        print("⚠ Grants skipped (running locally)")

# ── Step 4: Verify ────────────────────────────────────────────────────────────
with engine.connect() as conn:
    for t in ["ledger_accounts", "loan_guarantors", "member_deposits", "assets"]:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
        print(f"  {t}: {count} rows")

print("\nMigration complete.")
