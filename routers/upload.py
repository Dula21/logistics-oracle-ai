import os
import shutil
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd

router = APIRouter()

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOADS_DIR = os.path.join(PROJECT_ROOT, "uploads")
ORIGINAL_CSV = os.path.join(PROJECT_ROOT, "historic_sales.csv")

# Runtime pointer — which CSV the app is currently using
_active_csv_path: str = ORIGINAL_CSV

os.makedirs(UPLOADS_DIR, exist_ok=True)


def get_active_csv() -> str:
    return _active_csv_path


def set_active_csv(path: str):
    global _active_csv_path
    _active_csv_path = path


# =====================================================================
# ENDPOINT 1: Upload a new CSV
# =====================================================================
@router.post("/api/upload")
async def upload_csv(file: UploadFile = File(...)):
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

    # Validate CSV structure
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

        # Extract unique SKUs
        skus = df["SKU_ID"].astype(str).str.strip().str.upper().unique().tolist()
        if not skus:
            os.remove(save_path)
            raise HTTPException(status_code=422, detail="No SKU data found in CSV.")

        # Switch app to use this new file
        set_active_csv(save_path)

        # Clear forecast cache so new data is used
        from services.prophet_service import _forecast_cache
        _forecast_cache.clear()

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


# =====================================================================
# ENDPOINT 2: Reset to original CSV
# =====================================================================
@router.post("/api/upload/reset")
async def reset_to_original():
    if not os.path.exists(ORIGINAL_CSV):
        raise HTTPException(status_code=404, detail="Original CSV not found.")

    set_active_csv(ORIGINAL_CSV)

    from services.prophet_service import _forecast_cache
    _forecast_cache.clear()

    df = pd.read_csv(ORIGINAL_CSV)
    skus = df["SKU_ID"].astype(str).str.strip().str.upper().unique().tolist()

    return JSONResponse({
        "status": "reset",
        "skus_detected": skus,
        "first_sku": skus[0],
        "message": "Reverted to original historic_sales.csv"
    })


# =====================================================================
# ENDPOINT 3: Current CSV status
# =====================================================================
@router.get("/api/upload/status")
async def upload_status():
    is_original = _active_csv_path == ORIGINAL_CSV
    return {
        "active_file": os.path.basename(_active_csv_path),
        "is_original": is_original,
        "path": _active_csv_path
    }