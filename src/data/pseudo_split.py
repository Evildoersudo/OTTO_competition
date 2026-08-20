"""
将pseudo_future切分为train(hist+gt)和valid(hist+gt)
"""

from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import pyarrow.compute as pc
import random

ROOT = Path(__file__).resolve().parents[2]
EVENT_DIR = ROOT / "data/processed/events"
OUT_DIR = ROOT / "data/processed"
FUTURE_DIR = OUT_DIR / "pseudo_future"

RANKER_TRAIN=OUT_DIR/"ranker_train"
LOCAL_VALID=OUT_DIR/"local_valid"

for d in [
    RANKER_TRAIN/"hist",
    RANKER_TRAIN/"gt",
    LOCAL_VALID/"hist",
    LOCAL_VALID/"gt"
]:
    d.mkdir(
        parents=True,
        exist_ok=True
    )
def hist_gt_cut(df,rng):
    hist,gt=[],[]
    for sid,group in df.groupby("session"):
        if len(group)<2:
            continue
        group=group.sort_values("ts")
        events=group.to_dict("records")
        cut=rng.randint(1,len(group)-1)
        hist.extend(events[:cut])
        gt.extend(events[cut:])
    #将list拼接为dataframe
    hist=pd.DataFrame(hist)
    gt=pd.DataFrame(gt)
    return hist,gt
    

# 先从pseudo_future提取session_list 进行随机切分
session_set=set()
for file in sorted(FUTURE_DIR.glob("*.parquet")):
    table=pq.read_table(file,columns=["session"])
    sessions=table["session"].to_pylist()
    session_set.update(sessions)
#随即划分session
split_rng=random.Random(42)
hist_gt_rng=random.Random(189)
session_set=list(session_set)
split_rng.shuffle(session_set)#原地随机打乱顺序
split=int(len(session_set)*0.8)
ranker_sessions=set(session_set[:split])
valid_sessions=set(session_set[split:])
#根据session id过滤event

#重新扫描pseudo_future
for i,file in enumerate(sorted(FUTURE_DIR.glob("*.parquet"))):
    df=pq.read_table(file).to_pandas()
    ranker_df=df[df.session.isin(ranker_sessions)]
    valid_df=df[df.session.isin(valid_sessions)]
    #session内部hist/gt切分
    ranker_df=ranker_df.sort_values(["session","ts"])#按照session和ts进行排序
    valid_df=valid_df.sort_values(["session","ts"])
    ranker_hist,ranker_gt=hist_gt_cut(ranker_df,hist_gt_rng)
    valid_hist,valid_gt=hist_gt_cut(valid_df,hist_gt_rng)
    #保存为parquet
    ranker_hist.to_parquet(RANKER_TRAIN/"hist"/f"ranker_hist_{i:04d}.parquet",index=False)
    ranker_gt.to_parquet(RANKER_TRAIN/"gt"/f"ranker_gt_{i:04d}.parquet",index=False)
    valid_hist.to_parquet(LOCAL_VALID/"hist"/f"valid_hist_{i:04d}.parquet",index=False)
    valid_gt.to_parquet(LOCAL_VALID/"gt"/f"valid_gt_{i:04d}.parquet",index=False)
    print(i,end=" ",flush=True)