from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import shutil
import os

from database import SessionLocal
from models import Recording

router = APIRouter()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# -----------------------
# Upload Recording
# -----------------------
@router.post("/upload")
async def upload_recording(
    title: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_recording = Recording(
        title=title,
        filename=file.filename,
        file_path=file_path,
    )

    db.add(new_recording)
    db.commit()
    db.refresh(new_recording)

    return {"message": "Recording uploaded successfully"}


# -----------------------
# Get All Recordings
# -----------------------
@router.get("/")
def get_recordings(db: Session = Depends(get_db)):
    recordings = db.query(Recording).all()
    return recordings


# -----------------------
# Delete Recording
# -----------------------
@router.delete("/{recording_id}")
def delete_recording(recording_id: int, db: Session = Depends(get_db)):
    recording = db.query(Recording).filter(Recording.id == recording_id).first()

    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    if os.path.exists(recording.file_path):
        os.remove(recording.file_path)

    db.delete(recording)
    db.commit()

    return {"message": "Recording deleted successfully"}