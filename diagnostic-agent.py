#!/usr/bin/env python3
"""
diagnostic-agent.py
------------------------------------------------------------
Receives MonitoringAgent JSON (via POST /diagnose) and uses
Nemotron to identify the most probable root cause.
Runs as a FastAPI microservice at port 8010.
------------------------------------------------------------
"""

import os
import json
from openai import OpenAI
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import uvicorn

# ───────────────────────────────────────────────
# 1️⃣  Setup
# ───────────────────────────────────────────────
load_dotenv()
API_KEY = "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"
NIM_API_BASE = "https://integrate.api.nvidia.com/v1"

client = OpenAI(base_url=NIM_API_BASE, api_key=API_KEY)

# ───────────────────────────────────────────────
# 2️⃣  Diagnostic Reasoning
# ───────────────────────────────────────────────
def diagnostic_agent(monitoring_output):
    """Use Nemotron to infer root cause from MonitoringAgent's observations."""
    system_message = {
        "role": "system",
        "content": (
            "You are a diagnostic reasoning AI. Based on factual anomaly data from the monitoring agent, "
            "identify the most probable root cause. Respond ONLY with JSON:\n"
            "{\n"
            "  'root_cause': str,\n"
            "  'confidence': float,\n"
            "  'supporting_evidence': list[str],\n"
            "  'recommended_next_agent': 'GuidanceAgent'\n"
            "}\n"
        ),
    }

    user_message = {
        "role": "user",
        "content": "Here is the monitoring agent report:\n\n" + json.dumps(monitoring_output, indent=2),
    }

    try:
        completion = client.chat.completions.create(
            model="nvidia/nvidia-nemotron-nano-9b-v2",
            messages=[system_message, user_message],
            temperature=0.3,
            top_p=0.9,
            max_tokens=1024,
        )

        response_text = completion.choices[0].message.content.strip()
        response_text = response_text.replace("'", '"')

        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            result = {"raw_output": response_text, "parse_error": True}

        return result

    except Exception as e:
        print(f"❌ Error in diagnostic_agent: {e}")
        return {"error": "nemotron_call_failed", "details": str(e)}

# ───────────────────────────────────────────────
# 3️⃣  FastAPI Service
# ───────────────────────────────────────────────
app = FastAPI(
    title="Diagnostic Agent API",
    description="Receives MonitoringAgent output and performs root-cause reasoning via Nemotron.",
    version="1.0.0",
)

@app.post("/diagnose")
async def diagnose(request: Request):
    """POST endpoint for MonitoringAgent handoff."""
    try:
        data = await request.json()
        print("\n📥 Received MonitoringAgent data:")
        print(json.dumps(data, indent=2))

        result = diagnostic_agent(data)

        print("\n📤 Diagnostic Output:")
        print(json.dumps(result, indent=2))

        return JSONResponse(content=result)
    except Exception as e:
        print(f"❌ Exception in /diagnose: {e}")
        return JSONResponse(
            content={"error": "diagnostic_agent_failed", "details": str(e)},
            status_code=500,
        )

# ───────────────────────────────────────────────
# 4️⃣  Launch server
# ───────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("DIAGNOSTIC_PORT", 8010))
    print(f"🚀 Diagnostic Agent running at http://localhost:{port}/diagnose")
    uvicorn.run(app, host="0.0.0.0", port=port)