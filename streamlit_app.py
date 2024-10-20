import streamlit as st
import llama_index
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, ServiceContext
from llama_index.llms.openai import OpenAI
from llama_index.memory import ChatMemoryBuffer
import os

# Set up OpenAI API key
TOOLHOUSE_API_KEY = st.secrets["TOOLHOUSE_API_KEY"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# Load documents (you would replace this with your own fantasy world data)
documents = SimpleDirectoryReader("path_to_your_fantasy_world_data").load_data()

# Create index
service_context = ServiceContext.from_defaults(llm=OpenAI(model="gpt-3.5-turbo", temperature=0.7))
index = VectorStoreIndex.from_documents(documents, service_context=service_context)

# Create chat engine
memory = ChatMemoryBuffer.from_defaults(token_limit=1500)
chat_engine = index.as_chat_engine(
    chat_mode="context",
    memory=memory,
    system_prompt=(
        "You are an AI Dungeon Master. Create an engaging and dynamic fantasy adventure "
        "based on the player's input. Be creative, descriptive, and adapt the story based "
        "on the player's choices. Ensure a balance of narrative, dialogue, and action."
    )
)

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

    # Generate AI Dungeon Master response
    response = chat_engine.chat(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response.response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response.response})

st.sidebar.title("Game Information")
st.sidebar.info("This is an AI-powered Dungeon Master. Describe your actions, and the AI will respond with the next part of your adventure. Enjoy your journey!")

print("Streamlit app is ready to run!")
