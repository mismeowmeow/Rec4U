import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict

from fastapi import UploadFile, BackgroundTasks, APIRouter
from moviepy import VideoFileClip

# ---------------------------
# Recordings folder
# ---------------------------
BASE_DIR = Path(__file__).resolve().parent
RECORDINGS_DIR = BASE_DIR / "recordings"
RECORDINGS_DIR.mkdir(exist_ok=True)

router = APIRouter()

# ---------------------------
# Allowed video types
# ---------------------------
ALLOWED_MIME_TYPES = ["video/mp4", "video/webm", "video/quicktime", "video/x-msvideo"]
ALLOWED_EXTENSIONS = ["mp4", "webm", "mov", "avi"]


# ---------------------------
# Generate unique filename
# ---------------------------
def generate_filename(original_name: str) -> str:
    ext = original_name.split(".")[-1].lower()
    unique_id = uuid.uuid4().hex
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"{timestamp}_{unique_id}.{ext}"


# ---------------------------
# Validate uploaded video
# ---------------------------
def validate_video(file: UploadFile):
    ext = file.filename.split(".")[-1].lower()

    if file.content_type not in ALLOWED_MIME_TYPES or ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported video type: {file.content_type}")

    return True


# ---------------------------
# Save video file (async)
# ---------------------------
async def save_video_file(file: UploadFile) -> str:
    validate_video(file)

    filename = generate_filename(file.filename)
    filepath = RECORDINGS_DIR / filename

    with open(filepath, "wb") as buffer:
        buffer.write(await file.read())

    return str(filepath)


# ---------------------------
# Extract video metadata
# ---------------------------
def extract_video_metadata(file_path: str) -> Dict:
    clip = VideoFileClip(file_path)

    duration = round(clip.duration, 2)  # seconds
    width, height = clip.size
    resolution = f"{width}x{height}"
    file_size = os.path.getsize(file_path)

    clip.close()

    return {
        "duration": duration,
        "resolution": resolution,
        "file_size": file_size,
    }


# ---------------------------
# Delete video file
# ---------------------------
def delete_video_file(filepath: str) -> bool:
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False


# ---------------------------
# Background task: process recording
# ---------------------------
def background_process(file_path: str, db_save_callback):
    """
    Extract metadata and save to DB.
    `db_save_callback` is a function that writes info to your Recording table.
    """
    metadata = extract_video_metadata(file_path)
    db_save_callback(file_path, metadata)


# ---------------------------
# Entry function for FastAPI route
# ---------------------------
async def process_recording(file: UploadFile, background_tasks: BackgroundTasks, db_save_callback):
    """
    Save the file immediately and schedule metadata extraction in background.
    Returns file path instantly.
    """
    file_path = await save_video_file(file)
    background_tasks.add_task(background_process, file_path, db_save_callback)
    return {"file_path": file_path, "status": "processing"}
