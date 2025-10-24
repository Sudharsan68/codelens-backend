from groq import Groq
from typing import List, Dict
from config import GROQ_API_KEY, LLM_MODEL
from .retriever import search_documents

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

def generate_answer(query: str, top_k: int = 3) -> Dict:
    """
    Generate an answer using RAG (Retrieval-Augmented Generation) with Groq.
    
    Args:
        query: User's question
        top_k: Number of documents to retrieve
    
    Returns:
        Dictionary with answer and sources
    """
    try:
        # Step 1: Retrieve relevant documents
        print(f"🔍 Searching for relevant documents...")
        search_results = search_documents(query, top_k=top_k)
        
        if not search_results:
            return {
                "answer": "I don't have enough information to answer that question. Please update the knowledge base.",
                "sources": [],
                "context_used": False
            }
        
        # Step 2: Build context from retrieved documents
        context_parts = []
        sources = []
        
        for i, result in enumerate(search_results, 1):
            context_parts.append(f"[Source {i}]: {result['text']}")
            sources.append({
                "source": result.get("source", "unknown"),
                "score": float(result.get("score", 0)),
                "text_preview": result['text'][:200] + "..." if len(result['text']) > 200 else result['text']
            })
        
        context = "\n\n".join(context_parts)
        print(f"📚 Found {len(search_results)} relevant chunks")
        
        # Step 3: Create prompt for LLM
        system_prompt = """You are CodeLens, an expert AI assistant for developers. 
Your role is to answer questions about developer documentation and frameworks accurately.

Instructions:
- Use ONLY the provided context to answer questions
- If the context doesn't contain the answer, say so honestly
- Be concise but comprehensive
- Use code examples when relevant
- Cite sources when possible using [Source N] notation
- Format your answers with proper markdown when appropriate"""

        user_prompt = f"""Context from documentation:
{context}

Question: {query}

Answer:"""

        # Step 4: Generate answer using Groq
        print(f"🤖 Generating answer with {LLM_MODEL}...")
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            model=LLM_MODEL,
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stream=False
        )
        
        answer = chat_completion.choices[0].message.content
        print(f"✅ Answer generated successfully")
        
        return {
            "answer": answer,
            "sources": sources,
            "context_used": True,
            "model": LLM_MODEL
        }
        
    except Exception as e:
        print(f"❌ Error generating answer: {e}")
        return {
            "answer": f"Error generating answer: {str(e)}",
            "sources": [],
            "context_used": False,
            "error": str(e)
        }
