from datetime import date as Date
from typing import Annotated

from fastapi import APIRouter, Query

from app.db import queries

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/summary")
def monthly_summary(
    year: Annotated[int, Query(ge=2000, le=2100)] = Date.today().year,
    month: Annotated[int, Query(ge=1, le=12)] = Date.today().month,
) -> dict:
    return queries.get_summary(year, month)


@router.get("/expenses-by-category")
def expenses_by_category(
    year: Annotated[int, Query(ge=2000, le=2100)] = Date.today().year,
    month: Annotated[int, Query(ge=1, le=12)] = Date.today().month,
) -> list[dict]:
    return queries.get_expenses_by_category(year, month)


@router.get("/balance-evolution")
def balance_evolution(
    months: Annotated[int, Query(ge=1, le=60)] = 12,
) -> list[dict]:
    return queries.get_monthly_balance_evolution(months)
