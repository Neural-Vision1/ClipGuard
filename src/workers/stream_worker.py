from ..utils.stream_reader import stream_frame
from ..services.context_manager import ContextManager
from ..core.live_memory import LiveMemoryIndex

def start_stream_worker(video_url,interval,context:ContextManager,live_memory:LiveMemoryIndex):
    frame_no = 0
    frames = stream_frame(video_url,interval)
    for frame in frames:
        embedding = context.embedding_service.embed_frame(frame)
        frame_no+=1
        live_memory.add_embeddings(embedding,frame_no)
    