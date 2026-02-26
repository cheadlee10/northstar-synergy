import requests
import json

response = requests.get('http://localhost:8765/api/kalshi/summary', timeout=5)
data = response.json()

print('Raw JSON response:')
print(json.dumps(data['live'], indent=2))
