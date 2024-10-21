import streamlit as st
import random
from typing import List
from openai import OpenAI
from toolhouse import Toolhouse

# Set API Keys (using st.secrets for Streamlit)
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
TOOLHOUSE_API_KEY = st.secrets["TOOLHOUSE_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)
th = Toolhouse(api_key=TOOLHOUSE_API_KEY, provider="openai")
th.set_metadata("id", "10566")
th.set_metadata("timezone", -8)

# Define the OpenAI model
MODEL = 'gpt-4o-mini'

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = [{
        "role": "system",
        "content": "You are a Dungeon Master in a D&D-style adventure game. Guide the player through the story, prompting them to take actions and roll dice when necessary. Use a d6 (six-sided die) for all rolls."
    },
    {
        "role": "user",
        "content": "Start a new adventure game. Introduce the setting and the player's character."
    }]

if 'game_state' not in st.session_state:
    st.session_state.game_state = "intro"

# Function to roll a d6
def roll_d6():
    return random.randint(1, 6)

# Streamlit UI
st.title("D&D Adventure Game")

# Display chat history
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.write(message["content"])

# User input and dice rolling
if st.session_state.game_state != "waiting_for_roll":
    user_input = st.chat_input("What would you like to do?")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Get AI response
        response = client.chat.completions.create(
            model=MODEL,
            messages=st.session_state.messages,
            tools=th.get_tools()
        )

        ai_message = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": ai_message})

        with st.chat_message("assistant"):
            st.write(ai_message)

        # Check if the AI is asking for a dice roll
        if "roll" in ai_message.lower() and "dice" in ai_message.lower():
            st.session_state.game_state = "waiting_for_roll"

# Dice rolling button
if st.session_state.game_state == "waiting_for_roll":
    if st.button("Roll Dice"):
        roll_result = roll_d6()
        roll_message = f"You rolled a {roll_result}."
        st.session_state.messages.append({"role": "user", "content": roll_message})

        with st.chat_message("user"):
            st.write(roll_message)

        # Get AI response to the roll
        response = client.chat.completions.create(
            model=MODEL,
            messages=st.session_state.messages,
            tools=th.get_tools()
        )

        ai_message = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": ai_message})

        with st.chat_message("assistant"):
            st.write(ai_message)

        st.session_state.game_state = "continue"

# Run the Streamlit app
if __name__ == "__main__":
    st.empty() # This line is here to trigger a rerun when the state changes
