from PyPDF2 import PdfReader
from typing import Dict
from .retriever import add_document, init_collection
import os

def load_pdf(file_path: str) -> Dict:
    """
    Extract text from a PDF file and add to knowledge base.
    
    Args:
        file_path: Path to the PDF file
    
    Returns:
        Summary of the operation
    """
    try:
        init_collection()
        
        if not os.path.exists(file_path):
            return {
                "status": "failed",
                "error": f"File not found: {file_path}"
            }
        
        print(f"📄 Loading PDF: {file_path}")
        
        # Read PDF
        reader = PdfReader(file_path)
        num_pages = len(reader.pages)
        
        print(f"📖 PDF has {num_pages} pages")
        
        # Extract text from all pages
        text_parts = []
        for i, page in enumerate(reader.pages, 1):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
                print(f"   Extracted page {i}/{num_pages}")
        
        full_text = "\n\n".join(text_parts)
        
        if not full_text or len(full_text) < 100:
            return {
                "status": "failed",
                "error": "Insufficient text extracted from PDF"
            }
        
        # Add to vector database
        chunks_added = add_document(
            text=full_text,
            metadata={
                "source": os.path.basename(file_path),
                "type": "pdf",
                "pages": num_pages,
                "file_path": file_path
            }
        )
        
        print(f"✅ Added {chunks_added} chunks from PDF")
        
        return {
            "status": "success",
            "file": file_path,
            "pages": num_pages,
            "chunks_added": chunks_added,
            "text_length": len(full_text)
        }
        
    except Exception as e:
        print(f"❌ Error loading PDF: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }

def load_multiple_pdfs(directory: str) -> Dict:
    """
    Load all PDF files from a directory.
    
    Args:
        directory: Path to directory containing PDFs
    
    Returns:
        Summary of all operations
    """
    if not os.path.exists(directory):
        return {
            "status": "failed",
            "error": f"Directory not found: {directory}"
        }
    
    pdf_files = [f for f in os.listdir(directory) if f.endswith('.pdf')]
    
    if not pdf_files:
        return {
            "status": "failed",
            "error": f"No PDF files found in {directory}"
        }
    
    results = {
        "total_files": len(pdf_files),
        "successful": 0,
        "failed": 0,
        "total_chunks": 0,
        "details": []
    }
    
    for pdf_file in pdf_files:
        file_path = os.path.join(directory, pdf_file)
        result = load_pdf(file_path)
        
        if result["status"] == "success":
            results["successful"] += 1
            results["total_chunks"] += result["chunks_added"]
        else:
            results["failed"] += 1
        
        results["details"].append(result)
    
    return results
