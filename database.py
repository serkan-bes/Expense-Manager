"""
Database management, schema migration, and financial accounting engine for Expense Manager.

This module enforces P2P synchronization safety (for tools like Syncthing) by storing
the SQLite database inside the `data/` directory and running mandatory journal/sync PRAGMAs
on every connection opening. It also implements non-destructive schema migrations, dynamic
account/card management, statement closing date calculations, and credit card installment logic.
"""

import calendar
import datetime
import os
import shutil
import sqlite3 as sql
import uuid
from typing import Any, Dict, List, Optional, Tuple

# Resolve directory and database file paths relative to this module
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "database.db")
LEGACY_DB_PATH = os.path.join(BASE_DIR, "database.db")

# Account type constants
ACCOUNT_TYPE_CASH_BANK = "Cash / Bank"
ACCOUNT_TYPE_CREDIT_CARD = "Credit Card"

# Transaction type constants
TX_TYPE_EXPENSE = "Expense"
TX_TYPE_INCOME = "Income"
TX_TYPE_TRANSFER = "Transfer"

# Default initial checking/cash accounts seeded when the database is empty
DEFAULT_ACCOUNTS = [
    ("Cash", ACCOUNT_TYPE_CASH_BANK, 0.0, 0.0, None, None),
    ("Bank 1", ACCOUNT_TYPE_CASH_BANK, 0.0, 0.0, None, None),
    ("Bank 2", ACCOUNT_TYPE_CASH_BANK, 0.0, 0.0, None, None),
]


def get_connection(db_path: Optional[str] = None) -> sql.Connection:
    """
    Open and configure a SQLite database connection with P2P synchronization safety.

    To avoid database corruption when syncing across devices with Syncthing (which can
    conflict on multi-file WAL journals like .db-wal and .db-shm), every connection
    explicitly enforces:
      - PRAGMA journal_mode = DELETE; (rollback journal deleted cleanly after each transaction)
      - PRAGMA synchronous = FULL;    (ensures all writes are flushed to disk before commit completes)
    """
    target_path = db_path or DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    conn = sql.connect(target_path)
    conn.row_factory = sql.Row

    # Mandatory PRAGMAs for P2P (Syncthing) synchronization safety
    conn.execute("PRAGMA journal_mode = DELETE;")
    conn.execute("PRAGMA synchronous = FULL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _migrate_legacy_db_file() -> None:
    """
    Safely migrate a legacy root-level `database.db` file into `data/database.db`
    without losing any existing transaction records.
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(LEGACY_DB_PATH):
        return

    # Case 1: Target database in data/ does not exist yet -> move legacy file directly
    if not os.path.exists(DB_PATH):
        try:
            shutil.move(LEGACY_DB_PATH, DB_PATH)
            return
        except OSError:
            shutil.copy2(LEGACY_DB_PATH, DB_PATH)

    # Case 2: Both files exist -> merge any legacy rows from root database.db into data/database.db
    try:
        legacy_conn = sql.connect(LEGACY_DB_PATH)
        legacy_cur = legacy_conn.cursor()
        tables = [
            row[0]
            for row in legacy_cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        ]
        legacy_rows = []
        if "finance" in tables:
            legacy_rows = legacy_cur.execute(
                "SELECT amount, category, description, account, date FROM finance"
            ).fetchall()
        legacy_conn.close()

        if legacy_rows:
            target_conn = get_connection(DB_PATH)
            target_cur = target_conn.cursor()
            target_cur.execute(
                """
                CREATE TABLE IF NOT EXISTS finance (
                    amount REAL,
                    category TEXT,
                    description TEXT,
                    account TEXT,
                    date NUMERIC
                )
                """
            )
            existing_count = target_cur.execute("SELECT COUNT(*) FROM finance").fetchone()[0]
            if existing_count == 0:
                target_cur.executemany(
                    "INSERT INTO finance (amount, category, description, account, date) VALUES (?, ?, ?, ?, ?)",
                    legacy_rows,
                )
                target_conn.commit()
            target_conn.close()

        # Remove the legacy root file after ensuring its data is safely preserved in data/database.db
        os.remove(LEGACY_DB_PATH)
    except Exception as exc:
        print(f"Warning during legacy database file migration: {exc}")


def init_db() -> None:
    """
    Initialize the database schema and perform non-destructive migrations on existing tables.

    Ensures both `accounts` and `finance` tables exist, upgrades older `finance` schemas
    by adding new columns for credit card installments and transfers, normalizes legacy
    account names, and seeds default accounts (`Cash`, `Bank 1`, `Bank 2`) if `accounts` is empty.
    """
    _migrate_legacy_db_file()

    conn = get_connection()
    cursor = conn.cursor()

    # 1. Create the dynamic `accounts` table for Cash/Bank accounts and Credit Cards
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            account_type TEXT NOT NULL,
            initial_balance REAL DEFAULT 0.0,
            credit_limit REAL DEFAULT 0.0,
            closing_day INTEGER DEFAULT NULL,
            due_day INTEGER DEFAULT NULL
        )
        """
    )

    # 2. Create the `finance` transactions table if it does not exist yet
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS finance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT,
            description TEXT,
            account TEXT,
            date TEXT,
            transaction_type TEXT DEFAULT 'Expense',
            to_account TEXT DEFAULT NULL,
            installments INTEGER DEFAULT 1,
            installment_number INTEGER DEFAULT 1,
            installment_group_id TEXT DEFAULT NULL,
            statement_date TEXT DEFAULT NULL
        )
        """
    )

    # 3. Inspect existing columns in `finance` and safely add any missing columns via ALTER TABLE
    existing_finance_cols = {
        row["name"] for row in cursor.execute("PRAGMA table_info(finance)").fetchall()
    }

    required_finance_migrations = [
        ("transaction_type", "TEXT DEFAULT NULL"),
        ("to_account", "TEXT DEFAULT NULL"),
        ("installments", "INTEGER DEFAULT 1"),
        ("installment_number", "INTEGER DEFAULT 1"),
        ("installment_group_id", "TEXT DEFAULT NULL"),
        ("statement_date", "TEXT DEFAULT NULL"),
    ]

    for col_name, col_def in required_finance_migrations:
        if col_name not in existing_finance_cols:
            cursor.execute(f"ALTER TABLE finance ADD COLUMN {col_name} {col_def}")

    # 4. Inspect existing columns in `accounts` and safely add any missing columns
    existing_account_cols = {
        row["name"] for row in cursor.execute("PRAGMA table_info(accounts)").fetchall()
    }
    required_account_migrations = [
        ("account_type", f"TEXT DEFAULT '{ACCOUNT_TYPE_CASH_BANK}'"),
        ("initial_balance", "REAL DEFAULT 0.0"),
        ("credit_limit", "REAL DEFAULT 0.0"),
        ("closing_day", "INTEGER DEFAULT NULL"),
        ("due_day", "INTEGER DEFAULT NULL"),
    ]
    for col_name, col_def in required_account_migrations:
        if col_name not in existing_account_cols:
            cursor.execute(f"ALTER TABLE accounts ADD COLUMN {col_name} {col_def}")

    # 5. Normalize legacy v1.0 records in `finance` without deleting any user data
    # Legacy code saved "Bank1" and "Bank2" without spaces
    cursor.execute("UPDATE finance SET account = 'Bank 1' WHERE account = 'Bank1'")
    cursor.execute("UPDATE finance SET account = 'Bank 2' WHERE account = 'Bank2'")

    # Backfill transaction_type based on sign of amount for legacy rows
    cursor.execute(
        """
        UPDATE finance
        SET transaction_type = CASE
            WHEN amount >= 0 THEN 'Income'
            ELSE 'Expense'
        END
        WHERE transaction_type IS NULL OR TRIM(transaction_type) = ''
        """
    )
    # Any positive amount row that had a default 'Expense' label from migration is an Income
    cursor.execute(
        "UPDATE finance SET transaction_type = 'Income' WHERE amount > 0 AND transaction_type = 'Expense'"
    )
    cursor.execute("UPDATE finance SET installments = 1 WHERE installments IS NULL OR installments < 1")
    cursor.execute(
        "UPDATE finance SET installment_number = 1 WHERE installment_number IS NULL OR installment_number < 1"
    )

    # 6. Seed default accounts (`Cash`, `Bank 1`, `Bank 2`) if the `accounts` table is empty
    account_count = cursor.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
    if account_count == 0:
        cursor.executemany(
            """
            INSERT INTO accounts (name, account_type, initial_balance, credit_limit, closing_day, due_day)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            DEFAULT_ACCOUNTS,
        )

    # Ensure any account referenced in existing legacy `finance` rows also exists in `accounts`
    distinct_legacy_accounts = cursor.execute(
        "SELECT DISTINCT account FROM finance WHERE account IS NOT NULL AND TRIM(account) != '' AND account != 'Not Specified'"
    ).fetchall()
    for row in distinct_legacy_accounts:
        acc_name = row["account"]
        exists = cursor.execute("SELECT 1 FROM accounts WHERE name = ?", (acc_name,)).fetchone()
        if not exists:
            cursor.execute(
                """
                INSERT INTO accounts (name, account_type, initial_balance, credit_limit, closing_day, due_day)
                VALUES (?, ?, 0.0, 0.0, NULL, NULL)
                """,
                (acc_name, ACCOUNT_TYPE_CASH_BANK),
            )

    conn.commit()
    conn.close()


# ==============================================================================
# Date & Credit Card Statement Closing Date Calculation Helpers
# ==============================================================================


def parse_date(date_str: Optional[str]) -> datetime.date:
    """
    Parse a date string in 'dd.MM.yyyy' or 'YYYY-MM-DD' format into a datetime.date object.
    Falls back to today's date if parsing fails.
    """
    if not date_str:
        return datetime.date.today()
    cleaned = str(date_str).strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return datetime.date.today()


def format_date(date_obj: datetime.date) -> str:
    """Format a datetime.date object into the standard UI display format 'dd.MM.yyyy'."""
    return date_obj.strftime("%d.%m.%Y")


def shift_year_month(year: int, month: int, delta_months: int) -> Tuple[int, int]:
    """
    Shift a (year, month) pair forward or backward by `delta_months`.
    Returns the resulting (new_year, new_month) tuple.
    """
    total_months = (year * 12 + (month - 1)) + delta_months
    new_year = total_months // 12
    new_month = (total_months % 12) + 1
    return new_year, new_month


def get_closing_date_for_month(year: int, month: int, closing_day: int) -> datetime.date:
    """
    Compute the exact statement closing date for a given (year, month) and card closing_day (1-31).
    Automatically clamps the day to the maximum number of days in that month (e.g. 28/29 for Feb).
    """
    clamped_closing_day = max(1, min(31, int(closing_day)))
    max_day_in_month = calendar.monthrange(year, month)[1]
    actual_day = min(clamped_closing_day, max_day_in_month)
    return datetime.date(year, month, actual_day)


def add_months(source_date: datetime.date, delta_months: int) -> datetime.date:
    """
    Shift a date forward by `delta_months` months, clamping the day of month
    to the valid range of the target month (e.g., Jan 31 + 1 month -> Feb 28/29).
    """
    target_year, target_month = shift_year_month(source_date.year, source_date.month, delta_months)
    max_day = calendar.monthrange(target_year, target_month)[1]
    return datetime.date(target_year, target_month, min(source_date.day, max_day))


def calculate_statement_closing_date_for_tx(
    tx_date: datetime.date, closing_day: int, month_offset: int = 0
) -> datetime.date:
    """
    Calculate the statement closing date that a transaction (or a specific installment) falls into.

    Logic:
      1. Determine the statement closing date in the transaction's own month (`tx_date.year`, `tx_date.month`).
      2. If `tx_date <= this_month_closing_date`, the first installment belongs to this month's statement cycle.
      3. If `tx_date > this_month_closing_date`, the statement for this month has already closed, so the
         first installment rolls over into next month's statement cycle (+1 month).
      4. For subsequent installments (`month_offset > 0`), shift the base statement month forward by
         `+month_offset` months and clamp `closing_day` to that month's length.
    """
    this_month_closing = get_closing_date_for_month(tx_date.year, tx_date.month, closing_day)
    if tx_date <= this_month_closing:
        base_year, base_month = tx_date.year, tx_date.month
    else:
        base_year, base_month = shift_year_month(tx_date.year, tx_date.month, 1)

    target_year, target_month = shift_year_month(base_year, base_month, month_offset)
    return get_closing_date_for_month(target_year, target_month, closing_day)


def calculate_next_closing_date(
    closing_day: int, reference_date: Optional[datetime.date] = None
) -> datetime.date:
    """
    Determine the upcoming (active) statement closing date for a credit card relative to `reference_date` (today).
    All transactions/installments with `statement_date <= next_closing_date` belong to the
    Current Statement Period; those with `statement_date > next_closing_date` belong to Future Statement Periods.
    """
    ref = reference_date or datetime.date.today()
    return calculate_statement_closing_date_for_tx(ref, closing_day, month_offset=0)


def calculate_next_due_date(
    closing_day: int, due_day: int, reference_date: Optional[datetime.date] = None
) -> datetime.date:
    """
    Calculate the payment due date corresponding to the card's next statement closing date.
    If `due_day >= closing_day`, the due date is in the same month as the statement closing date;
    otherwise, it falls in the following month.
    """
    next_closing = calculate_next_closing_date(closing_day, reference_date)
    if due_day >= closing_day:
        return get_closing_date_for_month(next_closing.year, next_closing.month, due_day)
    due_year, due_month = shift_year_month(next_closing.year, next_closing.month, 1)
    return get_closing_date_for_month(due_year, due_month, due_day)


def calculate_installment_schedule(
    total_amount: float,
    tx_date: datetime.date,
    closing_day: int,
    installments: int = 1,
    reference_date: Optional[datetime.date] = None,
) -> List[Dict[str, Any]]:
    """
    Split a credit card purchase into `installments` monthly installment records and compute
    each installment's effective date, statement closing date, and statement period classification.

    Financial precision guarantee:
      Each of the first (N - 1) installments is rounded to 2 decimal places (`round(total / N, 2)`),
      and the final N-th installment absorbs any 1-cent rounding remainder so that the sum of all
      installments equals `total_amount` strictly to the cent.
    """
    count = max(1, int(installments))
    positive_total = round(abs(float(total_amount)), 2)
    base_installment = round(positive_total / count, 2)
    next_closing = calculate_next_closing_date(closing_day, reference_date)

    schedule: List[Dict[str, Any]] = []
    accumulated = 0.0

    for idx in range(count):
        if idx < count - 1:
            inst_amount = base_installment
            accumulated = round(accumulated + inst_amount, 2)
        else:
            # Final installment absorbs any rounding difference
            inst_amount = round(positive_total - accumulated, 2)

        inst_date = add_months(tx_date, idx)
        stmt_date = calculate_statement_closing_date_for_tx(tx_date, closing_day, month_offset=idx)
        is_current = stmt_date <= next_closing

        schedule.append(
            {
                "installment_number": idx + 1,
                "installments": count,
                "raw_amount": inst_amount,
                "signed_amount": -inst_amount,
                "installment_date": inst_date,
                "installment_date_str": format_date(inst_date),
                "statement_date": stmt_date,
                "statement_date_str": format_date(stmt_date),
                "is_current_period": is_current,
                "period_label": "Current Statement" if is_current else "Future Statement",
            }
        )

    return schedule


# ==============================================================================
# Account & Credit Card CRUD Operations
# ==============================================================================


def get_all_accounts(account_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch all accounts (or filtered by `account_type`: 'Cash / Bank' or 'Credit Card').
    """
    conn = get_connection()
    cursor = conn.cursor()
    if account_type:
        rows = cursor.execute(
            "SELECT * FROM accounts WHERE account_type = ? ORDER BY id ASC",
            (account_type,),
        ).fetchall()
    else:
        rows = cursor.execute("SELECT * FROM accounts ORDER BY id ASC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_account_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single account record by its unique name."""
    conn = get_connection()
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM accounts WHERE name = ?", (name,)).fetchone()
    conn.close()
    return dict(row) if row else None


def add_cash_account(name: str, initial_balance: float = 0.0) -> None:
    """
    Insert a new Checking / Cash account into the `accounts` table.
    Raises ValueError if the name is empty or already exists.
    """
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Account name cannot be empty.")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO accounts (name, account_type, initial_balance, credit_limit, closing_day, due_day)
            VALUES (?, ?, ?, 0.0, NULL, NULL)
            """,
            (clean_name, ACCOUNT_TYPE_CASH_BANK, round(float(initial_balance), 2)),
        )
        conn.commit()
    except sql.IntegrityError as exc:
        raise ValueError(f"An account or card named '{clean_name}' already exists.") from exc
    finally:
        conn.close()


def add_credit_card(name: str, credit_limit: float, closing_day: int, due_day: int) -> None:
    """
    Insert a new Credit Card into the `accounts` table with its total credit limit,
    statement closing day (1-31), and payment due day (1-31).
    """
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Card name cannot be empty.")
    if credit_limit <= 0:
        raise ValueError("Total card limit must be greater than zero.")
    if not (1 <= int(closing_day) <= 31):
        raise ValueError("Statement closing day must be between 1 and 31.")
    if not (1 <= int(due_day) <= 31):
        raise ValueError("Payment due day must be between 1 and 31.")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO accounts (name, account_type, initial_balance, credit_limit, closing_day, due_day)
            VALUES (?, ?, 0.0, ?, ?, ?)
            """,
            (
                clean_name,
                ACCOUNT_TYPE_CREDIT_CARD,
                round(float(credit_limit), 2),
                int(closing_day),
                int(due_day),
            ),
        )
        conn.commit()
    except sql.IntegrityError as exc:
        raise ValueError(f"An account or card named '{clean_name}' already exists.") from exc
    finally:
        conn.close()


def delete_account(name: str) -> None:
    """
    Delete an account or credit card by name.
    Prevents deletion if there are existing transactions linked to the account.
    """
    conn = get_connection()
    cursor = conn.cursor()
    linked_count = cursor.execute(
        "SELECT COUNT(*) FROM finance WHERE account = ? OR to_account = ?",
        (name, name),
    ).fetchone()[0]
    if linked_count > 0:
        conn.close()
        raise ValueError(
            f"Cannot delete '{name}' because it has {linked_count} linked transaction(s)."
        )
    cursor.execute("DELETE FROM accounts WHERE name = ?", (name,))
    conn.commit()
    conn.close()


# ==============================================================================
# Transaction Recording & Installment Generation
# ==============================================================================


def record_transaction(
    transaction_type: str,
    raw_amount: float,
    category: str,
    description: str,
    account_name: str,
    tx_date: datetime.date,
    to_account_name: Optional[str] = None,
    installments: int = 1,
) -> List[Dict[str, Any]]:
    """
    Record an Expense, Income, or Transfer transaction into the `finance` table.

    Accounting Rules Enforced:
      1. Expense on Cash/Bank Account:
         - Inserts a single Expense record (`amount = -abs(raw_amount)`).
         - Deducts directly from that Cash/Bank account's balance.
      2. Expense on Credit Card:
         - Does NOT touch any Cash/Bank account balance.
         - If `installments == 1`, inserts 1 row with the card's calculated `statement_date`.
         - If `installments > 1`, splits `raw_amount` into `N` equal monthly installments,
           shifts each subsequent installment date and statement closing date by +1 month,
           appends `(1/N)`, `(2/N)`, ..., `(N/N)` to the description, and assigns a shared
           `installment_group_id`.
         - The sum of all `N` rows immediately reduces the card's Available Limit by the full
           purchase amount, while only installments with `statement_date <= next_closing_date`
           count toward the Current Statement Debt.
      3. Income:
         - Inserts a positive record (`amount = +abs(raw_amount)`).
      4. Transfer (Credit Card Debt Payment or Inter-Account Transfer):
         - Inserts a Transfer record (`transaction_type = 'Transfer'`, `account = from_account`,
           `to_account = to_account`, `amount = -abs(raw_amount)`).
         - Deducts `raw_amount` from the source Cash/Bank account balance.
         - Reduces the target Credit Card's debt and restores its Available Limit by `raw_amount`.
         - Never counted as a new Expense in income/expense summaries.
    """
    positive_amount = round(abs(float(raw_amount)), 2)
    if positive_amount <= 0:
        raise ValueError("Transaction amount must be greater than zero.")

    clean_desc = (description or "").strip()
    account_info = get_account_by_name(account_name)
    if not account_info:
        raise ValueError(f"Selected account '{account_name}' does not exist.")

    conn = get_connection()
    cursor = conn.cursor()
    created_rows: List[Dict[str, Any]] = []

    try:
        if transaction_type == TX_TYPE_INCOME:
            date_str = format_date(tx_date)
            cursor.execute(
                """
                INSERT INTO finance (
                    amount, category, description, account, date,
                    transaction_type, to_account, installments, installment_number,
                    installment_group_id, statement_date
                ) VALUES (?, ?, ?, ?, ?, ?, NULL, 1, 1, NULL, NULL)
                """,
                (
                    positive_amount,
                    category,
                    clean_desc,
                    account_name,
                    date_str,
                    TX_TYPE_INCOME,
                ),
            )
            created_rows.append(
                {
                    "amount": positive_amount,
                    "description": clean_desc,
                    "date": date_str,
                    "statement_date": None,
                }
            )

        elif transaction_type == TX_TYPE_TRANSFER:
            if not to_account_name:
                raise ValueError("Please select a target account/card for the transfer.")
            if account_name == to_account_name:
                raise ValueError("Source and destination accounts cannot be the same.")
            to_account_info = get_account_by_name(to_account_name)
            if not to_account_info:
                raise ValueError(f"Destination account '{to_account_name}' does not exist.")

            date_str = format_date(tx_date)
            transfer_category = category or "Credit Card Payment"
            transfer_desc = (
                clean_desc
                if clean_desc
                else f"Transfer: {account_name} -> {to_account_name}"
            )
            # Store Transfer with negative amount from source perspective, and to_account set
            cursor.execute(
                """
                INSERT INTO finance (
                    amount, category, description, account, date,
                    transaction_type, to_account, installments, installment_number,
                    installment_group_id, statement_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1, NULL, NULL)
                """,
                (
                    -positive_amount,
                    transfer_category,
                    transfer_desc,
                    account_name,
                    date_str,
                    TX_TYPE_TRANSFER,
                    to_account_name,
                ),
            )
            created_rows.append(
                {
                    "amount": -positive_amount,
                    "description": transfer_desc,
                    "date": date_str,
                    "to_account": to_account_name,
                }
            )

        elif transaction_type == TX_TYPE_EXPENSE:
            is_credit_card = account_info["account_type"] == ACCOUNT_TYPE_CREDIT_CARD

            if is_credit_card:
                closing_day = int(account_info["closing_day"] or 1)
                inst_count = max(1, int(installments))
                group_id = str(uuid.uuid4())[:12] if inst_count > 1 else None
                schedule = calculate_installment_schedule(
                    total_amount=positive_amount,
                    tx_date=tx_date,
                    closing_day=closing_day,
                    installments=inst_count,
                )

                for item in schedule:
                    if inst_count > 1:
                        base_title = clean_desc if clean_desc else category
                        row_desc = f"{base_title} ({item['installment_number']}/{inst_count})"
                    else:
                        row_desc = clean_desc

                    cursor.execute(
                        """
                        INSERT INTO finance (
                            amount, category, description, account, date,
                            transaction_type, to_account, installments, installment_number,
                            installment_group_id, statement_date
                        ) VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?)
                        """,
                        (
                            item["signed_amount"],
                            category,
                            row_desc,
                            account_name,
                            item["installment_date_str"],
                            TX_TYPE_EXPENSE,
                            inst_count,
                            item["installment_number"],
                            group_id,
                            item["statement_date_str"],
                        ),
                    )
                    created_rows.append(
                        {
                            "amount": item["signed_amount"],
                            "description": row_desc,
                            "date": item["installment_date_str"],
                            "statement_date": item["statement_date_str"],
                            "period_label": item["period_label"],
                        }
                    )
            else:
                # Direct Cash / Bank Expense (single payment, immediately reduces cash/bank balance)
                date_str = format_date(tx_date)
                cursor.execute(
                    """
                    INSERT INTO finance (
                        amount, category, description, account, date,
                        transaction_type, to_account, installments, installment_number,
                        installment_group_id, statement_date
                    ) VALUES (?, ?, ?, ?, ?, ?, NULL, 1, 1, NULL, NULL)
                    """,
                    (
                        -positive_amount,
                        category,
                        clean_desc,
                        account_name,
                        date_str,
                        TX_TYPE_EXPENSE,
                    ),
                )
                created_rows.append(
                    {
                        "amount": -positive_amount,
                        "description": clean_desc,
                        "date": date_str,
                        "statement_date": None,
                    }
                )
        else:
            raise ValueError(f"Unsupported transaction type: {transaction_type}")

        conn.commit()
    finally:
        conn.close()

    return created_rows


# ==============================================================================
# Financial Aggregation, Balances, Credit Card Statements & Queries
# ==============================================================================


def get_financial_summary(reference_date: Optional[datetime.date] = None) -> Dict[str, Any]:
    """
    Calculate the complete financial overview for the Dashboard:
      - Individual and Total Liquid Cash/Bank Balances (strictly unaffected by credit card purchases)
      - Per-Credit-Card metrics:
          * Current Statement Debt (only unpaid installments due up to the next statement closing date)
          * Future Statement Debt (installments scheduled for future statement cycles)
          * Total Debt (Current + Future unpaid card debt)
          * Available Limit & Total Limit (Available Limit decreases immediately by the full purchase amount)
          * Next Statement Closing Date & Next Payment Due Date
      - Overall Income and Expense totals (excluding Transfer transactions so debt payments are never double-counted)
    """
    ref_date = reference_date or datetime.date.today()

    conn = get_connection()
    cursor = conn.cursor()
    account_rows = [dict(r) for r in cursor.execute("SELECT rowid AS row_id, * FROM accounts ORDER BY rowid ASC").fetchall()]
    tx_rows = [dict(r) for r in cursor.execute("SELECT rowid AS row_id, * FROM finance ORDER BY rowid ASC").fetchall()]
    conn.close()

    # Separate accounts by type
    cash_accounts_map: Dict[str, Dict[str, Any]] = {}
    credit_cards_map: Dict[str, Dict[str, Any]] = {}

    for acc in account_rows:
        name = acc["name"]
        if acc["account_type"] == ACCOUNT_TYPE_CREDIT_CARD:
            closing_day = int(acc["closing_day"] or 1)
            due_day = int(acc["due_day"] or 1)
            next_closing = calculate_next_closing_date(closing_day, ref_date)
            next_due = calculate_next_due_date(closing_day, due_day, ref_date)
            credit_cards_map[name] = {
                "id": acc["id"],
                "name": name,
                "account_type": ACCOUNT_TYPE_CREDIT_CARD,
                "credit_limit": round(float(acc["credit_limit"] or 0.0), 2),
                "closing_day": closing_day,
                "due_day": due_day,
                "next_closing_date": next_closing,
                "next_closing_date_str": format_date(next_closing),
                "next_due_date": next_due,
                "next_due_date_str": format_date(next_due),
                "raw_total_expenses": 0.0,
                "raw_matured_expenses": 0.0,
                "raw_payments": 0.0,
            }
        else:
            init_bal = round(float(acc["initial_balance"] or 0.0), 2)
            cash_accounts_map[name] = {
                "id": acc["id"],
                "name": name,
                "account_type": ACCOUNT_TYPE_CASH_BANK,
                "initial_balance": init_bal,
                "current_balance": init_bal,
            }

    total_income = 0.0
    total_expense = 0.0
    total_transfers = 0.0

    for tx in tx_rows:
        try:
            raw_val = float(tx["amount"] or 0.0)
        except (TypeError, ValueError):
            raw_val = 0.0
        abs_val = round(abs(raw_val), 2)

        tx_type = tx.get("transaction_type")
        if not tx_type:
            tx_type = TX_TYPE_INCOME if raw_val >= 0 else TX_TYPE_EXPENSE

        acc_name = tx.get("account") or ""
        to_acc_name = tx.get("to_account") or ""

        if tx_type == TX_TYPE_INCOME:
            total_income = round(total_income + abs_val, 2)
            if acc_name in cash_accounts_map:
                cash_accounts_map[acc_name]["current_balance"] = round(
                    cash_accounts_map[acc_name]["current_balance"] + abs_val, 2
                )
            elif acc_name in credit_cards_map:
                # If an income/refund is logged directly onto a credit card, treat it as reducing card debt
                credit_cards_map[acc_name]["raw_payments"] = round(
                    credit_cards_map[acc_name]["raw_payments"] + abs_val, 2
                )

        elif tx_type == TX_TYPE_EXPENSE:
            # All expenses (whether paid by cash/bank or credit card) count toward total expenses
            total_expense = round(total_expense + abs_val, 2)

            if acc_name in cash_accounts_map:
                # Cash/Bank expense directly reduces liquid account balance
                cash_accounts_map[acc_name]["current_balance"] = round(
                    cash_accounts_map[acc_name]["current_balance"] - abs_val, 2
                )
            elif acc_name in credit_cards_map:
                # Credit Card expense does NOT reduce liquid cash/bank balance;
                # it adds to card debt and reduces available credit limit.
                card = credit_cards_map[acc_name]
                card["raw_total_expenses"] = round(card["raw_total_expenses"] + abs_val, 2)

                # Determine which statement closing date this expense/installment belongs to
                stmt_date_str = tx.get("statement_date")
                if stmt_date_str:
                    stmt_date = parse_date(stmt_date_str)
                else:
                    tx_date = parse_date(str(tx.get("date") or ""))
                    stmt_date = calculate_statement_closing_date_for_tx(
                        tx_date, card["closing_day"], month_offset=0
                    )

                # If statement_date falls on or before the card's active next_closing_date,
                # it is part of the Current Statement Period debt.
                if stmt_date <= card["next_closing_date"]:
                    card["raw_matured_expenses"] = round(
                        card["raw_matured_expenses"] + abs_val, 2
                    )

        elif tx_type == TX_TYPE_TRANSFER:
            # Transfers are never counted as new Expenses!
            total_transfers = round(total_transfers + abs_val, 2)

            # 1. Deduct from source Cash/Bank account
            if acc_name in cash_accounts_map:
                cash_accounts_map[acc_name]["current_balance"] = round(
                    cash_accounts_map[acc_name]["current_balance"] - abs_val, 2
                )
            elif acc_name in credit_cards_map:
                credit_cards_map[acc_name]["raw_total_expenses"] = round(
                    credit_cards_map[acc_name]["raw_total_expenses"] + abs_val, 2
                )

            # 2. Credit destination Credit Card (reducing debt and restoring available limit)
            #    or credit destination Cash/Bank account
            if to_acc_name in credit_cards_map:
                credit_cards_map[to_acc_name]["raw_payments"] = round(
                    credit_cards_map[to_acc_name]["raw_payments"] + abs_val, 2
                )
            elif to_acc_name in cash_accounts_map:
                cash_accounts_map[to_acc_name]["current_balance"] = round(
                    cash_accounts_map[to_acc_name]["current_balance"] + abs_val, 2
                )

    # Finalize Total Liquid Cash/Bank Balance
    cash_accounts_list = list(cash_accounts_map.values())
    total_liquid_balance = round(
        sum(item["current_balance"] for item in cash_accounts_list), 2
    )

    # Finalize Credit Card summaries
    credit_cards_list: List[Dict[str, Any]] = []
    total_credit_card_debt = 0.0
    total_current_statement_debt = 0.0

    for card in credit_cards_map.values():
        limit_val = card["credit_limit"]
        total_debt = round(max(0.0, card["raw_total_expenses"] - card["raw_payments"]), 2)
        current_stmt_debt = round(
            max(0.0, card["raw_matured_expenses"] - card["raw_payments"]), 2
        )
        # Ensure current statement debt never exceeds total debt
        current_stmt_debt = min(current_stmt_debt, total_debt)
        future_stmt_debt = round(max(0.0, total_debt - current_stmt_debt), 2)
        available_limit = round(limit_val - total_debt, 2)

        if limit_val > 0:
            available_pct = max(0, min(100, int(round((max(0.0, available_limit) / limit_val) * 100))))
            used_pct = max(0, min(100, int(round((total_debt / limit_val) * 100))))
        else:
            available_pct = 0
            used_pct = 0

        card["total_debt"] = total_debt
        card["current_statement_debt"] = current_stmt_debt
        card["future_statement_debt"] = future_stmt_debt
        card["available_limit"] = available_limit
        card["available_percent"] = available_pct
        card["used_percent"] = used_pct

        total_credit_card_debt = round(total_credit_card_debt + total_debt, 2)
        total_current_statement_debt = round(
            total_current_statement_debt + current_stmt_debt, 2
        )
        credit_cards_list.append(card)

    return {
        "total_liquid_balance": total_liquid_balance,
        "cash_accounts": cash_accounts_list,
        "credit_cards": credit_cards_list,
        "total_income": total_income,
        "total_expense": total_expense,
        "total_transfers": total_transfers,
        "net_cash_flow": round(total_income - total_expense, 2),
        "total_credit_card_debt": total_credit_card_debt,
        "total_current_statement_debt": total_current_statement_debt,
    }


def get_transactions_for_display(
    search_text: str = "",
    type_filter: str = "All",
    reference_date: Optional[datetime.date] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve transactions in reverse-chronological/insertion order with enriched
    period and account display metadata for the Dashboard table.
    """
    ref_date = reference_date or datetime.date.today()
    conn = get_connection()
    cursor = conn.cursor()

    accounts_by_name = {
        row["name"]: dict(row)
        for row in cursor.execute("SELECT rowid AS row_id, * FROM accounts").fetchall()
    }
    rows = [
        dict(row)
        for row in cursor.execute("SELECT rowid AS row_id, * FROM finance ORDER BY rowid DESC").fetchall()
    ]
    conn.close()

    query = (search_text or "").strip().lower()
    result: List[Dict[str, Any]] = []

    for row in rows:
        try:
            amount_float = float(row.get("amount") or 0.0)
        except (TypeError, ValueError):
            amount_float = 0.0

        tx_type = row.get("transaction_type")
        if not tx_type:
            tx_type = TX_TYPE_INCOME if amount_float >= 0 else TX_TYPE_EXPENSE

        # Apply transaction type filter
        if type_filter == TX_TYPE_INCOME and tx_type != TX_TYPE_INCOME:
            continue
        if type_filter == TX_TYPE_EXPENSE and tx_type != TX_TYPE_EXPENSE:
            continue
        if type_filter == TX_TYPE_TRANSFER and tx_type != TX_TYPE_TRANSFER:
            continue

        acc_name = str(row.get("account") or "")
        to_acc_name = str(row.get("to_account") or "")
        category = str(row.get("category") or "")
        description = str(row.get("description") or "")
        date_str = str(row.get("date") or "")
        stmt_date_str = str(row.get("statement_date") or "")

        # Build human-readable account & statement period labels
        if tx_type == TX_TYPE_TRANSFER and to_acc_name:
            account_display = f"{acc_name} -> {to_acc_name}"
            period_display = "Debt Payment / Transfer"
        else:
            account_display = acc_name
            acc_obj = accounts_by_name.get(acc_name)
            if acc_obj and acc_obj["account_type"] == ACCOUNT_TYPE_CREDIT_CARD and tx_type == TX_TYPE_EXPENSE:
                closing_day = int(acc_obj["closing_day"] or 1)
                next_closing = calculate_next_closing_date(closing_day, ref_date)
                stmt_date = (
                    parse_date(stmt_date_str)
                    if stmt_date_str
                    else calculate_statement_closing_date_for_tx(
                        parse_date(date_str), closing_day, 0
                    )
                )
                stmt_formatted = format_date(stmt_date)
                if stmt_date <= next_closing:
                    period_display = f"Current Stmt ({stmt_formatted})"
                else:
                    period_display = f"Future Stmt ({stmt_formatted})"
            elif tx_type == TX_TYPE_INCOME:
                period_display = "Income"
            else:
                period_display = "Direct Expense"

        # Apply text search filter across all visible columns
        if query:
            searchable_blob = " ".join(
                [
                    date_str.lower(),
                    account_display.lower(),
                    category.lower(),
                    description.lower(),
                    tx_type.lower(),
                    period_display.lower(),
                    f"{abs(amount_float):.2f}",
                    str(abs(amount_float)),
                ]
            )
            if query not in searchable_blob:
                continue

        result.append(
            {
                "id": row.get("id"),
                "amount": amount_float,
                "transaction_type": tx_type,
                "category": category,
                "description": description,
                "account": acc_name,
                "to_account": to_acc_name,
                "account_display": account_display,
                "date": date_str,
                "statement_date": stmt_date_str,
                "period_display": period_display,
                "installments": row.get("installments") or 1,
                "installment_number": row.get("installment_number") or 1,
                "installment_group_id": row.get("installment_group_id"),
            }
        )

    return result


def reset_all_transactions() -> None:
    """Delete all transaction records from `finance` while keeping configured accounts intact."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM finance")
    conn.commit()
    conn.close()


# Automatically initialize and migrate the database when `database.py` is imported or executed directly
init_db()
