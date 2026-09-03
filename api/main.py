import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(title="File Serving API")

FILES_DIR = os.path.join(os.path.dirname(__file__), "..", "files")

FILE_MAP = {
    "1kb": "file_1kb.bin",
    "10kb": "file_10kb.bin",
    "1mb": "file_1mb.bin",
    "10mb": "file_10mb.bin",
    "100mb": "file_100mb.bin",
}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/files/{size}")
def serve_file(size: str):
    filename = FILE_MAP.get(size)
    if not filename:
        raise HTTPException(status_code=400, detail=f"Invalid size. Choose: {list(FILE_MAP.keys())}")

    filepath = os.path.join(FILES_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found. Run generate_files.py first.")

    return FileResponse(filepath, media_type="application/octet-stream", filename=filename)
