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
th = Toolhouse(api_key=TOOLHOUSE_API_KEY, provider="openai")
th.set_metadata("id", "10566")
th.set_metadata("timezone", -8)

# Define the OpenAI model we want to use
MODEL = 'gpt-4o-mini'

messages = [{
    "role": "user",
    "content":
        "Create the outline for a wonderful adventure in the world of imaginary dungeons and dragons world. Act as the Dungeon Master propting the user and other players to role when it is their turn. Outline the rules in terms of the number the player roles and what happens to their character."
        "Start the game off with communicating to all the players the story and who the players are. Prompt the user to take an action based off of rolling a number between 1 and 6."
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
st.write(response.choices[0].message.content)
