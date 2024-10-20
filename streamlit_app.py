import streamlit as st
import llama_index
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, ServiceContext
from llama_index.llms.openai import OpenAI as OpenAI

#from openai import OpenAI
from toolhouse import Toolhouse

# Set up API keys
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
TOOLHOUSE_API_KEY = st.secrets["TOOLHOUSE_API_KEY"]

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
th = Toolhouse(access_token=TOOLHOUSE_API_KEY, provider="openai")

MODEL = 'gpt-3.5-turbo'

documents = SimpleDirectoryReader("path_to_your_fantasy_world_data").load_data()
service_context = ServiceContext.from_defaults(llm=OpenAI(model="gpt-3.5-turbo", temperature=0.7))
index = VectorStoreIndex.from_documents(documents, service_context=service_context)
chat_engine = index.as_chat_engine(chat_mode="context")

st.title("AI Dungeon Master")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What do you do?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    messages = [{"role": "system", "content": "You are an AI Dungeon Master. Create an engaging and dynamic fantasy adventure based on the player's input. Be creative, descriptive, and adapt the story based on the player's choices. Ensure a balance of narrative, dialogue, and action."}]
    messages.extend(st.session_state.messages)

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=th.get_tools()
    )

    messages += th.run_tools(response)

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=th.get_tools()
    )

    assistant_response = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    with st.chat_message("assistant"):
        st.markdown(assistant_response)

st.sidebar.title("Game Information")
st.sidebar.info("This is an AI-powered Dungeon Master. Describe your actions, and the AI will respond with the next part of your adventure. Enjoy your journey!")
