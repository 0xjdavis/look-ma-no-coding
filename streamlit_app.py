import streamlit as st
import openai
import llama_index
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.openai import OpenAI as LlamaOpenAI

from toolhouse import Toolhouse

# Set up API keys
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")
TOOLHOUSE_API_KEY = st.secrets.get("TOOLHOUSE_API_KEY")

# Validate API Keys
if not OPENAI_API_KEY or not TOOLHOUSE_API_KEY:
    st.error("API keys are missing. Please check your configuration.")
    st.stop()

# Initialize OpenAI client
openai.api_key = OPENAI_API_KEY

# Initialize LlamaIndex components
embed_model = OpenAIEmbedding(model="text-embedding-3-small")
node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=20)
llm = LlamaOpenAI(model="gpt-3.5-turbo", api_key=OPENAI_API_KEY)
service_context = Settings.llm(
    llm=llm,
    embed_model=embed_model,
    node_parser=node_parser
)

# Initialize Toolhouse
th = Toolhouse(access_token=TOOLHOUSE_API_KEY, provider="openai")

# Load documents and create index
try:
    documents = SimpleDirectoryReader("./data").load_data()
    index = VectorStoreIndex.from_documents(documents, service_context=service_context)
    chat_engine = index.as_chat_engine(chat_mode="context")
except Exception as e:
    st.error(f"Error loading documents or creating index: {e}")
    st.stop()

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
    messages = [
        {"role": "system", "content": "You are an AI Dungeon Master. Create an engaging and dynamic fantasy adventure based on the player's input. Be creative, descriptive, and adapt the story based on the player's choices. Ensure a balance of narrative, dialogue, and action."}
    ]
    messages.extend(st.session_state.messages)

    try:
        # Get response from LlamaIndex chat engine
        response = chat_engine.chat(prompt)

        # Get tools from Toolhouse
        tools = th.get_tools()

        # Run tools, if applicable
        if tools:
            toolhouse_response = th.run_tools(response.response)
            assistant_response = toolhouse_response.choices[0]["message"]["content"]
        else:
            assistant_response = response.response

        st.session_state.messages.append({"role": "assistant", "content": assistant_response})

        # Display assistant response
        with st.chat_message("assistant"):
            st.markdown(assistant_response)

    except Exception as e:
        st.error(f"Error with the AI service: {e}")

# Sidebar information
st.sidebar.title("Game Information")
st.sidebar.info("This is an AI-powered Dungeon Master. Describe your actions, and the AI will respond with the next part of your adventure. Enjoy your journey!")
