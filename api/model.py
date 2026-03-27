from pydantic import BaseModel,Field



class StartStreamRequestSchema(BaseModel):
    url:str = Field(...)
    interval:int = Field(5)
    score:float = Field(2.1)
    count:int = Field(30)
    