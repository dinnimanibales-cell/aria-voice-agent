from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from typing import TypedDict, List
from backend.llm.providers import get_llm
from backend.agent.tools import rag_tool, web_search_tool

class AgentState(TypedDict):
    messages: List
    documents: List
    next_action: str

def router(state: AgentState) -> str:
    last_msg = state["messages"][-1].content.lower()
    
    # Always use RAG for these keywords
    rag_keywords = [
        "document", "file", "pdf", "uploaded", "summarize",
        "summary", "explain", "what does", "what is in",
        "key points", "describe", "tell me about the",
        "according to", "based on the", "in the file",
        "in the document", "nwkrtc", "report", "content"
    ]
    
    web_keywords = [
        "search", "latest", "news", "today", "current",
        "weather", "price", "stock", "trending"
    ]
    
    for kw in rag_keywords:
        if kw in last_msg:
            return "rag"
    
    for kw in web_keywords:
        if kw in last_msg:
            return "web_search"
    
    return "llm_direct"

def rag_node(state: AgentState) -> AgentState:
    query = state["messages"][-1].content
    results = rag_tool(query)
    state["documents"] = results if isinstance(results, list) else [results]
    return state

def web_node(state: AgentState) -> AgentState:
    query = state["messages"][-1].content
    result = web_search_tool(query)
    state["documents"] = [result]
    return state

def llm_node(state: AgentState) -> AgentState:
    llm = get_llm()
    messages = state["messages"]
    documents = state.get("documents", [])

    if documents:
        context = "\n\n".join(documents)
        system = SystemMessage(content=(
            "You are ARIA, a helpful AI assistant. "
            "Use the following document context to answer the user's question accurately and in detail.\n\n"
            f"DOCUMENT CONTEXT:\n{context}\n\n"
            "Answer based on the context above. If the answer is not in the context, say so."
        ))
        final_messages = [system] + list(messages)
    else:
        system = SystemMessage(content=(
            "You are ARIA, a helpful and intelligent AI assistant. "
            "Answer the user's question clearly and helpfully."
        ))
        final_messages = [system] + list(messages)

    response = llm.invoke(final_messages)
    state["messages"].append(AIMessage(content=response.content))
    return state

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("router_node", lambda s: {**s, "next_action": router(s)})
    graph.add_node("rag", rag_node)
    graph.add_node("web_search", web_node)
    graph.add_node("llm", llm_node)

    graph.set_entry_point("router_node")

    graph.add_conditional_edges(
        "router_node",
        lambda s: s["next_action"],
        {
            "rag": "rag",
            "web_search": "web_search",
            "llm_direct": "llm"
        }
    )

    graph.add_edge("rag", "llm")
    graph.add_edge("web_search", "llm")
    graph.add_edge("llm", END)

    return graph.compile()
