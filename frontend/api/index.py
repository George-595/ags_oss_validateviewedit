from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import tempfile
import hashlib
from pydantic import BaseModel
from typing import Dict, Any, List

# We will implement the actual logic in ags_service.py
import ags_service

app = FastAPI(title="Quore AGS Validator API", version="0.1.0")

# Build allowed origins — includes localhost for dev, and Vercel domains for production
_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
]
# Allow the specific production frontend URL if set via env var
_frontend_url = os.environ.get("FRONTEND_URL", "").strip()
if _frontend_url:
    _origins.append(_frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",  # covers all preview deployments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ValidationResponse(BaseModel):
    is_valid: bool
    errors: list
    warnings: list
    file_hash: str
    metadata: Dict[str, Any]

@app.get("/")
@app.get("/api")
@app.get("/api/")
def health_check():
    return {"status": "ok", "message": "Quore AGS API is running"}

@app.post("/validate")
@app.post("/api/validate", response_model=ValidationResponse)
async def validate_ags_file(file: UploadFile = File(...)):
    if not file.filename.endswith('.ags'):
        raise HTTPException(status_code=400, detail="Must be an .ags file")
    
    # Save uploaded file to temp file securely
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ags") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        
        # Calculate Hash
        with open(tmp_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
            
        # Validate using AGS service
        results = ags_service.validate_file(tmp_path)
        
        return {
            "is_valid": results["is_valid"],
            "errors": results["errors"],
            "warnings": results["warnings"],
            "file_hash": file_hash,
            "metadata": results.get("metadata", {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)

@app.post("/convert/to-excel")
@app.post("/api/convert/to-excel")
async def convert_to_excel(file: UploadFile = File(...)):
    if not file.filename.endswith('.ags'):
        raise HTTPException(status_code=400, detail="Must be an .ags file")
        
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ags") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
            
        excel_path = tmp_path.replace(".ags", ".xlsx")
        
        # We need to tell python-ags4 to convert 
        # ags_service handles this
        ags_service.convert_to_excel(tmp_path, excel_path)
        
        from fastapi.responses import FileResponse
        return FileResponse(excel_path, filename=file.filename.replace(".ags", ".xlsx"), 
                            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            background=ags_service.cleanup_task(tmp_path, excel_path))
    except Exception as e:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
             os.remove(tmp_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/convert/to-ags")
@app.post("/api/convert/to-ags")
async def convert_to_ags(file: UploadFile = File(...)):
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Must be an .xlsx file")
        
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
            
        ags_path = tmp_path.replace(".xlsx", ".ags")
        
        ags_service.convert_to_ags(tmp_path, ags_path)
        
        from fastapi.responses import FileResponse
        return FileResponse(ags_path, filename=file.filename.replace(".xlsx", ".ags"),
                            media_type="text/plain",
                            background=ags_service.cleanup_task(tmp_path, ags_path))
    except Exception as e:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
             os.remove(tmp_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/parse")
@app.post("/api/parse")
async def parse_ags_file(file: UploadFile = File(...)):
    if not file.filename.endswith('.ags'):
        raise HTTPException(status_code=400, detail="Must be an .ags file")
        
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ags") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
            
        parsed_data = ags_service.get_parsed_data(tmp_path)
        strat_data = ags_service.get_stratigraphy_data(tmp_path)
        
        return {
            "parsed_data": parsed_data,
            "stratigraphy": strat_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)

@app.post("/save")
@app.post("/api/save")
async def save_ags_file(data: Dict[str, Any]):
    try:
        tables_data = data.get("tables", {})
        filename = data.get("filename", "edited.ags")
        
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".ags")
        os.close(tmp_fd)
        
        ags_service.save_parsed_data(tables_data, tmp_path)
        
        from fastapi.responses import FileResponse
        return FileResponse(tmp_path, filename=filename,
                            media_type="text/plain",
                            background=ags_service.cleanup_task(tmp_path, tmp_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all(path_name: str):
    return {"error": "Path not found", "path": path_name}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
