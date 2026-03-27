from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active = {}
    async def connect(self,session_id,ws:WebSocket):
        await ws.accept()
        self.active[session_id] = ws
    async def send(self,session_id:str,data:dict):
        ws = self.active.get(session_id,None)
        if ws:
            ws.send_json(data)

