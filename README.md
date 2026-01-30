# Mashreq Bank Operational Resilience Bounty

## 🛡️ Overview
AI-powered operational resilience monitor with **Human-in-the-Loop** governance. Detects systemic risks (Service Outages, Reputational Threats) while filtering routine noise.

## 📁 Project Structure
```
mashreq_resilience_bounty/
├── src/
│   ├── data_generator.py   # Synthetic data generator (3 scenarios)
│   ├── agent_graph.py      # LangGraph triage workflow
│   └── dashboard.py        # Streamlit HITL dashboard
├── data/                   # JSON scenario files
├── tests/                  # Red team tests (TODO)
├── .env.example            # API key template
└── requirements.txt        # Dependencies
```

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up API key
cp .env.example .env
# Edit .env with your OPENAI_API_KEY

# 3. Generate test data
python src/data_generator.py

# 4. Run the agent (processes data, outputs alerts)
python src/agent_graph.py ./data/scenario_technical_outage.json

# 5. Launch dashboard
streamlit run src/dashboard.py
```

## 🔑 Key Features
- **Explainable AI**: Every alert shows step-by-step reasoning
- **Governance Checks**: PII masking, bias detection, audit logging
- **Human-in-the-Loop**: Approve/Dismiss buttons on all critical alerts
- **3 Test Scenarios**: Baseline (Noise), Outage (Signal), Rumor (Reputational)

## 📊 Dashboard (localhost:8501)
Metrics → Alert Queue → Reasoning Expanders → HITL Actions

## 🧪 Testing Checklist (for Hackathon Demo)
- [ ] Run baseline scenario → Should auto-handle (no alerts)
- [ ] Run outage scenario → Should flag CRITICAL
- [ ] Run rumor scenario → Should flag WARNING
- [ ] Demonstrate human override in dashboard
