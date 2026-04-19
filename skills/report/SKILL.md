---
name: report
description: 运行独立 Report workflow。聚合上游 artifacts，调用 LLM 生成业务可读报告与 notebook。
---

# Report Skill

## 何时使用
- 用户要把分析过程整理成管理层/技术版交付物。
- 需要统一导出 Markdown/PDF/Notebook。

## 输入
- `eda artifacts`
- `fe artifacts`
- `model artifacts`
- `evaluation artifacts`
- `output_dir` (可选)

## 输出
- `analysis_report.md|pdf`
- `analysis_notebook.ipynb`

## 执行约定
1. 聚合并校验上游产物完整性。
2. LLM 生成叙事与结论。
3. 导出报告与 notebook。
4. 将结果写入 `output/runs/<run_id>/report/`。
