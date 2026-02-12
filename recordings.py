from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from database import get_db
from models import Recording
import os
import shutil
import uuid

router = APIRouter()

@router.post("/upload")
def upload_recording(
    file: UploadFile = File(...),
    name: str = "Recording",
    user_id: int = 1,
    db: Session = Depends(get_db)

):
    os.makedirs("recordings", exist_ok=True)
    file_id = str(uuid.uuid4())
    file_path = os.path.join("recordings", f"{file_id}.mp3")
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    recording = Recording(
        name=name,
        file_path=file_path,
        user_id=user_id
    )
    db.add(recording)
    db.commit()
    db.refresh(recording)
    return {
            "message": "Recording uploaded successfully",
             "file_url": f"/recordings/file/{file_id}.mp3",
                 "recording_id": recording.id
    }
@router.get("/recordings")
def get_recordings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    recordings = db.query(Recording).filter(Recording.owner_id == current_user.id).all()
    return recordings

@router.put("/recordings/{recording_id}")
def rename_recording(
    recording_id: int,
    new_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rec = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.owner_id == current_user.id
    ).first()

    if not rec:
        raise HTTPException(status_code=404, detail="Recording not found")

    rec.original_name = new_name
    db.commit()
    return {"message": "Recording renamed"}

@router.delete("/recordings/{recording_id}")
def delete_recording(
    recording_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rec = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.owner_id == current_user.id
    ).first()

    if not rec:
        raise HTTPException(status_code=404, detail="Recording not found")

    file_path = f"recordings/{rec.filename}"
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(rec)
    db.commit()
    return {"message": "Recording deleted"}

@router.get("/recordings/file/{filename}")
def get_file(filename: str):
    file_path = f"recordings/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)