import cv2
import yt_dlp
import time
import os

# Browser-like headers to avoid bot detection
ydl_opts = {
    'format': 'best[ext=mp4]',
    'quiet': True,
    'no_warnings': True,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    },
}

# Add cookies if COOKIES_FILE is set in environment
cookies_file = os.getenv('YT_COOKIES_FILE')
if cookies_file and os.path.exists(cookies_file):
    ydl_opts['cookiefile'] = cookies_file


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


def live_video_reader(video_path: str, interval=5):
    video = cv2.VideoCapture(video_path)
    fps_interval = int(video.get(cv2.CAP_PROP_FPS)) * interval
    frame_count = 0
    while True:
        ret, frame = video.read()
        if not ret:
            break

        if frame_count % fps_interval == 0:
            gray_scaled = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            yield gray_scaled
        frame_count += 1
    video.release()
    cv2.destroyAllWindows()