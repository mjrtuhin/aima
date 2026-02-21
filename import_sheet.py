"""
AIMA Google Sheet Importer
--------------------------
Auto-detects column types from any Google Sheet and imports
customers + orders into the AIMA database.

Usage:
    python import_sheet.py "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"

Requirements:
    pip install psycopg2-binary requests --break-system-packages
"""

import sys
import re
import uuid
import csv
import io
import hashlib
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError

try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:
    print("\n  psycopg2 not installed. Run:")
    print("  pip install psycopg2-binary --break-system-packages\n")
    sys.exit(1)


DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "aima",
    "user":     "aima",
    "password": "aima_password",
}

ORG_ID = "00000000-0000-0000-0000-000000000001"

COLUMN_KEYWORDS = {
    "email":        ["email", "e-mail", "email_address", "buyer_email", "customer_email", "mail", "buyer email"],
    "full_name":    ["name", "customer_name", "buyer_name", "full_name", "fullname", "customer name", "buyer name", "recipient"],
    "first_name":   ["first_name", "firstname", "first name", "given_name"],
    "last_name":    ["last_name", "lastname", "last name", "surname", "family_name"],
    "phone":        ["phone", "mobile", "contact", "telephone", "tel", "cell", "phone_number", "mobile_number"],
    "city":         ["city", "town", "district", "area", "region", "zone", "thana", "upazila"],
    "country":      ["country", "nation", "country_name"],
    "order_id":     ["order_id", "order id", "order_number", "order no", "order#", "invoice", "transaction_id", "transaction id", "id", "#"],
    "order_date":   ["date", "order_date", "order date", "purchase_date", "created_at", "placed_at", "order placed", "created date", "purchase date"],
    "amount":       ["amount", "total", "price", "order_total", "grand_total", "revenue", "gmv", "payment", "subtotal", "net_amount", "total_price", "order amount", "grand total", "net amount", "sale amount", "order value"],
    "product_name": ["product", "item", "sku", "product_name", "item_name", "description", "goods", "product name", "item name", "product title"],
    "status":       ["status", "order_status", "payment_status", "fulfillment_status", "order status"],
    "quantity":     ["quantity", "qty", "count", "units", "pieces"],
    "currency":     ["currency", "curr", "currency_code"],
}


def sheet_to_csv_url(url: str) -> str:
    """Convert any Google Sheets URL to a direct CSV export URL."""
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", url)
    if not match:
        print(f"\n  Could not extract Sheet ID from URL: {url}")
        print("  Make sure it looks like: https://docs.google.com/spreadsheets/d/SHEET_ID/...\n")
        sys.exit(1)
    sheet_id = match.group(1)

    gid_match = re.search(r"[#&?]gid=(\d+)", url)
    gid = gid_match.group(1) if gid_match else "0"

    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"


def fetch_csv(url: str) -> list[dict]:
    """Download the CSV from Google Sheets and return list of row dicts."""
    print(f"\n  Fetching sheet...")
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        response = urlopen(req, timeout=15)
        raw = response.read().decode("utf-8-sig")
    except URLError as e:
        print(f"\n  Could not download sheet: {e}")
        print("  Make sure the sheet is set to 'Anyone with the link can view'.\n")
        sys.exit(1)

    reader = csv.DictReader(io.StringIO(raw))
    rows = [row for row in reader]
    print(f"  Downloaded {len(rows)} rows, {len(reader.fieldnames)} columns.")
    return rows, reader.fieldnames


def detect_columns(fieldnames: list[str]) -> dict:
    """Auto-detect which column maps to which field."""
    mapping = {}
    fieldnames_lower = {f: f.lower().strip() for f in fieldnames}

    for field, keywords in COLUMN_KEYWORDS.items():
        for col, col_lower in fieldnames_lower.items():
            if col in mapping.values():
                continue
            for kw in keywords:
                if kw in col_lower or col_lower in kw:
                    mapping[field] = col
                    break
            if field in mapping:
                break

    return mapping


def clean_amount(val: str) -> float:
    """Strip currency symbols and commas, return float."""
    if not val:
        return 0.0
    cleaned = re.sub(r"[^\d.]", "", str(val).replace(",", ""))
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def clean_date(val: str) -> datetime:
    """Try multiple date formats and return a datetime."""
    if not val:
        return datetime.utcnow()
    formats = [
        "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y",
        "%d-%m-%Y", "%Y/%m/%d", "%d %b %Y",
        "%b %d, %Y", "%d %B %Y", "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(val.strip(), fmt)
        except ValueError:
            continue
    return datetime.utcnow()


def make_customer_id(email: str, phone: str, name: str) -> str:
    """Generate a deterministic UUID from customer identifiers."""
    key = (email or phone or name or str(uuid.uuid4())).lower().strip()
    return str(uuid.UUID(hashlib.md5((ORG_ID + key).encode()).hexdigest()))


def build_records(rows: list[dict], mapping: dict) -> tuple[list, list]:
    """Build customer and order records from raw rows."""
    customers = {}
    orders = []

    def get(row, field):
        col = mapping.get(field)
        return row.get(col, "").strip() if col else ""

    for row in rows:
        email = get(row, "email").lower()
        full_name = get(row, "full_name")
        first_name = get(row, "first_name")
        last_name = get(row, "last_name")
        phone = get(row, "phone")
        city = get(row, "city")
        country = get(row, "country") or "BD"

        if not full_name and (first_name or last_name):
            full_name = f"{first_name} {last_name}".strip()

        first = first_name or (full_name.split()[0] if full_name else "Unknown")
        last = last_name or (" ".join(full_name.split()[1:]) if full_name and " " in full_name else "")

        cid = make_customer_id(email, phone, full_name)

        if cid not in customers:
            customers[cid] = {
                "id": cid,
                "org_id": ORG_ID,
                "email": email or f"{cid[:8]}@unknown.com",
                "first_name": first,
                "last_name": last,
                "phone": phone,
                "city": city,
                "country": country,
                "tags": [],
                "properties": {},
            }

        raw_date = get(row, "order_date")
        raw_amount = get(row, "amount")
        raw_order_id = get(row, "order_id")
        raw_product = get(row, "product_name") or "Order"
        raw_status = get(row, "status") or "completed"
        raw_qty = get(row, "quantity") or "1"
        raw_currency = get(row, "currency") or "BDT"

        amount = clean_amount(raw_amount)
        order_date = clean_date(raw_date)
        order_id = make_customer_id(raw_order_id or (cid + raw_date + raw_amount), "", "")

        try:
            qty = int(float(raw_qty))
        except ValueError:
            qty = 1

        orders.append({
            "id": order_id,
            "customer_id": cid,
            "org_id": ORG_ID,
            "external_id": raw_order_id or None,
            "amount": amount,
            "currency": raw_currency,
            "status": raw_status.lower().replace(" ", "_"),
            "items": [{"name": raw_product, "quantity": qty, "price": amount}],
            "ordered_at": order_date,
        })

    return list(customers.values()), orders


def import_to_db(customers: list, orders: list):
    """Upsert customers and orders into AIMA's PostgreSQL database."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    print(f"\n  Importing {len(customers)} customers...")

    customer_rows = [
        (
            c["id"], c["org_id"], c["email"], c["first_name"], c["last_name"],
            c["phone"] or None, c["city"] or None, None, c["country"],
            [], "{}", datetime.utcnow(), datetime.utcnow()
        )
        for c in customers
    ]

    execute_values(
        cur,
        """
        INSERT INTO customers
            (id, org_id, email, first_name, last_name, phone, city, timezone, country,
             tags, properties, created_at, updated_at)
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            email       = EXCLUDED.email,
            first_name  = EXCLUDED.first_name,
            last_name   = EXCLUDED.last_name,
            phone       = COALESCE(EXCLUDED.phone, customers.phone),
            city        = COALESCE(EXCLUDED.city, customers.city),
            updated_at  = NOW()
        """,
        customer_rows,
    )

    print(f"  Importing {len(orders)} orders...")

    order_rows = [
        (
            o["id"], o["customer_id"], o["org_id"],
            o["external_id"], o["amount"], o["currency"],
            o["status"], o["items"], o["ordered_at"],
            datetime.utcnow(), datetime.utcnow()
        )
        for o in orders
    ]

    execute_values(
        cur,
        """
        INSERT INTO orders
            (id, customer_id, org_id, external_id, amount, currency,
             status, items, ordered_at, created_at, updated_at)
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            amount     = EXCLUDED.amount,
            status     = EXCLUDED.status,
            updated_at = NOW()
        """,
        order_rows,
        template="(%s, %s, %s, %s, %s, %s, %s, %s::jsonb[], %s, %s, %s)",
    )

    conn.commit()
    cur.close()
    conn.close()


def print_mapping(mapping: dict, fieldnames: list[str]):
    """Print detected column mapping in a readable way."""
    detected = {v: k for k, v in mapping.items()}
    print("\n  Column Detection Results:")
    print("  " + "-" * 50)
    for col in fieldnames:
        role = detected.get(col)
        if role:
            print(f"  {col:<35} →  {role}")
        else:
            print(f"  {col:<35}     (ignored)")
    print("  " + "-" * 50)

    required = ["order_date", "amount"]
    missing = [r for r in required if r not in mapping]
    if missing:
        print(f"\n  WARNING: Could not detect columns for: {', '.join(missing)}")
        print("  Import will continue but some data may be missing.\n")
    else:
        print("\n  All key columns detected successfully.\n")


def main():
    if len(sys.argv) < 2:
        print("\n  Usage: python import_sheet.py \"YOUR_GOOGLE_SHEET_URL\"\n")
        sys.exit(1)

    url = sys.argv[1]

    print("\n" + "=" * 60)
    print("  AIMA — Google Sheet Importer")
    print("=" * 60)

    csv_url = sheet_to_csv_url(url)
    rows, fieldnames = fetch_csv(csv_url)

    if not rows:
        print("\n  Sheet appears to be empty. Nothing to import.\n")
        sys.exit(0)

    mapping = detect_columns(fieldnames)
    print_mapping(mapping, fieldnames)

    if not mapping:
        print("  Could not detect any known columns.")
        print("  Make sure your sheet has headers like: Email, Name, Date, Amount, Order ID, etc.\n")
        sys.exit(1)

    answer = input("  Proceed with import? (y/n): ").strip().lower()
    if answer != "y":
        print("  Import cancelled.\n")
        sys.exit(0)

    customers, orders = build_records(rows, mapping)

    print(f"\n  Built {len(customers)} unique customers and {len(orders)} orders.")

    try:
        import_to_db(customers, orders)
    except psycopg2.OperationalError as e:
        print(f"\n  Could not connect to database: {e}")
        print("  Make sure AIMA Docker containers are running: docker compose up -d\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n  Import error: {e}\n")
        raise

    print("\n" + "=" * 60)
    print(f"  DONE!")
    print(f"  {len(customers)} customers imported")
    print(f"  {len(orders)} orders imported")
    print(f"\n  Open http://localhost:3000 to see your data.")
    print(f"  Go to Customers page — your Daraz buyers are there.")
    print(f"  Go to Segments page — click Re-Segment to group them.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
