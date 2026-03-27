import cv2

def extract_frames(video_path: str, interval=1):
    extracted_frames = []
    video = cv2.VideoCapture(video_path)
    fps_interval = int(video.get(cv2.CAP_PROP_FPS)) * interval
    frame_count = 0
    while True:
        ret, frame = video.read()
        if not ret:
            break

        if frame_count % fps_interval == 0:
            gray_scaled = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            extracted_frames.append(gray_scaled)
        frame_count += 1
    video.release()
    cv2.destroyAllWindows()
    return extracted_frames






