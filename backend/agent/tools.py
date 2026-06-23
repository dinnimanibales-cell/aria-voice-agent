import os
import requests
from backend.rag.retriever import query_documents
from backend.config import settings

def rag_tool(query: str) -> str:
    """Search uploaded documents using RAG."""
    results = query_documents(query)
    if not results:
        return "No relevant documents found."
    return "\n\n".join(results)

def web_search_tool(query: str) -> str:
    """Search the web using Serper API."""
    if not settings.SERPER_API_KEY:
        return "Web search not configured."
    
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": settings.SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        data = response.json()
        results = data.get("organic", [])[:3]
        formatted = "\n".join([f"- {r.get('title')}: {r.get('snippet')}" for r in results])
        return formatted or "No web results found."
    except Exception as e:
        return f"Web search failed: {str(e)}"

def sql_tool(query: str) -> str:
    """Placeholder for natural language to SQL (extend as needed)."""
    return "SQL agent not yet connected to a live database."
