from ..utils.stream_reader import stream_frame


def frame_producer(vidoe_url,interval,queue,stop_event):
    sampled = stream_frame(vidoe_url,interval)
    for frame in sampled:
        if stop_event.is_set():
            break   
        try:
            queue.put(frame,timeout=1)
        except:
            continue