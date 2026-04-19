---
name: evaluate
description: 运行独立 Evaluate workflow。对训练结果做指标复盘、风险诊断和改进建议输出。
---

# Evaluate Skill

## 何时使用
- 用户要独立审计模型表现。
- 需要判断是否触发重训。

## 输入
- `model_results.json` (必需)
- `best_model.pkl` (可选)
- `test_data` (可选)
- `output_dir` (可选)

## 输出
- `evaluation.json`
- `risk_flags.json`
- `improvement_actions.json`

## 执行约定
1. 汇总核心指标。
2. 检查低性能/过拟合/数据问题。
3. 生成可执行改进动作和重训建议。
4. 将结果写入 `output/runs/<run_id>/evaluate/`。
