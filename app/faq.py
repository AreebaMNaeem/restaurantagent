import requests

url = "https://xanders.pk/wp-json/wp/v2/pages?per_page=100"

try:
    r = requests.get(url, timeout=10)
    print("Status:", r.status_code)
    print("First 200 chars:", r.text[:200])
except Exception as e:
    print("Error:", e)
