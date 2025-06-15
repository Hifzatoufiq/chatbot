import streamlit as st
import google.generativeai as genai

# --- Gemini API Configuration ---
# It's highly recommended to use Streamlit Secrets for API keys, not hardcoding them.
# Example: API_KEY = st.secrets["gemini_api_key"]
API_KEY = "AIzaSyAYasZdwsTqqR1A5B4m3TcRxbrTWcsvlvM"  # Replace with your actual Gemini API key
genai.configure(api_key=API_KEY)

# ✅ Load the Gemini 1.5 Flash model
MODEL_NAME = "gemini-1.5-flash"
model = genai.GenerativeModel(MODEL_NAME)

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "history" not in st.session_state:
    st.session_state.history = []

# --- Sidebar: Chat History Management ---
st.sidebar.title("💬 Chat History")
st.sidebar.markdown("---")

# NEW: Add a "New Chat" button at the top of the sidebar
if st.sidebar.button("➕ New Chat", key="new_chat_button"):
    # 1. Save the current conversation to history if it's not empty and not already the active chat
    if st.session_state.messages:
        # Check if the current conversation is already the last entry in history
        # This prevents saving a duplicate if a chat was just loaded and no new messages added
        if not st.session_state.history or st.session_state.history[-1]["chat"] != st.session_state.messages:
            st.session_state.history.append({
                "title": st.session_state.messages[0]["content"][:50] if st.session_state.messages and st.session_state.messages[0]["content"] else "New Chat",
                "chat": st.session_state.messages.copy() # Make a copy to avoid mutation issues
            })

    # 2. Add a new placeholder for the "New Chat" entry
    # This ensures "New Chat" appears in history immediately
    st.session_state.history.append({
        "title": "New Chat", # Initial title for the new chat
        "chat": [] # Empty chat messages for the new conversation
    })

    # 3. Clear current messages for the main chat interface
    st.session_state.messages = []
    
    st.rerun() # Rerun to update the main chat area and the history in the sidebar

st.sidebar.markdown("---")


# Display chat entries in reverse chronological order
for i, chat_entry in enumerate(reversed(st.session_state.history)):
    original_index = len(st.session_state.history) - 1 - i

    # Use a unique key for the expander to ensure proper state management
    # Ensure the 'New Chat' entry at the end of the history (which is the newest) is expanded by default
    # so the rename option is visible immediately after creation.
    # We check if it's the very last entry in the history (original_index == len(st.session_state.history) - 1)
    # AND if its title is "New Chat" AND if its chat is empty.
    is_newly_created_chat = (original_index == len(st.session_state.history) - 1 and
                             chat_entry['title'] == "New Chat" and
                             not chat_entry['chat'])

    with st.sidebar.expander(f"**{chat_entry['title'] if chat_entry['title'] else 'New Chat'}**", expanded=is_newly_created_chat):
        # Load Chat button
        if st.button("Load Chat", key=f"load_chat_{original_index}"):
            st.session_state.messages = chat_entry["chat"]
            st.rerun()

        # Rename Chat functionality (like an 'edit' option)
        current_title = chat_entry["title"]
        new_title = st.text_input("Rename Chat:", current_title, key=f"rename_chat_{original_index}")
        if new_title != current_title:
            st.session_state.history[original_index]["title"] = new_title
            st.rerun()

        # Delete Chat button
        if st.button("Delete Chat", key=f"delete_chat_{original_index}"):
            st.session_state.history.pop(original_index)
            # If the deleted chat was the one currently displayed, clear main chat area
            if not st.session_state.history or original_index >= len(st.session_state.history): # if the last chat was deleted
                st.session_state.messages = []
            st.rerun()

st.sidebar.markdown("---")

# Clear All History button
if st.sidebar.button("Clear All History", key="clear_all_history"):
    st.session_state.history = []
    st.session_state.messages = [] # Also clear current chat when clearing all history
    st.rerun()

# --- Main Chat Interface ---
st.title("🤖 Gemini Chatbot")
st.markdown("---")

# Display previous messages in the chat interface
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input from the user
user_input = st.chat_input("Type your message here...")

if user_input:
    # 1. Add user's message to the chat display and session state
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 2. Get response from Gemini using a chat session for context
    try:
        # Convert st.session_state.messages into the format expected by the API
        api_history = []
        for msg in st.session_state.messages:
            api_role = "user" if msg["role"] == "user" else "model"
            api_history.append({"role": api_role, "parts": [{"text": msg["content"]}]})

        # Start the chat session with the correctly formatted history
        chat_session = model.start_chat(history=api_history)

        # Send the user's latest message to the chat session
        gemini_response = chat_session.send_message(user_input)

        # Display Gemini's response
        with st.chat_message("assistant"):
            st.markdown(gemini_response.text)

        # 3. Append Gemini's response to messages for display and future history
        st.session_state.messages.append({"role": "assistant", "content": gemini_response.text})

    except Exception as e:
        error_message = f"❌ Gemini API Error: {str(e)}. Please try again."
        with st.chat_message("assistant"):
            st.markdown(error_message)
        st.session_state.messages.append({"role": "assistant", "content": error_message})

    # 4. Update the last history entry with the new messages
    # This logic assumes the last entry in history is the *currently active* chat.
    # When "New Chat" is clicked, we ensure a new empty entry is created, so this will
    # always correctly update that new entry or an existing loaded one.
    if st.session_state.history: # Ensure history is not empty
        last_history_entry = st.session_state.history[-1]

        # Update the chat content
        last_history_entry["chat"] = st.session_state.messages.copy()

        # Update the title if it's still "New Chat" and a meaningful input exists
        if last_history_entry["title"] == "New Chat" and len(user_input) > 0:
            last_history_entry["title"] = user_input[:50]
    else:
        # This case should ideally not be hit if "New Chat" always adds an entry,
        # but it's a fallback for the very first message if app started fresh.
        st.session_state.history.append({
            "title": user_input[:50] if len(user_input) > 0 else "New Chat",
            "chat": st.session_state.messages.copy()
        })
    
    st.rerun() # Rerun to update the sidebar and main chat