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
        "agent_id": str(r[1]) if r[1] else None,
        "address_street": r[2],
        "address_city": r[3],
        "address_state": r[4],
        "address_zip": r[5],
        "property_type": r[6],
        "status": r[7],
        "beds": r[8],
        "baths": float(r[9]) if r[9] is not None else None,
        "sqft": r[10],
        "list_price": float(r[11]) if r[11] is not None else None,
        "description": r[12] or "",
        "features": r[13] or [],
        "images": r[14] or [],
        "mls_number": r[15] or "",
        "zillow_url": r[16] if len(r) > 16 else None,
        "created_at": r[17].isoformat() if len(r) > 17 and r[17] else None,
        "updated_at": r[18].isoformat() if len(r) > 18 and r[18] else None,
    }


_COLUMNS = """
    id, agent_id, address_street, address_city, address_state, address_zip,
    property_type, status, beds, baths, sqft, list_price, description,
    features, images, mls_number, zillow_url, created_at, updated_at
"""


@router.get("")
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

    return [_row_to_dict(r) for r in rows]


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

    with Session(engine) as session:
        session.execute(
            text("""
                INSERT INTO properties
                    (id, agent_id,
                     address_street, address_city, address_state, address_zip,
                     property_type, status, beds, baths, sqft, list_price,
                     description, features, mls_number,
                     created_at, updated_at)
                VALUES
                    (:id, :agent_id,
                     :street, :city, :state, :zip,
                     :prop_type, :status, :beds, :baths, :sqft, :list_price,
                     :description, :features, :mls,
                     :created_at, :updated_at)
            """),
            {
                "id": listing_id,
                "agent_id": agent_id,
                "street": data.address_street,
                "city": data.address_city,
                "state": data.address_state,
                "zip": data.address_zip,
                "prop_type": data.property_type,
                "status": data.status,
                "beds": data.beds,
                "baths": data.baths,
                "sqft": data.sqft,
                "list_price": data.list_price,
                "description": data.description,
                "features": data.features or [],
                "mls": data.mls_number,
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
        "property_type": "property_type",
        "status": "status", "beds": "beds", "baths": "baths",
        "sqft": "sqft", "list_price": "list_price",
        "description": "description",
        "features": "features", "mls_number": "mls_number",
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
