import streamlit as st
from llama_index import VectorStoreIndex, SimpleDirectoryReader, ServiceContext
from llama_index.llms import OpenAI
import os
from toolhouse import memory_store, memory_fetch

# Set up OpenAI API key
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# Toolhouse API key (should be stored securely, e.g., as an environment variable)
TOOLHOUSE_API_KEY = st.secrets["TOOLHOUSE_API_KEY"]

# Load documents (you would replace this with your own fantasy world data)
documents = SimpleDirectoryReader("./data").load_data()

# Create index
service_context = ServiceContext.from_defaults(llm=OpenAI(model="gpt-3.5-turbo", temperature=0.7))
index = VectorStoreIndex.from_documents(documents, service_context=service_context)

# Create chat engine
chat_engine = index.as_chat_engine(
    chat_mode="context",
    system_prompt=(
        "You are an AI Dungeon Master. Create an engaging and dynamic fantasy adventure "
        "based on the player's input. Be creative, descriptive, and adapt the story based "
        "on the player's choices. Ensure a balance of narrative, dialogue, and action."
    )
)

# Function to store memory using Toolhouse memory_store
def store_memory(message):
    memory_to_store = f"User: {message['user']}\nAssistant: {message['assistant']}"
    memory_store(api_key=TOOLHOUSE_API_KEY, memory=memory_to_store)

# Function to fetch memory using Toolhouse memory_fetch
def fetch_memory():
    return memory_fetch(api_key=TOOLHOUSE_API_KEY)

st.title("AI Dungeon Master")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What do you do?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Fetch previous memories
    previous_memories = fetch_memory()

    # Generate AI Dungeon Master response
    response = chat_engine.chat(prompt, context=previous_memories)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response.response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response.response})

    # Store the new memory
    store_memory({"user": prompt, "assistant": response.response})

st.sidebar.title("Game Information")
st.sidebar.info("This is an AI-powered Dungeon Master. Describe your actions, and the AI will respond with the next part of your adventure. Enjoy your journey!")

st.write("Streamlit app is ready to run!")
