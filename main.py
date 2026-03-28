import os
from queue import Queue
import glob
import uuid

from sqlalchemy.orm import Session
from fastapi import FastAPI,UploadFile,Depends,File, WebSocket, WebSocketDisconnect
from fastapi.exceptions import HTTPException
import asyncio

from src.db.models import Video
from src.services.ingestion import sync_imagekit_files,run_ingestion
from src.db.deps import get_db
from src.services.imagekit_instance import list_all_files
from src.services.query import query_video
from src.db.database import Base,engine
from src.utils.file_handeling import save_temp,cleanup
from src.utils.videos import extract_frames
from src.utils.logger import logging
from src.core.session_maker import create_session,delete_session,get_active_sessions,stop_session
from src.workers.stream_worker import start_stream_worker
from src.services.context_manager import ContextManager

from api.model import StartStreamRequestSchema



app = FastAPI()
Base.metadata.create_all(bind = engine)
context=ContextManager()
match_queue = asyncio.Queue()

@app.post("/query")
async def load_from_imagekit(threshold_count:int,threshold_score:float,file:UploadFile=File(...),db = Depends(get_db)):
    if not file.filename.endswith((".mp4", ".mov", ".avi")):
        raise HTTPException(status_code=400, detail="Invalid video format")
    path = None
    try:
        path = await save_temp(file.file)
        logging.debug("File loaded to local")
        results = query_video(path,context,db=db,threshold_count=threshold_count,threshold_score=threshold_score)
        logging.debug("Result found")
        return {
            "status": "success",
            "matches": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if path:
            cleanup(path)

    

@app.post("/sync-imagekit")
def sync_imagekit(db = Depends(get_db)):
    all_files = list_all_files()
    newly_synced = sync_imagekit_files(db,all_files) 
    return {
        "total_recieved":len(all_files),
        "new_added": len(newly_synced),
    }  

@app.post("/run-ingestion")
def run_synced_ingestion(db = Depends(get_db)):
    run_ingestion(db,context)
    return {
        "status": "ingestion complete",
    }

@app.post("/sync-ingest")
def sync_ingest(db = Depends(get_db)):
    all_files = list_all_files()
    newly_synced = sync_imagekit_files(db,all_files)
    run_ingestion(db,context)
    return {
        "total_recieved":len(all_files),
        "new_added": len(newly_synced),
        "status": "ingestion complete",
    }  
@app.post("/cleanup")
def cleanup_dbs(db:Session=Depends(get_db)):
    context.vector_db.clear_collection()
    db.query(Video).delete(synchronize_session=False)
    db.commit()
    return {"status":"cleaned up"}

@app.post("/local-sync-ingest")
def local_sync_ingest(dir_location:str=r"D:\Programming\Python\Projects\VideoDect\TestData",db:Session=Depends(get_db)):
    new_added = 0
    dir_path = dir_location + r"\*.mp4"
    file_paths = glob.glob(dir_path,recursive=True)
    for path in file_paths:
        exists = db.query(Video).filter(Video.url==path).first()
        if exists and exists.ingested:
            continue
        elif not exists:
            video_id = str(uuid.uuid4())
            new_video = Video(
                id=video_id,
                url=path,
                ingested = False
            )
            db.add(new_video)
            db.commit()
            new_added +=1
        else:
            video_id =exists.id
            new_added +=1
        metadatas = []
        
        frames = extract_frames(path,3)
        for i in range(len(frames)):
            metadatas.append({
                "video_id":video_id,
                "timestamp":i
            })
        embeddings = context.embedding_service.embed_frames(frames)
        context.vector_db.add_embeddings(embeddings,metadatas)
        ingested_video = db.query(Video).filter(Video.id==video_id).first()
        ingested_video.ingested = True
        db.commit()
        db.refresh(ingested_video)
    return {
        "status": "successful",
        "total_recieved":len(file_paths),
        "new_added": new_added,
        
    }

        
        



# Stream Manager

@app.post("/start_stream")
async def start_stream(request:StartStreamRequestSchema,db:Session=Depends(get_db)):
    session = create_session()
    session["queue"] = Queue(maxsize=20)
    threshold = {
        "count":request.count,
        "score":request.score
    }
    await start_stream_worker(request.url,threshold,match_queue,request.interval,context,session,db)
    return {
        "status":"session started",
        "session_id":session["id"]
    }

@app.post("/stop-stream/{session_id}")
def stop_stream(session_id:str):
    session = stop_session(session_id=session_id)
    return {
        "status":"session stopped",
        "session_id":session_id if session else None
        }

@app.websocket("ws/{session_id}")
async def ws_route(ws:WebSocket,session_id:str):
    await context.manager.connect(session_id,ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        context.manager.active.pop(session_id,None)

@app.on_event("startup")
async def event_dispatcher():
    asyncio.create_task(dispatch_events())   

async def dispatch_events():
    while True:
        event = await match_queue.get()
        logging.debug(f"Found : {event}")
        await context.manager.send(event["session_id"],event["match"])

#temp
@app.get("/show-sessions")
def show():
    return get_active_sessions()