from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Optional
import uuid
from config import QDRANT_URL, QDRANT_API_KEY, COLLECTION_NAME, VECTOR_SIZE
from .embedder import get_embedder
from .chunker import chunk_text

# Initialize Qdrant client with longer timeout
qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY if QDRANT_API_KEY else None,
    timeout=60  # ADD THIS - Increase to 60 seconds
)


def init_collection():
    """
    Initialize or create the Qdrant collection.
    """
    try:
        # Check if collection exists
        collections = qdrant_client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if COLLECTION_NAME in collection_names:
            print(f"✅ Collection '{COLLECTION_NAME}' already exists")
            return
        
        # Create new collection
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE
            )
        )
        print(f"✅ Created collection '{COLLECTION_NAME}'")
        
    except Exception as e:
        print(f"❌ Error initializing collection: {e}")
        raise

def add_document(text: str, metadata: Optional[Dict] = None, batch_size: int = 10) -> int:
    """
    Add a document to the vector database with batching support.
    
    Args:
        text: Document text
        metadata: Optional metadata (source, timestamp, etc.)
        batch_size: Number of chunks to upload at once (default 10)
    
    Returns:
        Number of chunks added
    """
    try:
        # Chunk the text
        chunks = chunk_text(text)
        
        if not chunks:
            print("⚠️ No chunks generated from text")
            return 0
        
        print(f"📝 Generated {len(chunks)} chunks, uploading in batches of {batch_size}...")
        
        # Get embedder
        embedder = get_embedder()
        
        total_uploaded = 0
        
        # Process in batches
        for batch_start in range(0, len(chunks), batch_size):
            batch_end = min(batch_start + batch_size, len(chunks))
            batch_chunks = chunks[batch_start:batch_end]
            
            print(f"   Uploading batch {batch_start//batch_size + 1}/{(len(chunks)-1)//batch_size + 1} ({len(batch_chunks)} chunks)...")
            
            # Generate embeddings for this batch
            vectors = embedder.embed_text(batch_chunks)
            
            # Create points for Qdrant
            points = []
            for i, (chunk, vector) in enumerate(zip(batch_chunks, vectors)):
                point_id = str(uuid.uuid4())
                
                payload = {
                    "text": chunk,
                    "chunk_index": batch_start + i,
                    **(metadata or {})
                }
                
                points.append(
                    PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload
                    )
                )
            
            # Upload this batch to Qdrant
            qdrant_client.upsert(
                collection_name=COLLECTION_NAME,
                points=points,
                wait=True  # Wait for completion before next batch
            )
            
            total_uploaded += len(batch_chunks)
            print(f"   ✅ Batch uploaded ({total_uploaded}/{len(chunks)} total)")
        
        print(f"✅ Added {len(chunks)} chunks to Qdrant")
        return len(chunks)
        
    except Exception as e:
        print(f"❌ Error adding document: {e}")
        raise


def search_documents(query: str, top_k: int = 5) -> List[Dict]:
    """
    Search for relevant documents using semantic search.
    
    Args:
        query: Search query
        top_k: Number of results to return
    
    Returns:
        List of search results with text and metadata
    """
    try:
        # Get embedder
        embedder = get_embedder()
        
        # Embed the query
        query_vector = embedder.embed_query(query)
        
        # Search Qdrant
        search_results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=top_k
        )
        
        # Format results
        results = []
        for result in search_results:
            results.append({
                "text": result.payload.get("text", ""),
                "score": result.score,
                "source": result.payload.get("source", "unknown"),
                "metadata": result.payload
            })
        
        return results
        
    except Exception as e:
        print(f"❌ Error searching documents: {e}")
        return []

def get_collection_info() -> Dict:
    """
    Get information about the collection.
    """
    try:
        collection_info = qdrant_client.get_collection(COLLECTION_NAME)
        return {
            "name": COLLECTION_NAME,
            "vectors_count": collection_info.vectors_count,
            "points_count": collection_info.points_count,
            "status": "healthy"
        }
    except Exception as e:
        return {
            "name": COLLECTION_NAME,
            "status": "error",
            "error": str(e)
        }
