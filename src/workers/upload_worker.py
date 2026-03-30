from collections import defaultdict,deque

import asyncio
import threading

from ..utils.stream_reader import live_video_reader
from ..services.embedding import EmbeddingService
from ..core.session_maker import get_all_live_streams
from ..utils.logger import logging
WINDOW_SIZE = 12
SCORE_THRESHOLD = 0.6
WINDOW_THRESHOLD = 0.7

def check_uploaded_video(path,embedding_service:EmbeddingService,match_queue:asyncio.Queue):
    session_windows = defaultdict(lambda:deque(maxlen=WINDOW_SIZE))
    frames = live_video_reader(path,5)
    for frame in frames:
        embedding = embedding_service.embed_frame(frame)
        for session_id, live_memory in get_all_live_streams():
            scores, _ = live_memory.search(embedding,1)
            logging.debug(f"Uploaded video search score = {scores} and id = {_}")
            best_score = scores[0]
            if best_score > SCORE_THRESHOLD:
                session_windows[session_id].append(1)
            else:
                session_windows[session_id].append(0)
            window = session_windows[session_id]
            if len(window)>=2 and sum(window)>=WINDOW_THRESHOLD:
                match_queue.put_nowait({
                    "stream_id":session_id,
                    "video_path":path,
                    "score":round(sum(window)/WINDOW_SIZE,3)
                })
                session_windows[session_id].clear()
