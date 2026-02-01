# Mashreq AI Command Center - System Specifics

## 1. What is your tech stack? (Specifics)

I chose a **100% Python-native stack** to ensure seamless integration between the Data Science logic and the Application layer, minimizing "serialization friction."

*   **Language**: Python 3.9+
*   **Interface (Frontend)**: **Streamlit**. Chosen for its ability to rapidly build "Glassmorphism" UI components (custom CSS injection) while keeping the logic primarily in Python.
*   **API (Backend)**: **FastAPI**. Used to expose the pipeline as a high-performance REST endpoint (`/pipeline/run-from-csv`), enabling potential future integration with mobile apps or other banking systems.
*   **Machine Learning**: **Custom Naive Bayes Implementation**. Instead of using a black-box LLM API (like GPT-4) for the core logical classification, I built a probabilistic **Naive Bayes Classifier** from scratch.
    *   *Why?* Banking regulations often require **Determinism** and **Explainability**. A Naive Bayes model based on known keywords is fully auditable. We know *exactly* why it flagged "OTP" as fraud. LLMs can hallucinate; this model cannot.
*   **Data Processing**: **Pandas** for high-velocity CSV ingestion and manipulation.
*   **Governance**: **Regex (Regular Expressions)** for the PII Guardrails. This is a deterministic layer that creates a hard boundary for data privacy.

---

## 2. Which scenarios did you choose?

I focused on **Operational Resilience**, selecting three distinct high-impact banking scenarios:

1.  **The "Liquidity Crisis" Rumor (Misinformation)**:
    *   *Scenario*: A coordinated bot attack spreading fake news that "Mashreq is out of cash," leading to a potential run on the bank.
    *   *Signals*: "Can't withdraw", "Bankrupt", "Empty ATMs".
2.  **The "OTP Interception" Attack (Fraud)**:
    *   *Scenario*: A wave of customers complaining about delayed or missing OTPs, which is often a precursor to a "SIM Swap" or large-scale phishing campaign.
    *   *Signals*: "OTP delay", "Did not receive code", "Unordered SMS".
3.  **Digital Service Outage (Service)**:
    *   *Scenario*: Detecting subtle app failures before the monitoring systems catch them (User-reported latency).
    *   *Signals*: "App stuck", "Login spinning", "FaceID fail".

---

## 3. How are you generating your "synthetic" signals?

The system accepts a **Controlled Input Dataset** (`synthetic_social_signals_mashreq.csv`).

*   **Source**: These signals were not scraped from real users (privacy violation). They were **procedurally generated** to mimic the linguistic patterns of angry/concerned banking customers.
*   **Structure**: Each generated signal follows a strict schema:
    *   `content`: The text body (e.g., "Why is my OTP taking 10 minutes??")
    *   `timestamp`: Crucial for the "Velocity" calculation.
    *   `metadata`: Contains the `synthetic: True` flag.
*   **Governance Check**: The specific file input path prevents the system from accidentally ingesting real customer / production data. If the `synthetic` flag is missing, the Guardrails layer rejects the record immediately.

---

## 4. What does your "Human-in-the-loop" interface actually look like?

It is **NOT** just a visualization dashboard; it is a **Decision Support System**.

*   **The "Triage" View**: Analysts see a prioritized queue of signals.
    *   *Feature*: **AI Reasoning Box**. Instead of just a red flag, the AI renders a text block: *"Signal: Potential fraud pattern... Why it matters: Regulatory fine risk."*
*   **The "Escalation" View**: Once an analyst clicks "Escalate", the signal moves to this distinct state.
    *   *Feature*: **AI Action Plans**. The interface presents a checklist: "1. Verify system status, 2. Notify Fraud Team". It does NOT execute these; it *prompts* the human to do them.
*   **The "Audit" View**: Every click is recorded. If an analyst dismisses a high-risk signal, that action is logged forever in the Immutable Audit Trail for post-incident review.

---

## 5. How are you calculating the "Confidence Score"?

The "Confidence Score" (0-100%) and "Risk Score" (0-10) are calculated using a **Multi-Factor Weighted Algorithm** in `risk_scorer.py`:

1.  **Bayesian Probability (The Base)**:
    *   The classifier calculates the probability `P(Category | Words)`.
    *   *Example*: If the text contains "OTP" (Weight 3.5) and "Delay" (Weight 3.0), the probability of `FRAUD` is near 99%.
2.  **Velocity Multiplier (The Context)**:
    *   The `ClusteringEngine` looks at how many *similar* signals arrived in the last 60 minutes.
    *   *Formula*: If `velocity > threshold`, the score is boosted by 1.2x. (A single complaint is noise; 50 complaints is a crisis).
3.  **Keyword Severity (The Spike)**:
    *   Certain "Kill Words" (defined in the dictionary) carry extra weight. "Hacked" has a higher weight than "Slow".
4.  **Final Normalization**:
    *   The aggregate score is mapped to a 0-10 scale.
    *   `Confidence Score` is the direct statistical output of the probability model.
    *   `Risk Score` is the probability *multiplied* by the potential impact (Severity).
