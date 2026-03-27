from .frame_processor import frame_processor
from .frame_producer import frame_producer
import threading
frame_producer()
def start_stream_worker(video_url,interval,context,session,db):
    queue = session["queue"]
    stop_event = session["stop_event"]
    session_id = session["id"]
    chunker = threading.Thread(
        target=frame_producer,
        args=(video_url,interval,queue,stop_event),
        daemon=True
    )
    processor = threading.Thread(
        target=frame_processor,
        args=(queue,context,session_id,stop_event,db),
        daemon=True
    )
    chunker.start()
    processor.start()
    session["threads"].extend([chunker,processor])