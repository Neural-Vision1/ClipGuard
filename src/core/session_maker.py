import uuid
from threading import Event
active_session = {}

def create_session():
    session_id = str(uuid.uuid4())
    active_session[session_id] = {
        "threads":[],
        "queue":None,
        "id":session_id,
        "stop_event ":Event()
    }
    return active_session[session_id]


def stop_session(session_id):
    session = active_session.get(session,None)
    if session:
        session["stop_event"].set()

def get_session(session_id:str):
    return active_session[session_id]

def delete_session(session_id:str):
    return active_session.pop(session_id,None)