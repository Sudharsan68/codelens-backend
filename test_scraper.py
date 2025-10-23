import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_scrape_single_url():
    """Test scraping a single URL."""
    print("\n" + "="*60)
    print("TEST: Scraping Single URL")
    print("="*60)
    
    data = {
        "url": "https://fastapi.tiangolo.com/"
    }
    
    response = requests.post(f"{BASE_URL}/update_from_url", json=data)
    print(f"Status: {response.status_code}")
    print(f"Result:\n{json.dumps(response.json(), indent=2)}")

def test_predefined_source():
    """Test updating from predefined source."""
    print("\n" + "="*60)
    print("TEST: Update Predefined Source (FastAPI)")
    print("="*60)
    
    response = requests.post(f"{BASE_URL}/update_predefined/fastapi")
    print(f"Status: {response.status_code}")
    print(f"Result:\n{json.dumps(response.json(), indent=2)}")
    
    print("\n⏳ Waiting 10 seconds for scraping to complete...")
    time.sleep(10)
    
    # Check collection info
    info_response = requests.get(f"{BASE_URL}/collection_info")
    print(f"\n📊 Collection Info:\n{json.dumps(info_response.json(), indent=2)}")

def test_ask_after_scraping():
    """Test asking a question after scraping."""
    print("\n" + "="*60)
    print("TEST: Ask Question After Scraping")
    print("="*60)
    
    data = {
        "query": "How do I create a FastAPI application?"
    }
    
    response = requests.post(f"{BASE_URL}/ask", json=data)
    result = response.json()
    
    print(f"\n💬 Question: {data['query']}")
    print(f"\n🤖 Answer:\n{result.get('answer', 'No answer')}")
    print(f"\n📚 Sources used: {len(result.get('sources', []))}")

if __name__ == "__main__":
    print("🧪 CodeLens Web Scraper Tests")
    print("Make sure FastAPI server is running!\n")
    
    # Test 1: Scrape single URL
    test_scrape_single_url()
    
    # Test 2: Use predefined source
    # test_predefined_source()  # Uncomment to test
    
    # Test 3: Ask question after scraping
    print("\n⏳ Waiting 5 seconds before asking question...")
    time.sleep(5)
    test_ask_after_scraping()
    
    print("\n✅ All tests complete!")
