import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ..workers.upload_worker import check_uploaded_video


WATCH_DIR = r"D:\Programming\Python\Projects\VideoDect\TestData"

class VideoHandler(FileSystemEventHandler):
    def __init__(self,embedding_service,match_queue):
        self.embedding_service = embedding_service
        self.match_queue = match_queue
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith((".mp4", ".mkv", ".avi")):
            print(f"[Watcher] New video detected: {event.src_path}")
            worker_watcher(event.src_path,self.embedding_service,self.match_queue)


def start_watcher(embedding_service,match_queue):
    event_handler = VideoHandler(embedding_service,match_queue)
    observer = Observer()
    observer.schedule(event_handler,WATCH_DIR,recursive=False)
    observer.start()
    print(f"[Watcher] Watching folder: {WATCH_DIR}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def worker_watcher(path,embedding_service,match_queue):
    video_worker = threading.Thread(
        target=check_uploaded_video,
        args=(path,embedding_service,match_queue)
        )
    video_worker.start()
