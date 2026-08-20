from pathlib import Path
import json
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "data/raw_data/train.jsonl"
OUTPUT = ROOT / "data/processed/events"
OUTPUT.mkdir(
    parents=True,
    exist_ok=True
)
# 一个parquet保存多少event
SHARD_SIZE = 400_000
buffer = []
shard_id = 0
def flush():
    global buffer, shard_id
    if len(buffer) == 0:
        return
    table = pa.Table.from_pylist(buffer)
    path = OUTPUT / f"event_{shard_id:04d}.parquet"
    pq.write_table(
        table,
        path,
        compression="snappy"
    )
    print(
        f"write {path}, rows={len(buffer)}"
    )
    buffer.clear()
    shard_id += 1



with open(INPUT,"r") as f:
    for idx,line in enumerate(f):
        session = json.loads(line)
        current_events=session["events"]
        sid = session["session"]
        if (len(buffer)+len(current_events))>SHARD_SIZE:
            flush()
        if len(current_events) > SHARD_SIZE:
            raise ValueError(
                "single session larger than shard size"
                )
        for event in session["events"]:
            buffer.append(
                {
                    "session":sid,
                    "aid":event["aid"],
                    "ts":event["ts"],
                    "type":event["type"]
                }
            )
        if idx % 100000 ==0:
            print(
                "processed",
                idx
            )
flush()
print("done")