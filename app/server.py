"""Dashboard intake API: the station POSTs one contract-2 JSON per plate scan (docs/contracts.md §2).

Run (repo root): .venv-app/Scripts/python -m uvicorn app.server:app --host 0.0.0.0 --port 8000
DB path: env INTAKE_DB (default app/dashboard.db).
"""
from typing import Literal, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app import store


class Item(BaseModel):
    name: str
    before_frac: Optional[float] = None
    after_frac: Optional[float] = None
    pct_eaten: Optional[float] = Field(None, ge=0, le=100)
    pct_area: Optional[float] = None   # area-only %; pct_eaten = mean(pct_area, pct_depth) when depth ran
    pct_depth: Optional[float] = None
    kcal: Optional[float] = None
    protein_g: Optional[float] = None


class Scan(BaseModel):
    scan_id: str = Field(min_length=1)
    station_id: str
    time: str
    resident_id: Optional[str] = None  # null when no QR was read
    meal: Optional[Literal["breakfast", "lunch", "dinner"]] = None
    phase: Literal["before", "after"]
    status: Literal["ok", "no_qr", "unknown_resident", "no_plate", "error"]
    needs_review: bool = False
    review_reasons: list[str] = []
    items: list[Item] = []
    total_pct_eaten: Optional[float] = Field(None, ge=0, le=100)
    chart_bin: Optional[Literal[0, 25, 50, 75, 100]] = None
    kcal: Optional[float] = None
    protein_g: Optional[float] = None
    annotated_jpg_b64: Optional[str] = None
    replaces: Optional[str] = None  # scan_id this one redoes (station REDO LAST)
    method: Optional[Literal["area", "area+depth"]] = None


def create_app(db: str | None = None) -> FastAPI:
    api = FastAPI(title="Intake.ai dashboard API")

    @api.get("/api/health")
    def health():
        return {"ok": True}

    @api.post("/api/scan")
    def post_scan(scan: Scan):
        con = store.connect(db)
        try:
            store.insert_scan(con, scan.model_dump())  # duplicate scan_id = station retry, ignored
        finally:
            con.close()
        return {"ok": True}

    @api.get("/api/scans")
    def get_scans(limit: int = 50, photos: bool = False):
        con = store.connect(db)
        try:
            scans = store.list_scans(con, limit)
        finally:
            con.close()
        if not photos:
            for s in scans:
                s["annotated_jpg_b64"] = "<jpeg>" if s.get("annotated_jpg_b64") else None
        return scans

    return api


app = create_app()
