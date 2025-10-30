This project aims to enhance communication stability for remote workers. It monitors and analyzes network issues using AI-driven diagnostics, then provides clear, step-by-step guidance to users without technical expertise. The AI acts as a domain expert, handling complex technical analysis while enabling non-technical users to implement effective solutions easily.

Overview

This project demonstrates a multi-agent AI system that monitors and diagnoses network performance in real time using NVIDIA Nemotron reasoning models.

It consists of:
	•	Network Data API (FastAPI) → Simulates real-time network metrics.
	•	Monitoring Agent → Observes network data and identifies anomalies.
	•	Diagnostic Agent → Determines the most probable root cause using Nemotron reasoning.

All agents communicate via local HTTP endpoints and share the same NVIDIA NIM API key.

+---------------------+       +--------------------+       +---------------------+
| Network Data API    | --->  | Monitoring Agent   | --->  | Diagnostic Agent    |
| (FastAPI, port 8000)|       | (Nemotron reasoning)|       | (Nemotron reasoning)|
+---------------------+       +--------------------+       +---------------------+
        ^                                                         |
        |                                                         v
        +-------------------< Shared .env (API key) >-------------+

⚙️ Requirements

🐍 Python Version
	•	Python 3.10+ (3.13 works fine)

📦 Install Dependencies

pip install fastapi uvicorn openai python-dotenv requests

Run API endpoints for demonstration and agents

uvicorn network_data:app --reload --port 8000

python diagnostic-agent.py

Run monitoring agent to create network diagnosis 

python nemotron-monitoring.py
