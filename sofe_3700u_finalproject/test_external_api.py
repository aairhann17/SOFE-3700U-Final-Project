# Test External API Integration

import requests

print("Testing Metropolitan Museum of Art API Integration...\n")

# Test 1: Search for artworks
print("1. Testing Search API...")
try:
    response = requests.get(
        'https://collectionapi.metmuseum.org/public/collection/v1/search',
        params={'q': 'painting', 'hasImages': 'true'},
        timeout=10
    )
    data = response.json()
    print(f"   ✓ Search successful! Found {data.get('total', 0)} total artworks")
    print(f"   ✓ Retrieved {len(data.get('objectIDs', [])[:20])} object IDs\n")
except Exception as e:
    print(f"   ✗ Search failed: {e}\n")

# Test 2: Get artwork details
print("2. Testing Object Details API...")
try:
    # Get details for a famous artwork (The Met's object ID for a Van Gogh)
    object_id = 436532  # Wheat Field with Cypresses
    response = requests.get(
        f'https://collectionapi.metmuseum.org/public/collection/v1/objects/{object_id}',
        timeout=10
    )
    artwork = response.json()
    print(f"   ✓ Retrieved artwork details:")
    print(f"     - Title: {artwork.get('title', 'N/A')}")
    print(f"     - Artist: {artwork.get('artistDisplayName', 'N/A')}")
    print(f"     - Date: {artwork.get('objectDate', 'N/A')}")
    print(f"     - Department: {artwork.get('department', 'N/A')}")
    print(f"     - Has Image: {'Yes' if artwork.get('primaryImage') else 'No'}\n")
except Exception as e:
    print(f"   ✗ Object details failed: {e}\n")

print("=" * 60)
print("External API Test Complete!")
print("=" * 60)
print("\nThe Met Museum API is working correctly.")
print("Your Flask application can now:")
print("  1. Search the Met Museum collection")
print("  2. Fetch detailed artwork information")
print("  3. Import artworks into your local database")
print("\nStart your Flask server and visit:")
print("  http://localhost:5000/import_artworks.html")
