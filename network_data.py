from fastapi import FastAPI
from fastapi.responses import JSONResponse
import random
import time

app = FastAPI()

def simulate_network_metrics():
    return {
        "latency_ms": random.choice([20, 30, 50, 100, 300]),
        "packet_loss_percent": random.choice([0, 0.5, 1, 5, 10]),
        "download_mbps": random.uniform(20, 100),
        "upload_mbps": random.uniform(5, 20),
        "dns_resolution_time_ms": random.choice([40, 60, 120, 500]),
        "connected": random.choice([True, True, True, False])
    }

@app.get("/metrics")
def get_metrics():
    """Endpoint that returns simulated network metrics."""
    data = simulate_network_metrics()
    return JSONResponse(content=data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)