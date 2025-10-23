from sentence_transformers import SentenceTransformer
from typing import List, Union
from config import EMBEDDING_MODEL, VECTOR_SIZE

class Embedder:
    """
    Handles text embedding using Sentence Transformers.
    """
    
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        """
        Initialize the embedding model.
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        print(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        print("✅ Embedding model loaded successfully!")
    
    def embed_text(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """
        Convert text(s) to vector embeddings.
        
        Args:
            texts: Single text string or list of text strings
        
        Returns:
            List of embedding vectors
        """
        # Convert single string to list
        if isinstance(texts, str):
            texts = [texts]
        
        # Generate embeddings
        embeddings = self.model.encode(texts, show_progress_bar=False)
        
        # Convert to list format
        return embeddings.tolist()
    
    def embed_query(self, query: str) -> List[float]:
        """
        Embed a single query string.
        
        Args:
            query: Query text
        
        Returns:
            Single embedding vector
        """
        return self.embed_text(query)[0]

# Create a global instance
_embedder_instance = None

def get_embedder() -> Embedder:
    """
    Get or create a singleton embedder instance.
    """
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = Embedder()
    return _embedder_instance
