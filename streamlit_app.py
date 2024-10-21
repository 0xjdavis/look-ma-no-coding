import streamlit as st
from typing import List
from openai import OpenAI
from toolhouse import Toolhouse

# Let's set our API Keys.
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
TOOLHOUSE_API_KEY = st.secrets["TOOLHOUSE_API_KEY"]
# Please remember to use a safer system to store your API KEYS 
# after finishing the quick start.
client = OpenAI(api_key=OPENAI_API_KEY)
th = Toolhouse(access_token=TOOLHOUSE_API_KEY, provider="openai")
th.set_metadata("id", "10566")
th.set_metadata("timezone", -8)

# Define the OpenAI model we want to use
MODEL = 'gpt-4o-mini'

messages = [{
    "role": "user",
    "content":
        "Generate FizzBuzz code."
        "Execute it to show me the results up to 10."
}]

response = client.chat.completions.create(
  model=MODEL,
  messages=messages,
  # Passes Code Execution as a tool
  tools=th.get_tools()
)

# Runs the Code Execution tool, gets the result, 
# and appends it to the context
messages += th.run_tools(response)

response = client.chat.completions.create(
  model=MODEL,
  messages=messages,
  tools=th.get_tools()
)
# Prints the response with the answer
print(response.choices[0].message.content)
