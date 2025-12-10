# ⚙️ AI Workflow Engine  
A lightweight, extensible workflow engine built with **FastAPI**, supporting **background execution**, **real-time WebSocket log streaming**, and **structured node-based graph workflows**.

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Framework-brightgreen?logo=fastapi)
![Status](https://img.shields.io/badge/Build-Passing-brightgreen)
![License](https://img.shields.io/badge/License-MIT-purple)

</div>

---

## 🚀 Overview  
This engine allows you to define graphs of nodes—each node being a Python function that reads/modifies a shared state.  
The engine supports **branching, looping, logging, async execution**, and **live log streaming** via WebSockets.

It is designed to be simple, modular, and easy to extend.

---

# 📦 Features  
Your workflow engine supports:

### ✅ **Node-based execution**
- Each node = a Python function  
- Nodes mutate a shared `state` dict  
- Supports sync + async functions

### ✅ **Graph structure**
- Directed execution  
- Supports:  
  - **Branching** (conditional next nodes)  
  - **Looping** (edges that point backwards)  
  - **End states** (no next node)

### ✅ **Background Execution**
- Workflows can run asynchronously  
- `POST /graph/run` returns immediately with a `run_id`  
- Execution happens in the background

### ✅ **Real-Time Log Streaming**
- WebSocket endpoint: `/ws/{run_id}`  
- Streams log updates node-by-node  
- Includes a browser test page: `/ws-test/{run_id}`  

### ✅ **Persistent Run Tracking**
- In-memory stores for graphs & runs  
- Each run stores logs, state, and execution metadata  

---

# 🛠️ How to Run Locally

### **1️⃣ Install dependencies**
```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### **2️⃣ Start the FastAPI server**
```bash
uvicorn app.main:app --reload --port 8000
```

### **3️⃣ Open Swagger UI**
👉 http://127.0.0.1:8000/docs

There you can:
- **Create a graph**  
- **Run the workflow**  
- **Check run state**  
- **Trigger background execution**  

### **4️⃣ Stream logs in real time**
Replace `{run_id}` with the value returned from `/graph/run`:

👉 http://127.0.0.1:8000/ws-test/{run_id}

---

# 🧩 Example Use Case: Code Review Agent  
The default example graph performs:

- Function extraction  
- Complexity analysis  
- Issue detection  
- Iterative improvement loops  

This demonstrates branching + loops + background execution + WebSocket logs.

---

# 🔧 Project Structure
```
ai-engine/
│
├── app/
│   ├── main.py          # FastAPI app + routes + WebSocket
│   ├── engine.py        # Workflow executor (background + logging)
│   ├── models.py        # Pydantic schemas
│   ├── storage.py       # In-memory stores + log queues
│   ├── tools.py         # Helper tools/functions
│   ├── workflows.py     # Node functions + example graph
│
├── requirements.txt
└── README.md
```

---

# 🚀 What I Would Improve With More Time

### **🗃️ 1. Persistent Storage**
Move from in-memory → SQLite/Postgres using SQLAlchemy:
- durable run history  
- restart-safe workflow execution  

### **🌿 2. Richer Branching Language**
Allow expressions like:
```yaml
next: "improve" if state.score < 7 else "issues"
```
instead of manual `_last_condition`.

### **🏃 3. Concurrency & Parallel Branch Execution**
Run independent branches simultaneously using asyncio tasks.

### **📡 4. Metrics + Monitoring Dashboard**
- Workflow durations  
- Node execution times  
- Failure analytics  

### **🔐 5. Authentication & Multi-Tenancy**
Token-based access for multi-user environments.

---

# 📝 Summary  
This project implements a clean, well-structured workflow engine with:

- Background execution  
- WebSocket logging  
- Modular node-based architecture  
- Complete Swagger documentation  

While simple by design, it provides a strong foundation for more advanced workflow automation systems.

---

<div align="center">
  
✨ *Designed for clarity, extensibility, and real-world engineering experience.*  

</div>
