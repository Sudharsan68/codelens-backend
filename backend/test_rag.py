import requests
import json

# Base URL for your API
BASE_URL = "http://127.0.0.1:8000"

def test_add_document():
    """Test adding a document to the knowledge base."""
    print("\n" + "="*50)
    print("TEST 1: Adding a document")
    print("="*50)
    
    doc_data = {
        "text": """FastAPI is a modern, fast (high-performance) web framework for building APIs with Python 3.7+ based on standard Python type hints. 
        
        Key features of FastAPI include:
        - Very high performance, on par with NodeJS and Go
        - Fast to code: Increase the speed to develop features by about 200% to 300%
        - Fewer bugs: Reduce about 40% of human induced errors
        - Intuitive: Great editor support with auto-completion everywhere
        - Easy: Designed to be easy to use and learn
        - Short: Minimize code duplication
        - Robust: Get production-ready code with automatic interactive documentation
        - Standards-based: Based on and fully compatible with OpenAPI and JSON Schema
        
        FastAPI was created by Sebastián Ramírez and is built on top of Starlette for web parts and Pydantic for data parts.""",
        "source": "FastAPI Documentation"
    }
    
    response = requests.post(f"{BASE_URL}/add_document", json=doc_data)
    print(f"\n✅ Status Code: {response.status_code}")
    print(f"📄 Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def test_ask_question():
    """Test asking a question."""
    print("\n" + "="*50)
    print("TEST 2: Asking a question")
    print("="*50)
    
    query_data = {
        "query": "What is FastAPI and what are its key features?"
    }
    
    response = requests.post(f"{BASE_URL}/ask", json=query_data)
    print(f"\n✅ Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n💬 Question: {query_data['query']}")
        print(f"\n🤖 Answer:\n{result.get('answer', 'No answer')}")
        print(f"\n📚 Number of sources used: {len(result.get('sources', []))}")
        
        if result.get('sources'):
            print("\n📖 Sources:")
            for i, source in enumerate(result['sources'], 1):
                print(f"  {i}. {source.get('source')} (Score: {source.get('score', 0):.3f})")
    else:
        print(f"❌ Error: {response.text}")
    
    return response.status_code == 200

def test_collection_info():
    """Test getting collection information."""
    print("\n" + "="*50)
    print("TEST 3: Collection Info")
    print("="*50)
    
    response = requests.get(f"{BASE_URL}/collection_info")
    print(f"\n✅ Status Code: {response.status_code}")
    print(f"📊 Collection Info: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def main():
    """Run all tests."""
    print("\n🚀 Starting CodeLens RAG System Tests...")
    print("Make sure your FastAPI server is running on http://127.0.0.1:8000")
    
    try:
        # Test if server is running
        response = requests.get(f"{BASE_URL}/")
        print(f"\n✅ Server is running: {response.json().get('message')}")
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to server!")
        print("Please start the server with: uvicorn main:app --reload")
        return
    
    # Run tests
    results = []
    results.append(("Add Document", test_add_document()))
    results.append(("Ask Question", test_ask_question()))
    results.append(("Collection Info", test_collection_info()))
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("\n🎉 All tests passed! Your RAG system is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
