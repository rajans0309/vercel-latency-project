import json
import os
from http.server import BaseHTTPRequestHandler

with open(os.path.join(os.path.dirname(__file__), "q-vercel-latency.json")) as f:
    RECORDS = json.load(f)

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "*",
}


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


class handler(BaseHTTPRequestHandler):
    def _send(self, status, body=None):
        self.send_response(status)
        for k, v in CORS.items():
            self.send_header(k, v)
        if body is not None:
            data = json.dumps(body).encode()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_header("Content-Length", "0")
            self.end_headers()

    def do_OPTIONS(self):
        self._send(204)

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(n) or b"{}")
            regions = payload["regions"]
            threshold = float(payload["threshold_ms"])
            if not isinstance(regions, list):
                raise ValueError
        except (ValueError, KeyError, TypeError):
            return self._send(400, {"error": 'Expected JSON {"regions": [...], "threshold_ms": number}'})
        self._send(200, {"regions": compute(regions, threshold)})
