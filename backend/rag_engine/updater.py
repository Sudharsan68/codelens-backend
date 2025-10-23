import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from .retriever import add_document, init_collection
import time

def fetch_page_text(url: str, timeout: int = 10) -> Dict[str, str]:
    """
    Fetch and extract text content from a web page.
    
    Args:
        url: URL of the page to scrape
        timeout: Request timeout in seconds
    
    Returns:
        Dictionary with 'url', 'text', and 'title'
    """
    try:
        print(f"🌐 Fetching: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, timeout=timeout, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get title
        title = soup.title.string if soup.title else url
        
        # Extract text from paragraphs and code blocks
        text_parts = []
        
        # Get paragraphs
        for p in soup.find_all(['p', 'pre', 'code', 'li']):
            text = p.get_text().strip()
            if text and len(text) > 20:  # Filter out very short snippets
                text_parts.append(text)
        
        # If no paragraphs found, get all text
        if not text_parts:
            text_parts = [soup.get_text()]
        
        full_text = "\n\n".join(text_parts)
        
        # Clean up excessive whitespace
        full_text = " ".join(full_text.split())
        
        print(f"✅ Fetched {len(full_text)} characters from {url}")
        
        return {
            "url": url,
            "text": full_text,
            "title": title
        }
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching {url}: {e}")
        return {
            "url": url,
            "text": "",
            "title": "",
            "error": str(e)
        }
    except Exception as e:
        print(f"❌ Error parsing {url}: {e}")
        return {
            "url": url,
            "text": "",
            "title": "",
            "error": str(e)
        }

def update_from_urls(urls: List[str], batch_delay: float = 1.0) -> Dict:
    """
    Scrape multiple URLs and add them to the knowledge base.
    
    Args:
        urls: List of URLs to scrape
        batch_delay: Delay between requests (seconds) to be respectful
    
    Returns:
        Summary of the update operation
    """
    init_collection()
    
    results = {
        "total_urls": len(urls),
        "successful": 0,
        "failed": 0,
        "total_chunks": 0,
        "details": []
    }
    
    for i, url in enumerate(urls, 1):
        print(f"\n📄 Processing {i}/{len(urls)}: {url}")
        
        # Fetch content
        page_data = fetch_page_text(url)
        
        if page_data["text"] and len(page_data["text"]) > 100:
            try:
                # Add to vector database
                chunks_added = add_document(
                    text=page_data["text"],
                    metadata={
                        "source": url,
                        "title": page_data["title"],
                        "type": "web_page"
                    }
                )
                
                results["successful"] += 1
                results["total_chunks"] += chunks_added
                results["details"].append({
                    "url": url,
                    "status": "success",
                    "chunks": chunks_added
                })
                
                print(f"✅ Added {chunks_added} chunks from {url}")
                
            except Exception as e:
                print(f"❌ Error adding {url} to database: {e}")
                results["failed"] += 1
                results["details"].append({
                    "url": url,
                    "status": "failed",
                    "error": str(e)
                })
        else:
            print(f"⚠️ Skipped {url} - insufficient content")
            results["failed"] += 1
            results["details"].append({
                "url": url,
                "status": "skipped",
                "reason": "insufficient_content"
            })
        
        # Be respectful - delay between requests
        if i < len(urls):
            time.sleep(batch_delay)
    
    print(f"\n{'='*60}")
    print(f"📊 Update Summary:")
    print(f"   Total URLs: {results['total_urls']}")
    print(f"   ✅ Successful: {results['successful']}")
    print(f"   ❌ Failed: {results['failed']}")
    print(f"   📝 Total chunks added: {results['total_chunks']}")
    print(f"{'='*60}\n")
    
    return results

def update_single_url(url: str) -> Dict:
    """
    Update knowledge base from a single URL.
    
    Args:
        url: URL to scrape
    
    Returns:
        Result of the operation
    """
    return update_from_urls([url])
