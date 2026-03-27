from collections import defaultdict
from ..db.models import Video
from sqlalchemy.orm import Session
class Aggregator:
    def __init__(self):
        self.stats = defaultdict(list)

    def update(self,result,db:Session):

        metadatas = result.get("metadatas",None)
        distances = result.get("distances",None)
        if metadatas and distances:
            for dis,res in zip(distances[0],metadatas[0]):
                video_id = res.get("video_id",None)
                score = 1 - dis
                old_stat = self.stats.get(video_id,None)
                if old_stat:
                    old_stat["total_score"] += score
                    old_stat["count"] += 1
                else:
                    video = db.query(Video).filter(Video.id==video_id).first()
                    self.stats[video_id] = {
                        "url":video.url,
                        "total_score":score,
                        "count":1
                    }
    def get_top_matches(self,threshold_count:int=30,threshold_score:float=2.1):
        return sorted([{"video_id":vid,**res} for vid,res in self.stats.items() if res.get("total_score",0) > threshold_score and res.get("count") >= threshold_count],key=lambda x:x["total_score"])
    


