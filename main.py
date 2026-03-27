import os
from queue import Queue

from sqlalchemy.orm import Session
from fastapi import FastAPI,UploadFile,Depends,File, WebSocket, WebSocketDisconnect
from fastapi.exceptions import HTTPException

from src.db.models import Video
from src.services.ingestion import sync_imagekit_files,run_ingestion
from src.db.deps import get_db
from src.services.imagekit_instance import list_all_files
from src.services.query import query_video
from src.db.database import Base,engine
from src.utils.file_handeling import save_temp,cleanup
from src.utils.logger import logging
from .src.core.session_maker import create_session,delete_session
from .src.workers.stream_worker import start_stream_worker
from .src.services.context_manager import ContextManager

from .api.model import StartStreamRequestSchema



app = FastAPI()
Base.metadata.create_all(bind = engine)
context=ContextManager()

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



# Stream Manager

@app.post("/start_stream")
def start_stream(request:StartStreamRequestSchema,db:Session=Depends(get_db)):
    session = create_session()
    session["queue"] = Queue(maxsize=20)
    start_stream_worker(request.url,request.interval,context,session,db)
    return {
        "status":"session started",
        "session_id":session["id"]
    }

@app.post("/stop-stream/{session_id}")
def stop_stream(session_id:str):
    delete_session(session_id)
    return {
        "status":"session stoped"
        }

@app.websocket("ws/{session_id}")
async def ws_route(ws:WebSocket,session_id:str):
    await context.alert_service.connect(session_id,ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        context.alert_service.active.pop(session_id,None)
    