---
name: model
description: 运行独立 Model workflow。基于特征数据训练候选模型、生成排行榜并选出最优模型。
---

# Model Skill

## 何时使用
- 用户要独立进行训练与模型选择。
- 已完成 FE，想比较多模型效果。

## 输入
- `feature_matrix` (必需)
- `target` (必需)
- `problem_type` (必需)
- `output_dir` (可选)

## 输出
- `model_results.json`
- `leaderboard.json`
- `best_model.pkl`

## 执行约定
1. 数据切分与基础校验。
2. 训练候选模型并记录指标。
3. 选择最优模型并持久化。
4. 将结果写入 `output/runs/<run_id>/model/`。
