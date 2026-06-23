from langchain_core.messages import HumanMessage, AIMessage

# Simple in-memory store: { session_id: [messages] }
_session_store = {}

def get_session_history(session_id: str):
    if session_id not in _session_store:
        _session_store[session_id] = []
    return _session_store[session_id]

def add_user_message(session_id: str, text: str):
    history = get_session_history(session_id)
    history.append(HumanMessage(content=text))
    return history

def add_ai_message(session_id: str, text: str):
    history = get_session_history(session_id)
    history.append(AIMessage(content=text))
    return history

def clear_session(session_id: str):
    _session_store[session_id] = []