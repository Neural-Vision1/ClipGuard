import cv2
import yt_dlp
import time

ydl_opts = {
    'format': 'best[ext=mp4]',
    'quiet': True,
    'no_warnings': True,
}


def stream_frame(video_url,interval):
    last_time = 0
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        url = info.get('url')
    capture = cv2.VideoCapture(url)
    while True:
        grabbed,frame = capture.read()
        if not grabbed:
            break
        current_time = time.perf_counter()
        if current_time - last_time >= interval:
            gray_scaled = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
            last_time = current_time
            yield gray_scaled
