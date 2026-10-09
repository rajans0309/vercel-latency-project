import json
from pathlib import Path
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

RECORDS = json.loads((Path(__file__).parent / "q-vercel-latency.json").read_text())

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def always_allow_origin(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


class Query(BaseModel):
    regions: List[str]
    threshold_ms: float


def percentile(values, p):
    """Linear-interpolation percentile (same as numpy default)."""
    s = sorted(values)
    k = (len(s) - 1) * p / 100
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def compute(regions, threshold):
    out = {}
    for region in regions:
        rows = [r for r in RECORDS if r["region"] == region]
        if not rows:
            continue
        lat = [r["latency_ms"] for r in rows]
        up = [r["uptime_pct"] for r in rows]
        out[region] = {
            "avg_latency": sum(lat) / len(lat),
            "p95_latency": percentile(lat, 95),
            "avg_uptime": sum(up) / len(up),
            "breaches": sum(1 for v in lat if v > threshold),
        }
    return out


@app.post("/")
@app.post("/api/latency")
def latency(q: Query):
    return {"regions": compute(q.regions, q.threshold_ms)}
