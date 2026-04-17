from datetime import date as Date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from app.db import queries

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


class TransactionIn(BaseModel):
    description: str = Field(..., min_length=1, max_length=200)
    amount: float = Field(..., gt=0)
    category: str = Field(..., min_length=1, max_length=100)
    date: Date
    type: str

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ("income", "expense"):
            raise ValueError("type must be 'income' or 'expense'")
        return v


@router.post("/", status_code=201)
def create_transaction(body: TransactionIn) -> dict:
    return queries.insert_transaction(
        description=body.description,
        amount=body.amount,
        category=body.category,
        date=str(body.date),
        type_=body.type,
    )


@router.get("/")
def read_transactions(
    date_from: Annotated[Date | None, Query()] = None,
    date_to: Annotated[Date | None, Query()] = None,
    category: Annotated[str | None, Query()] = None,
) -> list[dict]:
    return queries.list_transactions(
        date_from=str(date_from) if date_from else None,
        date_to=str(date_to) if date_to else None,
        category=category,
    )


@router.delete("/{transaction_id}", status_code=204)
def remove_transaction(transaction_id: int) -> None:
    if not queries.delete_transaction(transaction_id):
        raise HTTPException(status_code=404, detail="Transaction not found")


@router.get("/categories")
def read_categories() -> list[str]:
    return queries.list_categories()
