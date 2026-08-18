# Notebooks

按编号顺序执行；每个 notebook 保持独立可复现（开头加载配置与数据）。

| 编号 | 主题 | 状态 |
| --- | --- | --- |
| 01_eda.ipynb | 探索性数据分析：会话/事件分布、商品 popularity、type 比例、时间跨度、locale | stub |
| 02_baseline.ipynb | popularity baseline 训练与验证、提交文件生成 | 待创建 |
| 03_features.ipynb | 特征工程实验（session 统计、时序特征） | 待创建 |
| 04_ranking.ipynb | GBDT 排序 / 神经网络模型实验 | 待创建 |
| 05_ensemble.ipynb | 集成与后处理 | 待创建 |

约定：

- 大数据量处理尽量复用 `src/otto` 中的函数，避免 notebook 内重复代码。
- 冒烟测试用小样本（如 `--limit 100000` 生成的 parquet），全量跑之前先验证流程。
- 训练日志 / 指标记录到 `logs/`，模型产物到 `models/`，提交文件到 `submissions/`。
