# InsightPilot_AI 重构方案（面向可独立运行的 Skill Workflow）

## 1) 当前仓库主要问题（基于现状代码）

1. **README 的目标结构与实际目录不一致**：例如 `src/core`、`feature_engineering`、`reporting` 等在仓库中并不存在，导致维护者理解成本高。
2. **agent / tool / orchestrator 职责边界不够清晰**：部分模块既有业务逻辑也有流程调度，后续扩展成多 skill 时会耦合。
3. **缺少标准化 skill 目录与契约**：尚无 `skills/<name>/SKILL.md` 的统一入口，难以做到 EDA/FE/Model/Evaluate/Report 的独立调用和复用。
4. **输出协议未统一**：每个阶段产物路径和 JSON schema 缺少同层级的规范位置，不利于串联与回放。

---

## 2) 建议的增删改（文件夹级别）

> 你问的“哪些需要改、要增删改哪些文件夹”可以按下面执行。

### A. 新增（Add）

- `skills/`：技能封装根目录
  - `skills/eda/`
  - `skills/fe/`
  - `skills/model/`
  - `skills/evaluate/`
  - `skills/report/`
- `src/workflows/`：每个 skill 对应一个可单跑的 workflow 入口
  - `eda_workflow.py`
  - `fe_workflow.py`
  - `model_workflow.py`
  - `evaluate_workflow.py`
  - `report_workflow.py`
- `src/contracts/`：阶段间 I/O 协议（Pydantic/dataclass/json schema）
  - `eda_contract.py`
  - `fe_contract.py`
  - `model_contract.py`
  - `evaluate_contract.py`
  - `report_contract.py`
- `src/runtime/`：状态、artifact、run context
  - `state_store.py`
  - `artifact_store.py`
- `output/runs/<run_id>/`：一次完整执行的产物目录（可追溯）
- `configs/`：模型参数、prompt 路由、feature flags

### B. 修改（Modify）

- `src/orchestrator/`：保留总编排（全链路），但下沉各阶段执行到 `src/workflows/`。
- `src/tools/`：仅保留“原子工具”职责，不直接承担复杂跨步骤逻辑。
- `src/agent/`：由“重逻辑”转为“决策 + 调度”，调用 workflow / tools。
- `README.md`：更新为真实结构 + skill 运行方式。

### C. 逐步淘汰/迁移（Deprecate）

- `scripts/` 下零散 test / 调试入口，逐步迁移到：
  - `scripts/run_*.py`（只保留统一入口）
  - `tests/`（pytest）
- 老的单文件重逻辑模块，逐步拆分到 `workflows + contracts + tools`。

---

## 3) 最终推荐目录结构（总架构）

```text
InsightPilot_AI/
├─ app/
│  ├─ cli.py                         # 统一命令入口（run skill / run full）
│  └─ api.py                         # API服务入口
├─ skills/
│  ├─ eda/
│  │  └─ SKILL.md                    # EDA skill 使用说明与触发规则
│  ├─ fe/
│  │  └─ SKILL.md
│  ├─ model/
│  │  └─ SKILL.md
│  ├─ evaluate/
│  │  └─ SKILL.md
│  └─ report/
│     └─ SKILL.md
├─ src/
│  ├─ orchestrator/
│  │  └─ langgraph_flow.py           # 全链路编排（调用各workflow）
│  ├─ workflows/
│  │  ├─ eda_workflow.py             # 可单跑：原始数据 -> eda artifacts
│  │  ├─ fe_workflow.py              # 可单跑：eda summary -> fe plan
│  │  ├─ model_workflow.py           # 可单跑：fe outputs -> model result
│  │  ├─ evaluate_workflow.py        # 可单跑：model result -> eval report
│  │  └─ report_workflow.py          # 可单跑：全链路 artifacts -> report/notebook
│  ├─ contracts/
│  │  ├─ eda_contract.py
│  │  ├─ fe_contract.py
│  │  ├─ model_contract.py
│  │  ├─ evaluate_contract.py
│  │  └─ report_contract.py
│  ├─ tools/                         # 原子函数调用工具（Function Calling）
│  │  ├─ eda_tool.py
│  │  ├─ fe_tool.py
│  │  ├─ model_tool.py               # 新增（从agent逻辑沉淀）
│  │  ├─ evaluate_tool.py            # 新增
│  │  ├─ report_tool.py              # 新增
│  │  └─ registry.py
│  ├─ agent/                         # Agent层：思考、路由、反思，不做重计算
│  ├─ llm/                           # llm client/prompt/parser
│  ├─ knowledge/                     # RAG/KG检索与知识管理
│  ├─ runtime/                       # run context + artifact 管理
│  ├─ data/
│  └─ utils/
├─ scripts/
│  ├─ run_full_pipeline.py           # 全流程入口
│  ├─ run_eda_workflow.py
│  ├─ run_fe_workflow.py
│  ├─ run_model_workflow.py
│  ├─ run_evaluate_workflow.py
│  └─ run_report_workflow.py
├─ configs/
│  ├─ model_config.yaml
│  ├─ prompt_config.yaml
│  └─ runtime.yaml
├─ data/
│  ├─ raw/
│  ├─ processed/
│  └─ features/
├─ output/
│  └─ runs/
│     └─ <run_id>/
│        ├─ eda/
│        ├─ fe/
│        ├─ model/
│        ├─ evaluate/
│        └─ report/
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  └─ e2e/
└─ docs/
   └─ system_restructure_plan.md
```

---

## 4) 五个 Skill 的职责分工（可独立运行 + 带 LLM）

### 4.1 `eda` skill
- **输入**：`data_path`、`target`(可选)、`problem_type`(可选)
- **核心动作**：profile/missing/dist/outlier/correlation + LLM 生成业务洞察
- **输出**：`eda_result.json`、`eda_for_llm.json`、`kg_candidates.json`
- **独立运行价值**：可单独用于“数据体检 + 问题发现”

### 4.2 `fe` skill
- **输入**：`eda_for_llm.json` + `problem_type` + `model_candidates`
- **核心动作**：LLM 生成 FE plan（编码、变换、选择）+ 可执行 FE pipeline
- **输出**：`fe_plan.json`、`feature_matrix.parquet`
- **独立运行价值**：可作为“特征方案工厂”反复迭代

### 4.3 `model` skill
- **输入**：特征矩阵 + 任务类型 + 预算约束
- **核心动作**：候选模型训练、CV、模型选择、超参建议
- **输出**：`model_results.json`、`best_model.pkl`、`leaderboard.json`
- **独立运行价值**：能脱离上游直接做 AutoML 小闭环

### 4.4 `evaluate` skill
- **输入**：`model_results.json`、`best_model.pkl`、test/holdout数据
- **核心动作**：指标汇总、误差分析、漂移/稳健性检查、LLM 解释建议
- **输出**：`evaluation.json`、`risk_flags.json`、`improvement_actions.json`
- **独立运行价值**：做“模型审计/复盘”可独立复用

### 4.5 `report` skill
- **输入**：所有上游 artifacts
- **核心动作**：LLM 组织叙事 + 自动图表/表格拼装 + Notebook/PDF导出
- **输出**：`analysis_report.md|pdf`、`analysis_notebook.ipynb`
- **独立运行价值**：同一结果可多版本报告（管理层/技术版）

---

## 5) 推荐执行顺序（支持单跑）

1. `eda` → 2. `fe` → 3. `model` → 4. `evaluate` → 5. `report`

但每个阶段都应支持：
- 指定已有上游 artifact 直接启动
- 缺失输入时给出清晰错误和补齐建议
- 独立产出到 `output/runs/<run_id>/<skill>/`

---

## 6) 迁移建议（低风险）

- **第1阶段**：先建立 `skills/ + contracts/ + workflows/` 空壳，不改核心逻辑。
- **第2阶段**：把当前 `src/tools/eda_tool.py`、`src/tools/fe_tool.py` 接入 workflow。
- **第3阶段**：从 `src/agent/model_agent.py`、`src/agent/evaluation_agent.py` 抽取 `model/evaluate tool`。
- **第4阶段**：补齐 report workflow，并接入 orchestrator。
- **第5阶段**：补 tests + run_id 产物标准化。
