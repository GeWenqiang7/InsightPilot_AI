---
name: fe
description: 运行独立 FE workflow。基于 EDA 摘要与任务类型，由 LLM 生成可执行特征工程方案并输出特征产物。
---

# FE Skill

## 何时使用
- 用户要做特征工程规划或迭代。
- 已有 EDA 结果，需快速生成 FE plan。

## 输入
- `eda_for_llm.json` (必需)
- `problem_type` (必需)
- `model_candidates` (可选)
- `output_dir` (可选)

## 输出
- `fe_plan.json`
- `feature_matrix.parquet`（如执行落地）

## 执行约定
1. 校验 EDA 摘要存在并读取。
2. 调用 FE tool 生成结构化 plan。
3. 可选执行 plan 生成特征矩阵。
4. 将结果写入 `output/runs/<run_id>/fe/`。
