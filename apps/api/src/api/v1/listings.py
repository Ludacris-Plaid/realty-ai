import uuid
import os
import sys
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from .db import engine
from ...auth import TokenPayload
from .deps import require_user, optional_user

router = APIRouter()


class ListingCreate(BaseModel):
    address_street: str
    address_city: str
    address_state: str
    address_zip: str
    address_unit: Optional[str] = None
    property_type: str = "single_family"
    status: str = "draft"
    beds: Optional[int] = None
    baths: Optional[float] = None
    sqft: Optional[float] = None
    lot_size: Optional[float] = None
    year_built: Optional[int] = None
    garage_spaces: Optional[int] = None
    list_price: Optional[float] = None
    hoa_dues: Optional[float] = None
    description: Optional[str] = None
    features: Optional[list] = None
    mls_number: Optional[str] = None
    listed_at: Optional[datetime] = None
    client_id: Optional[str] = None


class ListingUpdate(BaseModel):
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_zip: Optional[str] = None
    address_unit: Optional[str] = None
    property_type: Optional[str] = None
    status: Optional[str] = None
    beds: Optional[int] = None
    baths: Optional[float] = None
    sqft: Optional[float] = None
    lot_size: Optional[float] = None
    year_built: Optional[int] = None
    garage_spaces: Optional[int] = None
    list_price: Optional[float] = None
    hoa_dues: Optional[float] = None
    description: Optional[str] = None
    features: Optional[list] = None
    mls_number: Optional[str] = None
    listed_at: Optional[datetime] = None
    sold_at: Optional[datetime] = None
    sold_price: Optional[float] = None
    client_id: Optional[str] = None


def _row_to_dict(r):
    return {
        "id": str(r[0]),
        "address_street": r[1],
        "address_city": r[2],
        "address_state": r[3],
        "address_zip": r[4],
        "address_unit": r[5],
        "property_type": r[6],
        "status": r[7],
        "beds": r[8],
        "baths": float(r[9]) if r[9] is not None else None,
        "sqft": r[10],
        "lot_size": r[11],
        "year_built": r[12],
        "garage_spaces": r[13],
        "list_price": float(r[14]) if r[14] is not None else None,
        "hoa_dues": float(r[15]) if r[15] is not None else None,
        "description": r[16] or "",
        "features": r[17] or [],
        "images": r[18] or [],
        "mls_number": r[19] or "",
        "listed_at": r[20].isoformat() if r[20] else None,
        "sold_at": r[21].isoformat() if r[21] else None,
        "sold_price": float(r[22]) if r[22] is not None else None,
        "client_id": str(r[23]) if r[23] else None,
        "created_at": r[24].isoformat() if r[24] else None,
        "updated_at": r[25].isoformat() if r[25] else None,
    }


_COLUMNS = """
    id, address_street, address_city, address_state, address_zip,
    address_unit, property_type, status, beds, baths, sqft, lot_size,
    year_built, garage_spaces, list_price, hoa_dues, description,
    features, images, mls_number, listed_at, sold_at, sold_price,
    client_id, created_at, updated_at
"""


@router.get("/")
def list_listings(
    status: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    beds: Optional[int] = Query(None),
    current_user: Optional[TokenPayload] = Depends(optional_user),
):
    query = f"SELECT {_COLUMNS} FROM properties WHERE 1=1"
    params = {}
    if status:
        query += " AND status = :status"
        params["status"] = status
    if city:
        query += " AND LOWER(address_city) LIKE :city"
        params["city"] = f"%{city.lower()}%"
    if min_price is not None:
        query += " AND list_price >= :min_price"
        params["min_price"] = min_price
    if max_price is not None:
        query += " AND list_price <= :max_price"
        params["max_price"] = max_price
    if beds is not None:
        query += " AND beds >= :beds"
        params["beds"] = beds
    query += " ORDER BY created_at DESC"

    with Session(engine) as session:
        rows = session.execute(text(query), params).fetchall()

    return {"listings": [_row_to_dict(r) for r in rows], "total": len(rows)}


@router.get("/{listing_id}")
def get_listing(listing_id: str, current_user: Optional[TokenPayload] = Depends(optional_user)):
    row = _fetch_listing(listing_id)
    if not row:
        raise HTTPException(status_code=404, detail="Listing not found")
    return _row_to_dict(row)


def _fetch_listing(listing_id: str):
    with Session(engine) as session:
        return session.execute(
            text(f"SELECT {_COLUMNS} FROM properties WHERE id = :id"),
            {"id": listing_id},
        ).fetchone()


@router.post("/", status_code=201)
def create_listing(data: ListingCreate, current_user: TokenPayload = Depends(require_user)):
    listing_id = str(uuid.uuid4())
    now = datetime.utcnow()
    agent_id = current_user.sub
    brokerage_id = current_user.brokerage_id or agent_id

    with Session(engine) as session:
        session.execute(
            text("""
                INSERT INTO properties
                    (id, agent_id, brokerage_id, client_id,
                     address_street, address_city, address_state, address_zip, address_unit,
                     property_type, status, beds, baths, sqft, lot_size,
                     year_built, garage_spaces, list_price, hoa_dues,
                     description, features, mls_number, listed_at,
                     created_at, updated_at)
                VALUES
                    (:id, :agent_id, :brokerage_id, :client_id,
                     :street, :city, :state, :zip, :unit,
                     :prop_type, :status, :beds, :baths, :sqft, :lot_size,
                     :year_built, :garage, :list_price, :hoa,
                     :description, :features, :mls, :listed_at,
                     :created_at, :updated_at)
            """),
            {
                "id": listing_id,
                "agent_id": agent_id,
                "brokerage_id": brokerage_id,
                "client_id": data.client_id,
                "street": data.address_street,
                "city": data.address_city,
                "state": data.address_state,
                "zip": data.address_zip,
                "unit": data.address_unit,
                "prop_type": data.property_type,
                "status": data.status,
                "beds": data.beds,
                "baths": data.baths,
                "sqft": data.sqft,
                "lot_size": data.lot_size,
                "year_built": data.year_built,
                "garage": data.garage_spaces,
                "list_price": data.list_price,
                "hoa": data.hoa_dues,
                "description": data.description,
                "features": data.features or [],
                "mls": data.mls_number,
                "listed_at": data.listed_at,
                "created_at": now,
                "updated_at": now,
            },
        )
        session.commit()

    return _row_to_dict(_fetch_listing(listing_id))


@router.put("/{listing_id}")
def update_listing(listing_id: str, data: ListingUpdate, current_user: TokenPayload = Depends(require_user)):
    fields = data.model_dump(exclude_none=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    field_map = {
        "address_street": "address_street", "address_city": "address_city",
        "address_state": "address_state", "address_zip": "address_zip",
        "address_unit": "address_unit", "property_type": "property_type",
        "status": "status", "beds": "beds", "baths": "baths",
        "sqft": "sqft", "lot_size": "lot_size", "year_built": "year_built",
        "garage_spaces": "garage_spaces", "list_price": "list_price",
        "hoa_dues": "hoa_dues", "description": "description",
        "features": "features", "mls_number": "mls_number",
        "listed_at": "listed_at", "sold_at": "sold_at",
        "sold_price": "sold_price", "client_id": "client_id",
    }

    set_parts = []
    params = {"id": listing_id}
    for py_field, db_col in field_map.items():
        if py_field in fields:
            set_parts.append(f"{db_col} = :{py_field}")
            params[py_field] = fields[py_field]

    set_parts.append("updated_at = NOW()")

    with Session(engine) as session:
        result = session.execute(
            text(f"UPDATE properties SET {', '.join(set_parts)} WHERE id = :id"),
            params,
        )
        session.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Listing not found")

    row = _fetch_listing(listing_id)
    return _row_to_dict(row) if row else {"id": listing_id}


@router.delete("/{listing_id}")
def delete_listing(listing_id: str, current_user: TokenPayload = Depends(require_user)):
    with Session(engine) as session:
        result = session.execute(
            text("DELETE FROM properties WHERE id = :id"),
            {"id": listing_id},
        )
        session.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Listing not found")
    return {"status": "deleted", "id": listing_id}


class DescriptionRequest(BaseModel):
    tone: str = "professional"
    include_features: bool = True


@router.post("/{listing_id}/generate-description")
def generate_listing_description(listing_id: str, req: DescriptionRequest, current_user: TokenPayload = Depends(require_user)):
    with Session(engine) as session:
        row = session.execute(
            text("SELECT address_street, address_city, address_state, beds, baths, sqft, list_price, description, features, property_type, mls_number FROM properties WHERE id = :id"),
            {"id": listing_id},
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Listing not found")

    property_context = (
        f"{row[0]}, {row[1]}, {row[2]} | "
        f"{row[3]} bed, {row[4]} bath, {row[5]} sqft | "
        f"${float(row[6]):,.2f}" if row[6] else "Price unavailable"
    )

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "packages", "ai"))
    try:
        from agent import ask
        prompt = (
            f"Write a {req.tone} MLS listing description for this property:\n"
            f"{property_context}\n"
        )
        if req.include_features and row[8]:
            prompt += f"Features: {', '.join(row[8])}\n"
        prompt += "\nWrite 2-3 paragraphs. Do not include placeholders."

        result = ask(prompt, override_model="fast-model")
        description = result.get("response", "")

        with Session(engine) as session:
            session.execute(
                text("UPDATE properties SET description = :desc, updated_at = NOW() WHERE id = :id"),
                {"id": listing_id, "desc": description},
            )
            session.commit()

        return {"description": description, "listing_id": listing_id}
    except Exception as e:
        fallback = (
            f"Charming {row[3]}-bedroom, {row[4]}-bathroom "
            f"{row[9].replace('_', ' ')} located at {row[0]}, {row[1]}, {row[2]}. "
            f"This beautiful property offers {row[5]:,.0f} square feet of living space."
        )
        return {"description": fallback, "listing_id": listing_id, "fallback": True, "error": str(e)}
