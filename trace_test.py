from dotenv import load_dotenv; load_dotenv()
import time

t = time.time()
from app.agents.pipeline import run_query
print('import time:', round(time.time()-t, 1), 's')

t = time.time()
r = run_query('scoliosis machine learning', 'researcher')
print('pipeline time:', round(time.time()-t, 1), 's')
print('trace:')
for step in r['pipeline_trace']:
    print(f"  {step['agent']:25s} {step['status']:12s} {step['latency_ms']:.0f}ms")
