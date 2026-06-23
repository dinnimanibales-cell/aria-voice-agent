from typing import List, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, StateGraph

from backend.llm.providers import get_llm
from backend.agent.tools import rag_tool, web_search_tool, sql_tool


class AgentState(TypedDict):
    messages: List[BaseMessage]
    next_action: str
    documents: List[str]


def _last_message_content(state: AgentState) -> str:
    messages = state.get("messages", [])
    if not messages:
        return ""
    return messages[-1].content


def route_request(state: AgentState) -> str:
    last_msg = _last_message_content(state).lower()
    if any(kw in last_msg for kw in ["document", "file", "uploaded", "pdf"]):
        return "rag"
    if any(kw in last_msg for kw in ["search", "latest", "news", "today"]):
        return "web_search"
    if any(kw in last_msg for kw in ["database", "table", "query", "sql"]):
        return "sql"
    return "llm_direct"


def rag_node(state: AgentState) -> AgentState:
    query = _last_message_content(state)
    result = rag_tool(query)
    return {**state, "documents": [result]}


def web_search_node(state: AgentState) -> AgentState:
    query = _last_message_content(state)
    result = web_search_tool(query)
    return {**state, "documents": [result]}


def sql_node(state: AgentState) -> AgentState:
    query = _last_message_content(state)
    result = sql_tool(query)
    return {**state, "documents": [result]}


def llm_node(state: AgentState) -> AgentState:
    llm = get_llm()
    context = "\n".join(state.get("documents", []))
    messages = state.get("messages", [])

    if context:
        messages = [
            HumanMessage(
                content=f"Context:\n{context}\n\nQuestion: {_last_message_content(state)}"
            )
        ]

    response = llm.invoke(messages)
    return {**state, "messages": [*state.get("messages", []), AIMessage(content=response.content)]}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("router", lambda state: {**state, "next_action": route_request(state)})
    graph.add_node("rag", rag_node)
    graph.add_node("web_search", web_search_node)
    graph.add_node("sql", sql_node)
    graph.add_node("llm", llm_node)

    graph.set_entry_point("router")
    graph.add_conditional_edges(
        "router",
        lambda state: state["next_action"],
        {
            "rag": "rag",
            "web_search": "web_search",
            "sql": "sql",
            "llm_direct": "llm",
        },
    )
    graph.add_edge("rag", "llm")
    graph.add_edge("web_search", "llm")
    graph.add_edge("sql", "llm")
    graph.add_edge("llm", END)
    return graph.compile()
