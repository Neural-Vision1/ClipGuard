import uuid
from threading import Event
active_session = {}

def create_session():
    session_id = str(uuid.uuid4())
    active_session[session_id] = {
        "thread":None,
        "live_memory":None,
        "id":session_id,
        "url":None,
        "stop_event":Event()
    }
    return active_session[session_id]


def stop_session(session_id):
    session = active_session.get(session_id,None)
    if session:
        session["stop_event"].set()
        return True
    return False

def get_session(session_id:str):
    return active_session[session_id]

def delete_session(session_id:str):
    return active_session.pop(session_id,None)

def get_active_sessions():
    return [k for k in active_session.keys()]


def get_all_live_streams():
    return [(sid,data["live_memory"]) for sid,data in active_session.items()]