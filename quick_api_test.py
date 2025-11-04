"""Quick API test."""
import requests
import time

time.sleep(2)  # Wait for backend to be ready

print("Testing /api/emails endpoint...")
try:
    r = requests.get('http://127.0.0.1:8000/api/emails?source=outlook&limit=5')
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        print(f"✓ Email count: {len(data['emails'])}")
        print(f"✓ Total: {data['total']}")
        
        if data['emails']:
            print(f"\nFirst 3 emails:")
            for i, email in enumerate(data['emails'][:3]):
                print(f"  {i+1}. {email['subject'][:60]}")
        else:
            print("\n⚠️ No emails returned")
    else:
        print(f"✗ Error: {r.text}")
        
except Exception as e:
    print(f"✗ Exception: {e}")
