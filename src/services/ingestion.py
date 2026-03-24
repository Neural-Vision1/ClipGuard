from datetime import datetime

from sqlalchemy.orm import Session

from ..utils.videos import extract_frames
from ..utils.logger import logging
from ..utils.file_handeling import download,cleanup
from .embedding import EmbeddingService
from ..db.chromadb_client import VectorDB
from ..db.models import Video


def process_video(video_path:str,video_id:str,embedding_service:EmbeddingService,vector_db:VectorDB):
    logging.debug("Processing Video")
    frames = extract_frames(video_path=video_path)
    logging.debug(f"Framed Video : {len(frames)}")
    embedded_vector = embedding_service.embed_frames(frames)
    logging.debug(f"Embedded : {len(embedded_vector)} | {embedded_vector[0].shape}")
    metadata = []
    for i,_ in enumerate(embedded_vector):
        metadata.append({
            "video_id":video_id,
            "timestamp":i
        })
    logging.debug(f"To be insertd into vector db")
    vector_db.add_embeddings(embedded_vector,metadata)
    logging.debug(f"Inserted to chroma  ")

def upsert_video(file,db:Session):
    existing = db.query(Video).filter(Video.id == file["video_id"]).first()
    if existing:
        return existing,False
    new_video = Video(
        id = file["video_id"],
        url = file["url"],
        ingested = False
    )
    db.add(new_video)
    db.commit()
    db.refresh(new_video)
    return new_video,True


def sync_imagekit_files(db,files):
    new_videos = []
    for file in files:
        video,is_new = upsert_video(file,db)
        if is_new:
            new_videos.append(video)
    return new_videos

def run_ingestion(db:Session,embedding_survice,vector_db):
    videos = db.query(Video).filter(Video.ingested == False).all()
    logging.debug(f"Total Videos found : {len(videos)}")
    for video in videos:
        logging.debug(f"Video Url : {video.url}")
        path = download(video.url)
        try:
            process_video(path,video.id,embedding_survice,vector_db)
            video.ingested = True
            video.ingested_at = datetime.utcnow()
            db.commit()
        except Exception as e:
            db.rollback()
            logging.debug(f"Video error : {e}")
        finally:
            cleanup(path)