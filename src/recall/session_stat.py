
"""
session_history 针对session中每个aid进行统计
1.生成行为one-hot
2.计算每个session中每种event的个数
3.计算每个session中每个aid的每种event的个数
4.计算每个session中每个aid最近一次出现距离session尾部的距离
5.ts_diff_pre-计算每个session中每个event和上一个event的时间间隔
6.ts_diff_post-计算每个session中每个event和下一个event的时间间隔
7.对ts_diff_pre和ts_diff_post按照aid计算mean,即这个 aid 在该 session 中出现时，与前一个行为时间间隔的平均值。或者这个 aid 出现后，到下一次行为之间的平均间隔。

最终(session,aid)得到
session aid
isin_0_count	出现总次数
isin_0_clicks	点击次数
isin_0_carts	加购次数
isin_0_orders	购买次数
isin_0_rank	最近一次出现距离 session 尾部的位置
isin_0_ts_diff_pre	与前一个 event 的平均时间差
isin_0_ts_diff_post	与后一个 event 的平均时间差


"""

from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
INPUT_DIR = (
        ROOT /
        "data/processed/ranker_train/hist"
    )
OUTPUT_DIR = (
        ROOT /
        "data/processed/features/ranker_train"
    )
HISTORY_DIR = (
        OUTPUT_DIR /
        "session_history"
    )
SESSION_DIR = (
        OUTPUT_DIR /
        "session_feature"
    )
EVENTS_DIR=(
        ROOT /
        "data/processed/events"
    )

def build_session_history(df:pd.DataFrame):
    results=[]
    for session,group in df.groupby("session"):
        group=group.sort_values("ts")
        #行为统计
        group["clicks"]=(group["type"]=="clicks").astype("int16")
        group["carts"]=(group["type"]=="carts").astype("int16")
        group["orders"]=(group["type"]=="orders").astype("int16")
        #平均时间差
        group["aid_ts_diff"]=(group.groupby("aid")["ts"].diff().fillna(0))/1000#按照每个aid计算其event前后时间差
        #最近位置
        rank_list=np.arange(0,len(group))
        group["rank"]=rank_list[::-1]
        #聚合到aid
        group["count"]=1
        aid_feat=(group.groupby("aid").agg(
            isin_0_count=("count","sum"),  #该物品在该会话中出现的次数
            isin_0_clicks=("clicks","sum"),    #点击次数
            isin_0_carts=("carts","sum"),      #加购次数
            isin_0_orders=("orders","sum"),      #购买次数
            isin_0_first_rank=("rank","max"),  #第一次出现的位置
            isin_0_last_rank=("rank","min"),   #最后一次出现的位置
            # isin_0_first_ts=("ts","min"),      #第一次出现的时间
            # isin_0_last_ts=("ts","max"),   #最后出现的时间
            isin_0_aid_gap_mean=("aid_ts_diff","mean"),    #该会话整体时间差均值（广播值，取mean即本身）
            isin_0_aid_gap_min=("aid_ts_diff", "min"),
            isin_0_aid_gap_max=("aid_ts_diff", "max")
        )).reset_index()# 把 aid 从索引变回普通列

        #添加会话标识
        aid_feat["session"]=session
        #收集结果
        results.append(aid_feat)
    final_df=pd.concat(results,ignore_index=True)
    return final_df


"""
针对session整体进行特征统计
输出(session)
统计：
session长度-event数量 Item统计-商品数量、时间行为-session时长+平均事件间隔、最后两次行为时间间隔、session中的行为比例
"""
def build_session_feature(df:pd.DataFrame):
    results=[]
    for session,group in df.groupby("session"):
        group=group.sort_values("ts")
        feat={}
        feat["session"]=session
        #长度
        feat["session_length"]=len(group)#event总数
        feat["unique_aid"]=group.aid.nunique()#不同aid的数量
        #商品重复率
        feat["repeat_ratio"]=(1-feat["unique_aid"]/feat["session_length"])
        #时间
        feat["duration"]=(group.ts.max()-group.ts.min())/1000
        feat["click_count"]=(
            group.type=="clicks"
        ).sum()
        feat["cart_count"]=(
            group.type=="carts"
        ).sum()
        feat["order_count"]=(
            group.type=="orders"
        ).sum()
        #比例
        feat["click_ratio"]=(
            feat["click_count"]
            /
            len(group)
        )
        feat["cart_ratio"]=(
            feat["cart_count"]
            /
            len(group)
        )
        feat["order_ratio"]=(
            feat["order_count"]
            /
            len(group)
        )
        results.append(feat)
    return pd.DataFrame(results)

def main_session_stat_process():
    for d in [HISTORY_DIR,SESSION_DIR]:
        d.mkdir(parents=True,exist_ok=True)
    files = sorted(
        INPUT_DIR.glob("*.parquet")
    )
    for idx,file in enumerate(files):
        print(
            f"processing {idx}/{len(files)}"
        )
        df=pq.read_table(file,columns=["session","aid","ts","type"]).to_pandas()
        history_feat=build_session_history(df)
        history_feat.to_parquet(
            HISTORY_DIR/f"history_{idx:04d}.parquet",index=False
        )
        session_feat=build_session_feature(df)
        session_feat.to_parquet(
            HISTORY_DIR/f"session_{idx:04d}.parquet",index=False
        )
        del df,history_feat,session_feat
    print("done")
if __name__=="__main__":
    for file in EVENTS_DIR.glob("*.parquet"):
        df = pq.read_table(
            file,
            columns=["session"]
        ).to_pandas()

        if df["session"].duplicated().any():
           print(
                "session split detected",
                file
            )
    main_session_stat_process()