#!/usr/bin/env python3
"""
nemotron-monitoring.py
Fetches local FastAPI metrics, summarizes anomalies using Nemotron (observation-only),
and sends structured JSON to the Diagnostic Agent API for root-cause reasoning.
"""

import os
import json
import re
import requests
from openai import OpenAI
from dotenv import load_dotenv

# ──────────────────────────────────────────────────────────────
# 1️⃣ Environment setup
# ──────────────────────────────────────────────────────────────
load_dotenv()

API_KEY = "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"
NIM_API_BASE = "https://integrate.api.nvidia.com/v1"
METRICS_URL = "http://localhost:8000/metrics"
DIAGNOSTIC_URL = "http://localhost:8010/diagnose"

client = OpenAI(base_url=NIM_API_BASE, api_key=API_KEY)

# ──────────────────────────────────────────────────────────────
# 2️⃣ Helpers
# ──────────────────────────────────────────────────────────────
def get_network_metrics():
    """Fetch metrics from the local FastAPI metrics endpoint."""
    try:
        r = requests.get(METRICS_URL, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": "failed_to_fetch_metrics", "exception": str(e)}

# ──────────────────────────────────────────────────────────────
# 3️⃣ JSON reasoning
# ──────────────────────────────────────────────────────────────
def get_reasoning_json(metrics):
    """Describe network metrics — observation-only (no root cause)."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are a network monitoring assistant. "
                "Your task is to describe the network condition using provided metrics. "
                "Identify anomalies but DO NOT infer causes. Respond ONLY in JSON format:\n"
                "{\n"
                "  'observation_summary': str,\n"
                "  'metrics': { key: value },\n"
                "  'anomaly_flags': list[str],\n"
                "  'confidence_score': float,\n"
                "  'recommended_next_agent': 'DiagnosticAgent'\n"
                "}\n"
            )
        },
        {
            "role": "user",
            "content": "Analyze the following metrics:\n\n" + json.dumps(metrics, indent=2)
        }
    ]

    completion = client.chat.completions.create(
        model="nvidia/nvidia-nemotron-nano-9b-v2",
        messages=messages,
        temperature=0.3,
        top_p=0.9,
        max_tokens=1024,
    )

    response_text = completion.choices[0].message.content.strip()
    # Pre-sanitize single quotes → double quotes to fix invalid JSON
    response_text = re.sub("'", '"', response_text)

    try:
        reasoning_json = json.loads(response_text)
    except json.JSONDecodeError:
        reasoning_json = {"raw_output": response_text, "parse_error": True}

    return reasoning_json

def send_to_diagnostic_agent(monitoring_output):
    """Send MonitoringAgent output JSON to Diagnostic Agent FastAPI endpoint."""
    try:
        headers = {"Content-Type": "application/json"}
        resp = requests.post(DIAGNOSTIC_URL, headers=headers, data=json.dumps(monitoring_output), timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"⚠️ Failed to send data to Diagnostic Agent: {e}")
        return {"error": "diagnostic_agent_unreachable", "exception": str(e)}

# ──────────────────────────────────────────────────────────────
# 4️⃣ Entrypoint
# ──────────────────────────────────────────────────────────────
def main():
    metrics = get_network_metrics()
    print("=== Metrics ===")
    print(json.dumps(metrics, indent=2))

    print("\n=== MonitoringAgent JSON (observation-only) ===")
    observation = get_reasoning_json(metrics)
    print(json.dumps(observation, indent=2))

    print("\n=== Sending to Diagnostic Agent ===")
    diagnostic_output = send_to_diagnostic_agent(observation)
    print("\n=== DiagnosticAgent Response ===")
    print(json.dumps(diagnostic_output, indent=2))

    print("\n=== Done ===")

if __name__ == "__main__":
    main()