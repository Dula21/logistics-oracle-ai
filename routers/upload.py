import os
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
import pandas as pd
from auth.dependencies import verify_admin
from logger import get_logger
from cache import cache_clear_all

logger = get_logger("upload")
router = APIRouter(tags=["Upload"])

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOADS_DIR = os.path.join(PROJECT_ROOT, "uploads")
ORIGINAL_CSV = os.path.join(PROJECT_ROOT, "historic_sales.csv")

_active_csv_path: str = ORIGINAL_CSV
os.makedirs(UPLOADS_DIR, exist_ok=True)


def get_active_csv() -> str:
    return _active_csv_path


def set_active_csv(path: str):
    global _active_csv_path
    _active_csv_path = path


@router.post("/api/upload")
async def upload_csv(
    file: UploadFile = File(...),
    user_id: str = Depends(verify_admin)
):
    logger.info("csv_upload_start", filename=file.filename, user_id=user_id)

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = os.path.join(UPLOADS_DIR, f"uploaded_{timestamp}.csv")

    try:
        with open(save_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File save failed: {str(e)}")

    try:
        df = pd.read_csv(save_path)
        df.columns = [col.strip() for col in df.columns]

        required_cols = {"SKU_ID", "Date", "Sales_Units"}
        missing = required_cols - set(df.columns)
        if missing:
            os.remove(save_path)
            raise HTTPException(
                status_code=422,
                detail=f"CSV missing required columns: {', '.join(missing)}"
            )

        skus = df["SKU_ID"].astype(str).str.strip().str.upper().unique().tolist()
        if not skus:
            os.remove(save_path)
            raise HTTPException(status_code=422, detail="No SKU data found in CSV.")

        set_active_csv(save_path)

        from services.prophet_service import _forecast_cache
        _forecast_cache.clear()
        cache_clear_all()

        logger.info("csv_upload_success", filename=file.filename, skus=len(skus), rows=len(df), user_id=user_id)

        return JSONResponse({
            "status": "success",
            "filename": file.filename,
            "saved_as": os.path.basename(save_path),
            "skus_detected": skus,
            "first_sku": skus[0],
            "row_count": len(df),
            "message": f"CSV loaded. {len(skus)} SKUs detected, {len(df)} rows."
        })

    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(save_path):
            os.remove(save_path)
        raise HTTPException(status_code=500, detail=f"CSV validation failed: {str(e)}")


@router.post("/api/upload/reset")
async def reset_to_original(user_id: str = Depends(verify_admin)):
    if not os.path.exists(ORIGINAL_CSV):
        raise HTTPException(status_code=404, detail="Original CSV not found.")

    set_active_csv(ORIGINAL_CSV)

    from services.prophet_service import _forecast_cache
    _forecast_cache.clear()
    cache_clear_all()

    df = pd.read_csv(ORIGINAL_CSV)
    skus = df["SKU_ID"].astype(str).str.strip().str.upper().unique().tolist()

    logger.info("csv_reset", user_id=user_id)

    return JSONResponse({
        "status": "reset",
        "skus_detected": skus,
        "first_sku": skus[0],
        "message": "Reverted to original historic_sales.csv"
    })


@router.get("/api/upload/status")
async def upload_status():
    is_original = _active_csv_path == ORIGINAL_CSV
    return {
        "active_file": os.path.basename(_active_csv_path),
        "is_original": is_original,
        "path": _active_csv_path
    }