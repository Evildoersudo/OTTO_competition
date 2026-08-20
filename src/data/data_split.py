"""
将数据切分为base_train和pseudo_future
输入数据格式：一行 = 一个session
{
 "session":123456,
 "events":[
    {
      "aid":100,
      "ts":1659300000000,
      "type":"clicks"
    },
    {
      "aid":200,
      "ts":1659300100000,
      "type":"carts"
    }
 ]
}
输出parque数据格式:一行=一个event 
session aid ts type
123456  100 xxx clicks
"""
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import pyarrow.compute as pc


ROOT = Path(__file__).resolve().parents[2]
EVENT_DIR = ROOT / "data/processed/events"
OUT_DIR = ROOT / "data/processed"
BASE_DIR = OUT_DIR / "base_train"
FUTURE_DIR = OUT_DIR / "pseudo_future"

RANKER_TRAIN=OUT_DIR/"ranker_train"
LOCAL_VALID=OUT_DIR/"local_valid"


for d in [
    BASE_DIR,
    FUTURE_DIR
]:
    d.mkdir(
        parents=True,
        exist_ok=True
    )

MS_DAY = 86400000
HOLDOUT_DAYS = 7
# =====================================================
# Pass1:
# 获取max timestamp
# =====================================================

max_ts = 0
for file in sorted(EVENT_DIR.glob("*.parquet")):
    table = pq.read_table(
        file,
        columns=["ts"]
    )
    shard_max = pc.max(
        table["ts"]
    ).as_py()
    max_ts = max(
        max_ts,
        shard_max
    )
print(
    "max_ts:",
    max_ts
)
cutoff = max_ts - HOLDOUT_DAYS*MS_DAY
print(
    "cutoff:",
    cutoff
)
# =====================================================
# Pass2:
# parquet级切分
# =====================================================
for idx,file in enumerate(
    sorted(EVENT_DIR.glob("*.parquet"))
):
    df = pq.read_table(
        file
    ).to_pandas()
    base = df[
        df.ts < cutoff
    ]
    future = df[
        df.ts >= cutoff
    ]
    base.to_parquet(
        BASE_DIR / f"event_{idx:04d}.parquet",
        index=False
    )
    future.to_parquet(
        FUTURE_DIR / f"event_{idx:04d}.parquet",
        index=False
    )
    print(
        idx,
        end=" "
    )
print("done")

