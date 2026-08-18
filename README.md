# OTTO — Multi-Objective Recommender System

Kaggle 竞赛工作区：[OTTO – Multi-Objective Recommender System](https://www.kaggle.com/competitions/otto-recommender-system)

> 根据匿名用户的会话行为序列（点击 / 加购 / 下单），预测该用户接下来会点击、加购、下单的商品。

## 任务概述

| 项目 | 内容 |
| --- | --- |
| 输入 | 匿名会话内的交互序列 `(session, aid, ts, type)`，`type ∈ {clicks, carts, orders}` |
| 输出 | 对每个会话的每个 objective 给出最多 20 个候选商品（可重复利用同一商品的三个预测） |
| 评估指标 | **Recall@20**，对 `clicks / carts / orders` 三个 objective 分别计算后取平均 |
| 训练数据 | `data/raw_data/train.jsonl`（约 1290 万会话 / 2.63 亿事件 / 185 万商品） |

### 提交格式

每会话每 objective 一行，`candidates` 为空格分隔的商品 id 列表（≤ 20 个）：

```csv
session_type,session,candidates
clicks,123,4 5 6 ...
carts,123,4 5 6 ...
orders,123,4 5 6 ...
```

## 目录结构

```
OTTO/
├── README.md                 # 本文件
├── requirements.txt          # Python 依赖
├── pyproject.toml            # 包配置（src 布局，pip install -e .）
├── .gitignore
├── .env.example              # Kaggle 凭据模板（复制为 .env 或写入 ~/.kaggle/kaggle.json）
├── data/
│   ├── README.md             # 数据说明
│   ├── raw_data/             # Kaggle 原始数据（git 忽略，~11 GB）
│   │   ├── train.jsonl
│   │   └── train.jsonl.zip
│   └── processed/            # 预处理产物（parquet shards，git 忽略）
├── configs/
│   └── default.yaml          # 全局默认配置
├── notebooks/
│   ├── 01_eda.ipynb          # EDA
│   └── README.md             # notebook 规划
├── src/otto/                 # 主代码包
│   ├── paths.py              # 路径常量
│   ├── config.py             # 配置加载（YAML + 默认值合并）
│   ├── data/                 # 数据读取 / 预处理
│   ├── features/             # 特征工程
│   ├── models/               # 模型（baseline / 后续模型）
│   ├── training/             # 训练逻辑
│   ├── inference/            # 推理与提交文件生成
│   ├── evaluation/           # Recall@20 等指标
│   └── utils/                # 日志 / IO 等工具
├── scripts/                  # 可执行脚本（从项目根目录运行）
│   ├── download_data.py      # Kaggle API 下载数据
│   ├── prepare_data.py       # jsonl → parquet shards
│   ├── train_baseline.py     # 训练 popularity baseline 并生成提交
│   └── evaluate.py           # 评估提交文件 Recall@20
├── models/                   # 模型产物（git 忽略）
├── submissions/              # 提交文件（git 忽略）
├── logs/                     # 运行日志（git 忽略）
└── tests/                    # 单元测试
```

## 环境搭建

```bash
# 1. 创建虚拟环境（Python >= 3.10）
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

# 2. 安装依赖（以可编辑方式安装本地包，使 `from otto import ...` 可用）
pip install -r requirements.txt
pip install -e .
```

Kaggle 凭据（下载数据用）：将 `KAGGLE_USERNAME` / `KAGGLE_KEY` 写入环境变量，或把 `kaggle.json` 放到 `~/.kaggle/`。

## 快速开始

```bash
# 1.（可选）下载数据（train.jsonl 已在 data/raw_data/ 中时可跳过）
python scripts/download_data.py

# 2. 小规模冒烟测试：jsonl → parquet
python scripts/prepare_data.py --limit 100000 --shard-sessions 50000 --output-dir data/processed/smoke

# 3. 训练 popularity baseline 并生成提交（用冒烟数据验证流程）
python scripts/train_baseline.py --input data/processed/smoke --num-sessions 10000

# 4. 用验证集事件评估提交文件的 Recall@20
python scripts/evaluate.py --predictions submissions/submission_popularity.csv --ground-truth data/processed/smoke/events_0000.parquet

# 5. 跑测试
pytest
```

完整数据处理（约 11 GB，耗时较长，建议后台执行）：

```bash
python scripts/prepare_data.py --shard-sessions 500000 --output-dir data/processed/events
```

## 标准流水线

1. **数据准备** — `scripts/prepare_data.py` 将 `train.jsonl` 展平为长表并分片存 parquet。
2. **切分** — 按时间切分验证集（`otto.data.preprocessing.split_by_time`，默认最后 7 天为验证）。
3. **特征工程** — `otto/features/`（session 统计、popularity、时序特征等）。
4. **候选生成** — 召回阶段（popularity / co-occurrence / 序列模型 / 检索）。
5. **排序** — GBDT（LightGBM/XGBoost）或神经网络对候选重排。
6. **评估** — `otto.evaluation.metrics` 实现官方 Recall@20（含三个 objective 平均）。
7. **提交** — `otto.inference.predict.predictions_to_submission` 输出官方格式。

## 后续迭代方向（参考公开高分方案）

- 用 `polars` 加速大数据量处理；`train.jsonl` 转 parquet 后可用 Arrow 内存映射。
- 召回：session 内共现 / 图方法 / 向量检索（如 `two-tower`、`item2vec`）。
- 排序：以 Recall@20 为目标构造候选对，LightGBM 排序；特征包括会话长度、时间差、type 序列等。
- 直接法：用候选商品得分矩阵乘法（热门高分方案的“矩阵乘法”思路）做近似检索。
- 集成与后处理：三个 objective 共享候选池 + 各自排序；对低频 session 回退到 popularity。

## 参考链接

- [竞赛主页](https://www.kaggle.com/competitions/otto-recommender-system)
- [官方评估脚本（Recall@20）](https://www.kaggle.com/code/otto/recall-metric)
- [竞赛论坛](https://www.kaggle.com/competitions/otto-recommender-system/discussion)
