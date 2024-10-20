import streamlit as st
import llama_index
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.openai import OpenAI
from toolhouse import Toolhouse

# Set up API keys
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")
TOOLHOUSE_API_KEY = st.secrets.get("TOOLHOUSE_API_KEY")

# Validate API Keys
if not OPENAI_API_KEY or not TOOLHOUSE_API_KEY:
    st.error("API keys are missing. Please check your configuration.")
    st.stop()

# Initialize OpenAI client and Toolhouse
llm_client = OpenAI(api_key=OPENAI_API_KEY, model="gpt-4", temperature=0.7)
th = Toolhouse(access_token=TOOLHOUSE_API_KEY, provider="openai")

# Load documents and create index
documents = SimpleDirectoryReader("./data").load_data()

# Create the VectorStoreIndex with the LLM service context
index = VectorStoreIndex.from_documents(documents, service_context=llm_client)
chat_engine = index.as_chat_engine(chat_mode="context")

# Streamlit UI setup
st.title("AI Dungeon Master")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input handling
if prompt := st.chat_input("What do you do?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare conversation context
    messages = [{"role": "system", "content": "You are an AI Dungeon Master. Create an engaging and dynamic fantasy adventure based on the player's input. Be creative, descriptive, and adapt the story based on the player's choices."}]
    messages.extend(st.session_state.messages)

    try:
        # Get tools from Toolhouse and make OpenAI chat completion call
        tools = th.get_tools()
        response = llm_client.chat_completion(messages=messages, tools=tools)

        # Update messages and run tools, if applicable
        if tools:
            response = th.run_tools(response)

        # Extract assistant response
        assistant_response = response["choices"][0]["message"]["content"]
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})

        # Display assistant response
        with st.chat_message("assistant"):
            st.markdown(assistant_response)

    except Exception as e:
        st.error(f"Error with the AI service: {e}")

# Sidebar information
st.sidebar.title("Game Information")
st.sidebar.info("This is an AI-powered Dungeon Master. Describe your actions, and the AI will respond with the next part of your adventure. Enjoy your journey!")
