import streamlit as st
import random
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

st.sidebar.title("Create your character")
Name = st.sidebar.text_input("Name", "Eldar")
Class = st.sidebar.text_input("Class", "Hunter")
Skills = st.sidebar.text_input("Skills", "tracking, animal handling")
Inventory = st.sidebar.text_input("Inventory", "1 Bow, Quiver of 40 arrows")

PROMPT = f"You are a Dungeon Master in a D&D-style adventure game. Guide the player through the story, prompting them to take actions and roll dice when necessary. Use a d6 (six-sided die) for all rolls."

# Initialize session state
if 'game_state' not in st.session_state:
    st.session_state.game_state = "not_started"
    st.session_state.messages = [{"role": "system", "content": PROMPT}]
    st.session_state.roll_result = None

# Function to roll a d6
def roll_d6():
    return random.randint(1, 6)

# Function to get AI response
def get_ai_response(messages):
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=th.get_tools()
    )
    return response.choices[0].message.content

# Function to display chat history
def display_chat_history():
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.write(message["content"])

# Streamlit UI
st.title("D&D Adventure Game")

# Start game button
if st.session_state.game_state == "not_started":
    if st.button("Start New Adventure"):
        st.session_state.game_state = "playing"
        st.session_state.messages.append({
            "role": "user",
            "content": "Start a new adventure game. Introduce the setting. The player's character will be defined as {Class} named {Name} with {Skills} skills and {Inventory}. "
        })
        ai_message = get_ai_response(st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": ai_message})
        st.rerun()

# Main game loop
if st.session_state.game_state in ["playing", "ready_to_roll"]:
    display_chat_history()

    # Dice rolling section
    if "roll" in st.session_state.messages[-1]["content"].lower() and "dice" in st.session_state.messages[-1]["content"].lower():
        if st.session_state.game_state == "playing":
            if st.button("Roll Dice"):
                st.session_state.game_state = "ready_to_roll"
                st.rerun()
        elif st.session_state.game_state == "ready_to_roll":
            if st.button("Submit Roll"):
                st.session_state.roll_result = roll_d6()
                roll_message = f"You rolled a {st.session_state.roll_result}."
                st.session_state.messages.append({"role": "user", "content": roll_message})
                ai_message = get_ai_response(st.session_state.messages)
                st.session_state.messages.append({"role": "assistant", "content": ai_message})
                st.session_state.game_state = "playing"
                st.rerun()

    # Display roll result
    if st.session_state.roll_result is not None:
        st.success(f"Last roll result: {st.session_state.roll_result}")
        st.session_state.roll_result = None

    # User input
    if st.session_state.game_state == "playing":
        user_input = st.chat_input("What would you like to do?")
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            ai_message = get_ai_response(st.session_state.messages)
            st.session_state.messages.append({"role": "assistant", "content": ai_message})
            st.rerun()

# Run the Streamlit app
if __name__ == "__main__":
    st.empty()  # This line is here to trigger a rerun when the state changes
