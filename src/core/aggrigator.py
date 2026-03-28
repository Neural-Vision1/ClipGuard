from collections import defaultdict
from ..db.models import Video
from sqlalchemy.orm import Session
class Aggregator:
    def __init__(self,threshold:dict={}):
        self.stats = defaultdict(list)
        self.threshold = threshold

    def update(self,result,db:Session):

        metadatas = result.get("metadatas",None)
        distances = result.get("distances",None)
        if metadatas and distances:
            for dis,res in zip(distances[0],metadatas[0]):
                video_id = res.get("video_id",None)
                score = 1 - dis
                if score>=0.6:
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
    def get_top_matches(self):
        return sorted(
            [{"video_id":vid,"score":res["total_score"]/res["count"],"count":res["count"]} 
             for vid,res in self.stats.items() 
             if res.get("count",0) >= self.threshold.get("count",40) and (res.get("total_score",0)/res.get("count",1000))>= self.threshold.get("score",0.6)],
             key=lambda x:x["count"],reverse=True)
    


