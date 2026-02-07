"""
Streamlit chat interface for LLM comparison.
"""
import streamlit as st
import uuid
import requests

BASE_URL = "http://127.0.0.1:8000"
MODEL_NAMES = ["Model A", "Model B", "Model C"]


def stream_from_backend(prompt: str, model: str, thread_id: str):
    """
    Stream response from backend API.
    
    Args:
        prompt: User's input message
        model: Selected model name
        thread_id: Conversation thread ID
        
    Yields:
        Response chunks from the backend
    """
    payload = {
        "userInput": prompt,
        "model": model.lower().replace(" ", "_"),
        "threadId": thread_id,
    }
    
    with requests.post(
        f"{BASE_URL}/result",
        json=payload,
        stream=True,
        timeout=(5, None),
    ) as r:
        r.raise_for_status()
        
        for chunk in r.iter_content(chunk_size=None):
            if chunk:
                yield chunk.decode("utf-8")


# ============================================================================
# Session State
# ============================================================================

if "threads" not in st.session_state:
    st.session_state.threads = {}

if "active_thread" not in st.session_state:
    st.session_state.active_thread = None


# ============================================================================
# Sidebar
# ============================================================================

with st.sidebar:
    st.title("🧠 LLM Lab")
    
    if st.button("+ New Thread", use_container_width=True):
        tid = str(uuid.uuid4())[:8]
        st.session_state.threads[tid] = {
            "id": tid,
            "title": "New chat",
            "model": "Model A",
            "messages": []
        }
        st.session_state.active_thread = tid
    
    st.divider()
    
    for tid, thread in st.session_state.threads.items():
        if st.button(thread["title"], key=tid, use_container_width=True):
            st.session_state.active_thread = tid


# ============================================================================
# Main Chat Interface
# ============================================================================

if not st.session_state.active_thread:
    st.info("👈 Start a new chat")
    st.stop()

thread = st.session_state.threads[st.session_state.active_thread]

# Top bar with model selector
top = st.container()
with top:
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### 💬 Chat")
    
    with col2:
        thread["model"] = st.selectbox(
            "Model",
            MODEL_NAMES,
            index=MODEL_NAMES.index(thread["model"]),
            label_visibility="collapsed"
        )

# Render chat history
for msg in thread["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
prompt = st.chat_input("Message")

if prompt:
    # Save user message
    thread["messages"].append({
        "role": "user",
        "content": prompt
    })
    
    # Show user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Stream assistant response
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        
        for token in stream_from_backend(
            prompt=prompt,
            model=thread["model"],
            thread_id=thread["id"],
        ):
            full_response += token
            placeholder.markdown(full_response)
    
    # Save assistant message
    thread["messages"].append({
        "role": "assistant",
        "content": full_response
    })
    
    # Update thread title
    thread["title"] = prompt[:30]
    
    st.rerun()
