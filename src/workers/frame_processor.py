import asyncio

from ..services.context_manager import ContextManager
from ..core.aggrigator import Aggregator
from sqlalchemy.orm import Session

def frame_processor(threshold:dict,queue,match_queue:asyncio.Queue,context:ContextManager,session_id,stop_event,db:Session):
    aggregator = Aggregator(threshold)
    while not stop_event.is_set():
        try:
            frame = queue.get(timeout=1)
        except:
            continue
        embedding = context.embedding_service.embed_frame(frame)
        results = context.vector_db.search(embedding)
        aggregator.update(results,db)
        matches = aggregator.get_top_matches()
        if matches:
            for match in matches:
                match_queue.put_nowait({"session_id":session_id,"match":match})