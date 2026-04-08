# 🤖 AI Data Analysis Agent System

## 📌 Overview

This project is an **agent-based automated data analysis system** powered by LLMs.

It integrates:

* 🧠 Agent decision-making
* 🔄 LangGraph workflow orchestration
* 🛠 Tool-based execution (EDA, Feature Engineering, Modeling)
* 📚 RAG (Retrieval-Augmented Generation)
* ⚙️ Function Calling for structured execution
* 🚀 API + Docker deployment

The system can automatically:

* Understand datasets
* Generate feature engineering strategies
* Train and evaluate models
* Iterate and optimize results

---

## 🧱 System Architecture

```
User Query
   ↓
LLM Agent (Decision Layer)
   ↓
Tool Execution (EDA / FE / Model / RAG)
   ↓
State Memory (LangGraph)
   ↓
Iteration Loop
   ↓
Final Report
```

---

## 🔑 Key Features

### 1. Agent-based Workflow

* LLM dynamically decides next actions
* Supports multi-step reasoning and iteration

### 2. Tool Modularization

* EDA Tool
* Feature Engineering Tool
* Model Training Tool
* Evaluation Tool

### 3. LangGraph Integration

* State-driven workflow
* Scalable pipeline orchestration

### 4. Function Calling

* Structured tool invocation
* Reliable JSON outputs

### 5. RAG (Knowledge Augmentation)

* Retrieves domain knowledge
* Enhances feature engineering and modeling decisions

### 6. Iterative Optimization

* Model → Evaluate → Improve loop

---

## 📁 Project Structure

```
src/
 ├── agent/        # decision logic
 ├── tools/        # execution modules
 ├── rag/          # retrieval system
 ├── graph/        # workflow orchestration
 ├── llm/          # LLM interface
 └── eda/          # EDA pipeline
```

---

## ⚙️ How It Works

### Step 1: EDA

Analyze dataset structure, distribution, missing values, and outliers.

### Step 2: Feature Engineering

Generate transformation plans using LLM.

### Step 3: Model Training

Train predictive models (Logistic Regression / XGBoost).

### Step 4: Evaluation

Evaluate performance and metrics.

### Step 5: Iteration (Agent Loop)

Agent decides whether to:

* Improve features
* Change model
* Stop

---

## 📚 RAG Integration

The system retrieves relevant knowledge such as:

* Feature engineering best practices
* Outlier handling techniques
* Model selection strategies

---

## 🚀 Deployment

### Run locally

```
python app/api.py
```

### Docker

```
docker build -t ai-agent .
docker run -p 8000:8000 ai-agent
```

---

## 🧪 Example Output

* EDA summary
* Feature engineering plan (JSON)
* Model performance report
* Final insights

---

## 🎯 Use Cases

* Automated data analysis
* Feature engineering assistant
* Model prototyping
* Data science workflow automation

---

## 🧠 Tech Stack

* Python
* OpenAI API
* LangGraph
* FAISS / Vector DB
* FastAPI
* Docker

---

## 💡 Future Work

* Multi-agent collaboration
* AutoML integration
* UI dashboard
* Real-time data pipeline

---

## 👤 Author

Wenqiang Ge

---
