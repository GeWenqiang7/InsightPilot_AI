# InsightPilot 架构建议：从单 Agent 到多 Agent + 分层记忆

## 1) 现有方向判断

你当前路线是合理的：

- 将可执行 skill 统一封装在 `src/skills/<xxx>_skill/`。
- 通过 `src/tools/*.py` 作为 function-calling 适配层，给 LLM/Agent 调用。
- 在编排层继续推进 LangChain + LangGraph。
- 让 RAG / Knowledge Base / KG 为决策提供外部证据与结构化关系。

这个分层可以概括为：

1. **Skill 执行层**：可复用、可测试、输入输出稳定。
2. **Tool 适配层**：把 skill 暴露给模型工具调用。
3. **Agent 编排层**：基于状态图调度步骤、做失败恢复和重试。
4. **Knowledge 层**：RAG + KG + 规则知识库，提供证据和约束。
5. **产品交付层**：输出模型、指标、可读报告。

---

## 2) 你现在是单 Agent 吗？

从当前代码形态看，本质上仍然是**单主控 Agent + 多工具**：

- 一个主 Agent 维护状态并串行调用 EDA/FE 等能力。
- skill/tool 是“能力模块”，不是“自治 Agent”。

这没有问题，且是最稳妥起点。

---

## 3) 如果要升级到多 Agent，思路怎么改

建议从“分工驱动”切，而不是一上来就把所有模块都 Agent 化。

### 推荐拓扑（最小可用）

- **Planner Agent**：解析用户诉求、拆解任务、制定执行图。
- **Data Analyst Agent**：负责 EDA + 数据质量判断。
- **Model Agent**：负责 FE/训练/评估策略执行。
- **Reviewer Agent**：做一致性审计（是否有数据泄漏、指标解释是否自洽）。
- **Report Agent**：面向业务输出结论和行动建议。

### 关键改造点

1. **共享状态总线**：统一 `state schema`，每个 Agent 只读写自己负责字段。
2. **标准化工件**：所有 Agent 只通过 artifacts 交互（JSON/Parquet/Markdown），避免隐式耦合。
3. **显式交接协议**：定义 handoff 契约（输入、输出、置信度、阻塞原因）。
4. **审计与回滚**：关键节点引入 reviewer gate，失败可回滚到上一步。
5. **预算治理**：按 Agent 维度做 token/time/cost 限额。

---

## 4) 三层记忆（上下文 / 历史会话 / 用户偏好）是否必要？

你的场景“用户上传数据并给一次性分析目标”为主，**不建议一开始就做重记忆系统**。

### MVP 阶段建议（必要）

保留两层即可：

1. **运行上下文记忆（短期）**
   - 范围：单次任务 run 内。
   - 内容：当前数据摘要、目标、中间 artifacts、失败重试信息。
   - 作用：保证流程连贯和可恢复。

2. **用户偏好记忆（轻量长期）**
   - 范围：跨会话。
   - 内容：报告语言风格、指标偏好、输出格式偏好、业务术语映射。
   - 作用：提升交付体验。

### 可延后（按需再加）

3. **历史会话记忆（完整长期）**
   - 仅当用户存在“连续项目复盘/多轮迭代建模”需求再引入。
   - 否则会带来存储、检索噪声和隐私治理成本。

---

## 5) 记忆层设计建议（可直接落地）

### Memory Schema

- `run_memory`（TTL: run 结束后归档）
  - `goal`, `constraints`, `dataset_fingerprint`, `artifacts_index`, `decision_log`
- `profile_memory`（长期）
  - `report_style`, `metric_preference`, `risk_tolerance`, `default_output_format`
- `session_memory`（可选）
  - `session_summary`, `open_questions`, `accepted_actions`

### 写入策略

- 只在**关键节点**写记忆：goal 确认、EDA结论、模型选择、最终报告。
- 避免逐轮写入全部对话，优先写“结构化摘要 + 决策依据”。

### 读取策略

- Planner 读取：`profile_memory + session_summary`
- Specialist 读取：`run_memory` 必要字段
- Reporter 读取：`run_memory + profile_memory`

---

## 6) 推荐迭代顺序

1. 先把 `src/skills` 下五个 skill（eda/fe/model/evaluate/report）封装完，稳定 I/O。
2. 在 LangGraph 建立单主控图：Plan -> EDA -> FE -> Model -> Evaluate -> Report。
3. 增加 Reviewer gate 和失败回滚。
4. 再拆为多 Agent（先拆 Planner/Reviewer，最后拆 Specialist）。
5. 最后再按真实需求补齐历史会话记忆层。

---

## 7) 一句话结论

你的总体方向是对的。短期优先做“**技能封装标准化 + 状态图编排稳定化**”；多 Agent 和完整三层记忆都应在出现真实复杂协作/长期复盘需求后再上，不要过早复杂化。

---

## 8) 预留微调（Fine-tuning）能力：现在该留哪些“窗口”

如果你后面要做微调，建议现在就把“可训练数据闭环”预留好，但**先不急着上训练基础设施**。

### 8.1 先定义可微调目标（不要泛化）

建议优先做以下两类之一：

1. **结构化输出稳态化**（最推荐）
   - 目标：让模型稳定输出你定义的 JSON schema（如 plan、risk_flags、report_outline）。
2. **领域叙事风格对齐**
   - 目标：让报告语言更贴近你的业务语境和术语。

不建议早期做“全能力端到端微调”，成本高且收益不稳定。

### 8.2 现在必须预留的 6 个接口

1. **样本记录接口（trace logger）**
   - 每次任务记录：`input`、`tool_calls`、`artifacts摘要`、`final_output`、`人工评分`。
2. **数据脱敏接口**
   - 对数据样本自动做 PII 清洗（列名、文本、ID）。
3. **样本筛选接口**
   - 可按 `task_type / quality_score / failure_type` 回放与抽样。
4. **评测基线接口**
   - 固定一套离线 benchmark（JSON 合规率、关键字段召回、结论一致性）。
5. **模型路由接口**
   - 支持 `base_model` 与 `fine_tuned_model` 可配置切换（A/B）。
6. **回滚开关接口**
   - 微调模型表现退化时一键切回 base。

### 8.3 建议的数据结构（先建表，不一定马上填满）

- `llm_traces`
  - `trace_id, task_type, prompt_hash, tool_trace, output_text, output_json, quality_score, reviewer_feedback`
- `training_candidates`
  - `trace_id, label_status(approved/rejected), rejection_reason, pii_status, split(train/val/test)`
- `eval_runs`
  - `model_id, benchmark_version, json_valid_rate, factual_consistency, business_acceptance`

### 8.4 训练策略路线（按阶段）

1. **Phase A：Prompt + Tool 优化（当前）**
   - 先把失败类型收敛，再决定是否微调。
2. **Phase B：小规模 SFT（结构化输出）**
   - 用高质量样本做监督微调，目标是提升稳定性。
3. **Phase C：偏好对齐（可选）**
   - 如果你有稳定人工偏好数据，再做偏好学习。

### 8.5 与你现有系统的结合点

- 在 Planner / Reporter 节点加 `trace_hook`，把关键输入输出写入 `llm_traces`。
- 在 Reviewer 节点把审计结论写入 `quality_score` 和 `reviewer_feedback`。
- 在模型调用层保留 `model_alias` 配置，如：
  - `analysis_default -> gpt-base`
  - `analysis_ft_v1 -> ft:analysis-domain-v1`

这样做的好处是：

- 你现在不需要承担训练运维复杂度；
- 但未来一旦样本量和质量达标，可以平滑切到微调。

### 8.6 一句话建议

你现在最该做的是**把高质量训练数据采集链路先打通**（trace + 评分 + 脱敏 + 基线评测 + 回滚），而不是急着训练模型本身。
