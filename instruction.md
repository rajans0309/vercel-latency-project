
eShopCo streams latency pings from every storefront to a small FastAPI service. Product managers want a serverless endpoint they can call from dashboards to check whether a deployment stays under target latency. 

Use Sample telemetry bundle q-vercel-latency.json and deploy a Python endpoint on **Vercel**. 

Your endpoint must:

- Accept a `POST` request with JSON body `{"regions": [...], "threshold_ms": 180}`
- Return per-region metrics: `avg_latency` (mean), `p95_latency` (95th percentile), `avg_uptime` (mean), and `breaches` (count of records above threshold)
- Enable CORS for `POST` requests from any origin

We'll send `{"regions":["apac","amer"],"threshold_ms":179}` to your endpoint and verify the response (order doesn't matter). 

