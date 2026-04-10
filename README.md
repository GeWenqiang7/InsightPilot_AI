# 🤖 AI Data Analysis Agent System (PRD Version - Full)

------------------------------------------------------------------------

## 1. 📌 Product Overview

AI Data Analysis Agent 是一个端到端自动化数据分析系统，通过 LLM +
Agent + Tool Pipeline，实现从用户需求到建模与报告输出的完整流程自动化。

核心价值： - 自动理解数据 - 自动生成分析目标 - 自动执行EDA、特征工程、选择模型建模与结果评估 - 自动输出Notebook与分析报告

------------------------------------------------------------------------

## 2. 🎯 Target Users

-   数据分析师（提升效率）
-   产品经理（快速验证业务问题）
-   非技术业务人员
-   AI / Data 产品开发者

------------------------------------------------------------------------

## 3. 🚀 End-to-End Workflow

User Input\
↓\
Goal Generation（LLM推荐分析目标）\
↓\
User Selection / Iteration\
↓\
EDA（结构化数据分析）\
↓\
Feature Engineering Plan（LLM生成）\
↓\
Feature Engineering Execution\
↓\
Model Training\
↓\
Evaluation\
↓\
Notebook + Report Output

------------------------------------------------------------------------

## 4. Core Modules

### 4.1 Input Layer

-   数据上传（CSV / 本地路径）
-   分析需求（自然语言 / 文档）

------------------------------------------------------------------------

### 4.2 Goal Generation 

LLM 自动生成 3--5 个候选分析目标：

每个目标包含： - goal_id - 分析标题 - problem_type - 方法（ML / 统计） - 分析思路 - 可行性解释 - 输出结果 - 评估指标

支持多轮 refinement（不覆盖历史）

------------------------------------------------------------------------

### 4.3 EDA Module

输出： - eda_result.json（完整） - eda_for_llm.json（压缩）

分析内容： - schema / meta - missing - distribution - outliers - correlation - insights

------------------------------------------------------------------------

### 4.4 Feature Engineering

LLM 生成：

fe_plan.json： - 变量转换 - 特征构造 - 编码方式 - 特征筛选 - explainability

------------------------------------------------------------------------

### 4.5 Modeling

自动匹配：

  类型   模型
  ------ --------------------
  分类   Logistic / XGBoost
  回归   Linear / XGBoost
  聚类   KMeans

------------------------------------------------------------------------

### 4.6 Evaluation

-   分类：AUC / F1
-   回归：RMSE / MAE
-   特征重要性
-   泛化能力

------------------------------------------------------------------------

### 4.7 Output

📓 Notebook（完整pipeline）\
📄 PDF Report（业务分析报告）

------------------------------------------------------------------------

## 5. 🧱 System Architecture

User → LLM → Agent → Tools → Output

------------------------------------------------------------------------

## 6. 📁 Project Structure

src/ ├── agent/ \# Agent决策逻辑 ├── tools/ \# EDA / FE / Model / Eval
├── eda/ \# 数据分析模块 ├── llm/ \# Prompt & API ├── graph/ \#
LangGraph workflow ├── rag/ \# 知识增强 ├── output/ \# 输出结果 └── app/
\# API入口

------------------------------------------------------------------------

## 7. Execution

``` bash
python app/api.py
```

------------------------------------------------------------------------

## 8. Deployment

``` bash
docker build -t ai-analysis-agent .
docker run -p 8000:8000 ai-analysis-agent
```

------------------------------------------------------------------------

## 9. 🧪 Example Outputs

-   eda_result.json\
-   eda_for_llm.json\
-   fe_plan.json\
-   model_metrics.json\
-   notebook.ipynb\
-   report.pdf

------------------------------------------------------------------------

## 10. Future Roadmap

-   Multi-Agent（Planner / Critic）
-   AutoML
-   多模态分析（图表理解）
-   Dashboard UI
-   实时数据接入

------------------------------------------------------------------------

## 11. Tech Stack

-   Python
-   OpenAI API
-   LangGraph
-   Pandas / Sklearn / XGBoost
-   FAISS
-   Docker

