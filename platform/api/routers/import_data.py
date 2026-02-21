"""
AIMA – Google Sheet Import Router
Accepts a public Google Sheet URL, auto-detects columns,
and upserts customers + orders into the AIMA database.
"""

import re
import csv
import io
import uuid
import hashlib
from datetime import datetime
from typing import Optional
from urllib.request import urlopen, Request
from urllib.error import URLError

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel

from ..database import get_db

router = APIRouter(prefix="/import", tags=["Import"])


COLUMN_KEYWORDS = {
    "email":        ["email", "e-mail", "email_address", "buyer_email", "customer_email", "mail", "buyer email"],
    "full_name":    ["name", "customer_name", "buyer_name", "full_name", "fullname", "customer name", "buyer name", "recipient"],
    "first_name":   ["first_name", "firstname", "first name", "given_name"],
    "last_name":    ["last_name", "lastname", "last name", "surname", "family_name"],
    "phone":        ["phone", "mobile", "contact", "telephone", "tel", "cell", "phone_number", "mobile_number"],
    "city":         ["city", "town", "district", "area", "region", "zone", "thana", "upazila"],
    "country":      ["country", "nation", "country_name"],
    "order_id":     ["order_id", "order id", "order_number", "order no", "order#", "invoice", "transaction_id", "transaction id"],
    "order_date":   ["date", "order_date", "order date", "purchase_date", "created_at", "placed_at", "order placed", "created date"],
    "amount":       ["amount", "total", "price", "order_total", "grand_total", "revenue", "gmv", "payment", "subtotal", "net_amount", "total_price", "grand total", "net amount", "sale amount", "order value"],
    "product_name": ["product", "item", "sku", "product_name", "item_name", "description", "goods", "product name", "item name"],
    "status":       ["status", "order_status", "payment_status", "fulfillment_status", "order status"],
    "quantity":     ["quantity", "qty", "count", "units", "pieces"],
    "currency":     ["currency", "curr", "currency_code"],
}


class ImportRequest(BaseModel):
    sheet_url: str
    org_id: str = "00000000-0000-0000-0000-000000000001"


def _sheet_to_csv_url(url: str) -> str:
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", url)
    if not match:
        raise ValueError(
            "Could not extract Sheet ID from the URL. "
            "Make sure it looks like: https://docs.google.com/spreadsheets/d/SHEET_ID/..."
        )
    sheet_id = match.group(1)
    gid_match = re.search(r"[#&?]gid=(\d+)", url)
    gid = gid_match.group(1) if gid_match else "0"
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"


def _fetch_csv(csv_url: str):
    try:
        req = Request(csv_url, headers={"User-Agent": "Mozilla/5.0"})
        response = urlopen(req, timeout=15)
        raw = response.read().decode("utf-8-sig")
    except URLError as e:
        raise ValueError(
            f"Could not download the sheet: {e}. "
            "Make sure the sheet is set to 'Anyone with the link can view'."
        )
    reader = csv.DictReader(io.StringIO(raw))
    rows = list(reader)
    fieldnames = list(reader.fieldnames or [])
    return rows, fieldnames


def _detect_columns(fieldnames: list) -> dict:
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


def _clean_amount(val: str) -> float:
    if not val:
        return 0.0
    cleaned = re.sub(r"[^\d.]", "", str(val).replace(",", ""))
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _clean_date(val: str) -> datetime:
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


def _make_id(org_id: str, key: str) -> str:
    raw = (org_id + key.lower().strip()).encode()
    return str(uuid.UUID(hashlib.md5(raw).hexdigest()))


def _build_records(rows: list, mapping: dict, org_id: str):
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

        key = email or phone or full_name or str(uuid.uuid4())
        cid = _make_id(org_id, key)

        if cid not in customers:
            customers[cid] = {
                "id": cid, "org_id": org_id,
                "email": email or f"{cid[:8]}@unknown.com",
                "first_name": first, "last_name": last,
                "phone": phone or None,
                "city": city or None,
                "country": country,
            }

        raw_date = get(row, "order_date")
        raw_amount = get(row, "amount")
        raw_order_id = get(row, "order_id")
        raw_product = get(row, "product_name") or "Order"
        raw_status = get(row, "status") or "completed"
        raw_qty = get(row, "quantity") or "1"
        raw_currency = get(row, "currency") or "BDT"

        amount = _clean_amount(raw_amount)
        order_date = _clean_date(raw_date)
        oid = _make_id(org_id, raw_order_id or (cid + raw_date + raw_amount))

        try:
            qty = int(float(raw_qty))
        except (ValueError, TypeError):
            qty = 1

        orders.append({
            "id": oid,
            "customer_id": cid,
            "org_id": org_id,
            "external_id": raw_order_id or None,
            "amount": amount,
            "currency": raw_currency,
            "status": raw_status.lower().replace(" ", "_"),
            "product": raw_product,
            "quantity": qty,
            "ordered_at": order_date,
        })

    return list(customers.values()), orders


@router.post("/preview")
async def preview_sheet(body: ImportRequest):
    """
    Fetch and parse a Google Sheet without importing.
    Returns detected column mapping so the user can review before committing.
    """
    try:
        csv_url = _sheet_to_csv_url(body.sheet_url)
        rows, fieldnames = _fetch_csv(csv_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    mapping = _detect_columns(fieldnames)
    detected = {v: k for k, v in mapping.items()}

    columns = [
        {"name": col, "detected_as": detected.get(col)}
        for col in fieldnames
    ]

    warnings = [
        f"Could not detect a column for: {f}"
        for f in ["order_date", "amount"]
        if f not in mapping
    ]

    return {
        "row_count": len(rows),
        "column_count": len(fieldnames),
        "columns": columns,
        "mapping": mapping,
        "warnings": warnings,
        "sample": rows[:3] if rows else [],
    }


@router.post("/google-sheet")
async def import_google_sheet(
    body: ImportRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Import customers and orders from a public Google Sheet.
    Auto-detects column types. Safe to re-run (upsert idempotent).
    """
    try:
        csv_url = _sheet_to_csv_url(body.sheet_url)
        rows, fieldnames = _fetch_csv(csv_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not rows:
        raise HTTPException(status_code=400, detail="The sheet appears to be empty.")

    mapping = _detect_columns(fieldnames)
    if not mapping:
        raise HTTPException(
            status_code=400,
            detail=(
                "Could not detect any known columns. "
                "Make sure your sheet has headers like: Email, Name, Order Date, Amount, etc."
            ),
        )

    customers, orders = _build_records(rows, mapping, body.org_id)

    for c in customers:
        await db.execute(
            text("""
                INSERT INTO customers
                    (id, org_id, email, first_name, last_name, phone, city, country,
                     tags, properties, created_at, updated_at)
                VALUES
                    (:id, :org_id, :email, :first_name, :last_name, :phone, :city, :country,
                     '{}', '{}', NOW(), NOW())
                ON CONFLICT (id) DO UPDATE SET
                    email      = EXCLUDED.email,
                    first_name = EXCLUDED.first_name,
                    last_name  = EXCLUDED.last_name,
                    phone      = COALESCE(EXCLUDED.phone, customers.phone),
                    city       = COALESCE(EXCLUDED.city, customers.city),
                    updated_at = NOW()
            """),
            {
                "id": c["id"], "org_id": c["org_id"],
                "email": c["email"],
                "first_name": c["first_name"], "last_name": c["last_name"],
                "phone": c["phone"], "city": c["city"], "country": c["country"],
            },
        )

    for o in orders:
        items_json = (
            f'[{{"name": "{o["product"].replace(chr(34), "")}", '
            f'"quantity": {o["quantity"]}, "price": {o["amount"]}}}]'
        )
        await db.execute(
            text("""
                INSERT INTO orders
                    (id, customer_id, org_id, external_id, total, subtotal, currency,
                     status, items, ordered_at, created_at)
                VALUES
                    (:id, :customer_id, :org_id, :external_id, :amount, :amount, :currency,
                     :status, :items::jsonb, :ordered_at, NOW())
                ON CONFLICT (id) DO UPDATE SET
                    total      = EXCLUDED.total,
                    subtotal   = EXCLUDED.subtotal,
                    status     = EXCLUDED.status
            """),
            {
                "id": o["id"], "customer_id": o["customer_id"], "org_id": o["org_id"],
                "external_id": o["external_id"],
                "amount": o["amount"], "currency": o["currency"],
                "status": o["status"], "items": items_json,
                "ordered_at": o["ordered_at"],
            },
        )

    await db.commit()

    return {
        "success": True,
        "customers_imported": len(customers),
        "orders_imported": len(orders),
        "message": (
            f"Successfully imported {len(customers)} customers "
            f"and {len(orders)} orders."
        ),
    }