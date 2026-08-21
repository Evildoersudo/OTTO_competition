import pandas as pd
from collections import defaultdict
from itertools import combinations
TYPE_WEIGHT={

"clicks":1,

"carts":3,

"orders":6

}
#生成共现矩阵
def build_covis_matrix(df:pd.DataFrame):
    conivs=defaultdict(lambda:defaultdict(int))#创建一个嵌套字典
    for session,group in df.groupby("session"):
        group=group.sort_values("ts")
        events=list(zip(group.aid,group.type))
        for (aid1,t1),(aid2,t2) in combinations(events,2):#取events中不重复的两个元素即元组
            score=TYPE_WEIGHT[t1]*TYPE_WEIGHT[t2]
            conivs[aid1][aid2]+=score
            conivs[aid2][aid1]+=score
    return conivs

def conivs_recall(session_items,conivs,top_k=50):
    scores=defaultdict(int)
    for item in session_items:
        neighbors=conivs[item]
        for aid,score in neighbors.items():
            scores[aid]+=score
    results=sorted(score.item(),key=lambda x:x[1],reverse=True)
    return results[:top_k]