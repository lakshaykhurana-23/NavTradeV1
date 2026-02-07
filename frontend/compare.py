"""
Streamlit interface for comparing multiple LLM responses side-by-side.
"""
import streamlit as st
import uuid
import time
import threading
from queue import Queue, Empty
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


def concurrent_stream_generator(prompt: str, left_model: str, right_model: str, thread_id: str):
    """
    Generator that yields updates from both models concurrently.
    
    Args:
        prompt: User's input message
        left_model: Left panel model name
        right_model: Right panel model name
        thread_id: Conversation thread ID
        
    Yields:
        Tuples of (left_text, right_text, left_done, right_done)
    """
    left_queue = Queue()
    right_queue = Queue()
    
    left_done = threading.Event()
    right_done = threading.Event()
    
    def run_left():
        try:
            for chunk in stream_from_backend(prompt, left_model, thread_id):
                left_queue.put(('chunk', chunk))
        except Exception as e:
            left_queue.put(('error', str(e)))
        finally:
            left_done.set()
    
    def run_right():
        try:
            for chunk in stream_from_backend(prompt, right_model, thread_id):
                right_queue.put(('chunk', chunk))
        except Exception as e:
            right_queue.put(('error', str(e)))
        finally:
            right_done.set()
    
    # Start threads
    t1 = threading.Thread(target=run_left, daemon=True)
    t2 = threading.Thread(target=run_right, daemon=True)
    
    t1.start()
    t2.start()
    
    left_text = ""
    right_text = ""
    
    # Poll both queues until both threads are done
    while not (left_done.is_set() and right_done.is_set() and
               left_queue.empty() and right_queue.empty()):
        
        updated = False
        
        # Process left queue
        try:
            msg_type, data = left_queue.get_nowait()
            if msg_type == 'chunk':
                left_text += data
                updated = True
        except Empty:
            pass
        
        # Process right queue
        try:
            msg_type, data = right_queue.get_nowait()
            if msg_type == 'chunk':
                right_text += data
                updated = True
        except Empty:
            pass
        
        # Yield current state if updated
        if updated:
            yield (left_text, right_text, left_done.is_set(), right_done.is_set())
        else:
            time.sleep(0.01)
    
    # Final yield to ensure everything is captured
    yield (left_text, right_text, True, True)
    
    # Wait for threads to complete
    t1.join(timeout=1)
    t2.join(timeout=1)


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
    st.title("🧠 LLM Compare")
    
    if st.button("+ New Compare Thread", use_container_width=True):
        tid = str(uuid.uuid4())[:8]
        st.session_state.threads[tid] = {
            "id": tid,
            "title": "New comparison",
            "compare_models": ["Model A", "Model B"],
            "messages": []
        }
        st.session_state.active_thread = tid
        st.rerun()
    
    st.divider()
    
    for tid, thread in st.session_state.threads.items():
        if st.button(thread["title"], key=tid, use_container_width=True):
            st.session_state.active_thread = tid
            st.rerun()


# ============================================================================
# Main Compare Interface
# ============================================================================

if not st.session_state.active_thread:
    st.info("👈 Start a comparison")
    st.stop()

thread = st.session_state.threads[st.session_state.active_thread]

# Top bar with model selectors
st.markdown("### 🔀 Compare Models")

col1, col2 = st.columns(2)

with col1:
    thread["compare_models"][0] = st.selectbox(
        "Left Model",
        MODEL_NAMES,
        index=MODEL_NAMES.index(thread["compare_models"][0]),
        key=f"left_{thread['id']}"
    )

with col2:
    thread["compare_models"][1] = st.selectbox(
        "Right Model",
        MODEL_NAMES,
        index=MODEL_NAMES.index(thread["compare_models"][1]),
        key=f"right_{thread['id']}"
    )

# Render history
for msg in thread["messages"]:
    with st.chat_message("user"):
        st.markdown(msg["user"])
    
    with st.chat_message("assistant"):
        left, right = st.columns(2)
        
        with left:
            st.markdown(f"### 🤖 {msg['left_model']}")
            st.markdown(msg["left"])
        
        with right:
            st.markdown(f"### 🤖 {msg['right_model']}")
            st.markdown(msg["right"])

# Chat input
prompt = st.chat_input("Ask once, compare outputs")

if prompt:
    # Save user message placeholder
    thread["messages"].append({
        "user": prompt,
        "left_model": thread["compare_models"][0],
        "right_model": thread["compare_models"][1],
        "left": "",
        "right": "",
    })
    
    # Render user message immediately
    with st.chat_message("user"):
        st.markdown(prompt)
    
    left_model, right_model = thread["compare_models"]
    
    # Stream assistant responses concurrently
    with st.chat_message("assistant"):
        col_l, col_r = st.columns(2)
        
        with col_l:
            st.markdown(f"### 🤖 {left_model}")
            left_box = st.empty()
        
        with col_r:
            st.markdown(f"### 🤖 {right_model}")
            right_box = st.empty()
        
        # Stream both models concurrently
        final_left = ""
        final_right = ""
        
        for left_text, right_text, left_done, right_done in concurrent_stream_generator(
            prompt, left_model, right_model, thread["id"]
        ):
            left_box.markdown(left_text)
            right_box.markdown(right_text)
            final_left = left_text
            final_right = right_text
    
    # Persist messages
    thread["messages"][-1]["left"] = final_left
    thread["messages"][-1]["right"] = final_right
    
    # Update thread title
    thread["title"] = prompt[:30]
    
    st.rerun()
