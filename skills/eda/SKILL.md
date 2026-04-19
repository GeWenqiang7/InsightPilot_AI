---
name: eda
description: 运行独立 EDA workflow。适用于从原始表格数据生成结构化数据体检结果、LLM可消费摘要和KG候选关系。
---

# EDA Skill

## 何时使用
- 用户要先做数据体检、缺失/异常/分布/相关性分析。
- 需要给下游 FE/Model 提供 `eda_for_llm.json`。

## 输入
- `data_path` (必需)
- `target` (可选)
- `problem_type` (可选: classification/regression/clustering)
- `output_dir` (可选)

## 输出
- `eda_result.json`
- `eda_for_llm.json`
- `kg_candidates`（在结果内或单独文件）

## 执行约定
1. 读取数据并校验 schema。
2. 调用 EDA tool 生成完整与压缩结果。
3. 将结果写入 `output/runs/<run_id>/eda/`。
4. 返回给调用方关键摘要（行列数、风险特征、可建模性）。
