from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq
import pyarrow.compute as pc

"""
hist_event/   = 所有会话截止前的事件   → 召回的"输入材料"
gt_event/     = 所有会话截止后的事件   → 评估的"标准答案"
valid_session = 哪些会话参与打分       → 评估的"范围清单"
"""


ROOT=Path(__file__).resolve().parents[2]
EVENTS_DIR=ROOT/"data"/"processed"/"events"
HIST_DIR=ROOT/"data"/"processed"/"hist_event"# 召回输入
GT_DIR=ROOT/"data"/"processed"/"gt_event"# 评估标签
#由于此处对train进行了valid切分，时间跨度在28天左右，对后7天的数据进行切分作为validation，但只将“有历史有答案的会话”作为validation
#如果是只有后7天的会话，或者只有前21天的会话，不放在valid的范围内，也不参与训练 故VALID_EVENT为一个会话是否有效的标签
VALID_DIR=ROOT/"data"/"processed"/"VALID_event"#评估范围
PROCESSED_DIR=ROOT/"data"/"processed"
MS_PER_DAY = 86_400_000   # 注意你的 ts 是毫秒！
VALID_DAYS = 7

for r in [HIST_DIR,GT_DIR,VALID_DIR]:
    r.mkdir(parents=True,exist_ok=True)

# phase1 只读ts列，算cutoff
max_ts=0
for p in sorted(EVENTS_DIR.glob("*.parquet")):
    #read_table返回的是一个表格对象，需要再进行索引，取到一个数组对象，但不是python原生支持，需要as_py转为python原生对象
    shard_max=pc.max(pq.read_table(p,columns=["ts"])["ts"]).as_py() 
    max_ts=max(max_ts,shard_max)
cut_off=max_ts-MS_PER_DAY*VALID_DAYS
print(f"max_ts={max_ts} cutoff={cut_off}")

# phase2 逐片切分
for i,q in enumerate(sorted(EVENTS_DIR.glob("*.parquet"))):
    df=pq.read_table(q,columns=["session","aid","ts","type"]).to_pandas()
    hist=df[df["ts"]<cut_off]#历史：所有召回/特征的唯一输入
    gt=df[df["ts"]>=cut_off]#未来：唯一评估依据
    hist.to_parquet(HIST_DIR/f"event_{i:04d}.parquet",index=False)#index=False保存时不写入 Pandas 的行索引，节省存储空间。
    gt.to_parquet(GT_DIR/f"event_{i:04d}.parquet",index=False)
    #片内有效会话
    #片内有效会话：既有历史又有 gt（因为会话不跨片，片内交集=全局交集）
    valid=pd.DataFrame({"session":sorted(set(hist["session"])&set(gt["session"]))})#转换为只有一列session的dataframe
    valid.to_parquet(VALID_DIR/f"event_{i:04d}.parquet",index=False)
    del df,hist,gt,valid
    print(i,end=" ",flush=True)

#phase3 合并有效会话 
#drop_duplicates 去除重复行，sort_values实现按照session_id进行排列，reset_index实现对排序后的行重新分配索引，如果不执行，则会将旧索引作为新的一列保留下来
valid=pd.concat([pd.read_parquet(p) for  p  in sorted(VALID_DIR.glob("*.parquet")) ],ignore_index=True).drop_duplicates().sort_values("session").reset_index(drop=True)
valid.to_parquet(PROCESSED_DIR/"valid_sessions.parquet",index=False)
print("valid session",len(valid))  