# Data

## Layout

```
data/
├── raw_data/      # Kaggle 原始数据（git 忽略，体积大）
│   ├── train.jsonl      # 11.3 GB（已下载）
│   └── train.jsonl.zip  # 2.0 GB
└── processed/     # 预处理产物（parquet shards，git 忽略）
```

`raw_data/` 中还需要（可用 `scripts/download_data.py` 下载）：

- `test.jsonl` — 测试会话（预测对象）
- `sample_submission.csv` — 提交样例

## 原始数据格式（train.jsonl）

每行一个会话，JSON 对象：

```json
{
  "session": 123,
  "locale": "DE",
  "events": [
    {"aid": 0, "ts": 1680120000, "type": "clicks"},
    {"aid": 1, "ts": 1680120010, "type": "carts"}
  ]
}
```

- `session`: 会话 id
- `locale`: 国家/地区（train 中有的行缺失该字段）
- `events[]`: 会话内交互序列，按 `ts` 升序
  - `aid`: 商品 id（1 ~ 1.85M）
  - `ts`: Unix 时间戳（秒）
  - `type`: `clicks` | `carts` | `orders`

## 规模（train）

- 会话数：约 12.9M
- 事件数：约 2.63 亿
- 商品数：约 185 万

## 处理约定

- `scripts/prepare_data.py` 将 `train.jsonl` 展平为长表
  `(session, aid, ts, type, locale)` 并分片存储为 parquet。
- 所有下游脚本默认从 `data/processed/events/events_XXXX.parquet` 读取。
- 原始数据与预处理产物均不提交到 git。
