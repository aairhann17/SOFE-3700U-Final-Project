import requests

# Test the actual Flask endpoint
session = requests.Session()

# First login
login_url = 'http://localhost:5000/login'
search_url = 'http://localhost:5000/api/search'

# Try to login first
print("Step 1: Attempting login...")
login_data = {
    'username': 'admin',
    'password': 'admin123'
}
login_resp = session.post(login_url, data=login_data, allow_redirects=False)
print(f"Login status: {login_resp.status_code}")
print(f"Cookies: {session.cookies.get_dict()}")

# Now test search
print("\nStep 2: Testing search endpoint...")
search_params = {
    'category': 'artworks',
    'field': '',
    'query': '',
    'matchType': 'partial'
}
search_resp = session.get(search_url, params=search_params)
print(f"Search status: {search_resp.status_code}")
print(f"Response: {search_resp.text[:500]}")

if search_resp.status_code == 200:
    data = search_resp.json()
    print(f"\n✓ Records returned: {len(data.get('records', []))}")
    if data.get('records'):
        print(f"  First record: {data['records'][0].get('Title', 'N/A')}")
else:
    print(f"\n✗ Error: {search_resp.text}")
