from ..services.context_manager import Context
from ..core.aggrigator import Aggregator
from sqlalchemy.orm import Session

def frame_processor(queue,context:Context,session_id,stop_event,db:Session):
    aggregator = Aggregator()
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
            context.alert_service.send(session_id,{
                "type":"MATCH",
                "matches":matches
            })