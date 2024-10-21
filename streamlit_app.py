import streamlit as st
import random
from openai import OpenAI

# Set API Keys (using st.secrets for Streamlit)
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

# Define the OpenAI model
MODEL = 'gpt-4'  # Adjust this to the appropriate model

st.sidebar.title("Create your character")
Name = st.sidebar.text_input("Name", "Eldar")
Class = st.sidebar.text_input("Class", "Hunter")
Skills = st.sidebar.text_input("Skills", "tracking, animal handling")
Inventory = st.sidebar.text_input("Inventory", "1 Bow, Quiver of 40 arrows")

PROMPT = "You are a Dungeon Master in a D&D-style adventure game. The player's character is defined as " + Class + " named " + Name + " with " + Skills + " skills and " + Inventory + ". Guide the player through the story, prompting them to take actions. When a situation requires a skill check or an action with uncertain outcome, explicitly ask the player to roll a d6 (six-sided die). Format your request for a dice roll as follows: '[ROLL THE DICE: reason for rolling]' For example: '[ROLL THE DICE: to see if you successfully track the creature]' After the player rolls, interpret the result as follows: 1-2 = Failure. 3-4 = Partial success. 5-6 = Complete success. Wait for the player's roll before continuing the story."
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
        messages=messages
    )
    return response.choices[0].message.content

# Function to display chat history
def display_chat_history():
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.write(message["content"])

# Function to check if AI is requesting a dice roll
def is_roll_request(message):
    return '[ROLL THE DICE:' in message

# Streamlit UI
st.title("D&D Adventure Game")

# Start game button
if st.session_state.game_state == "not_started":
    if st.button("Start New Adventure"):
        st.session_state.game_state = "playing"
        st.session_state.messages.append({
            "role": "user",
            "content": "Start a new adventure game. Introduce the setting."
        })
        ai_message = get_ai_response(st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": ai_message})
        st.rerun()

# Main game loop
if st.session_state.game_state == "playing":
    display_chat_history()

    # Check if the last message is a roll request
    if st.session_state.messages and is_roll_request(st.session_state.messages[-1]["content"]):
        if st.button("Roll Dice"):
            roll_result = roll_d6()
            roll_message = f"You rolled a {roll_result}."
            st.session_state.messages.append({"role": "user", "content": roll_message})
            ai_message = get_ai_response(st.session_state.messages)
            st.session_state.messages.append({"role": "assistant", "content": ai_message})
            st.rerun()
    else:
        # User input
        user_input = st.chat_input("What would you like to do?")
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            ai_message = get_ai_response(st.session_state.messages)
            st.session_state.messages.append({"role": "assistant", "content": ai_message})
            st.rerun()

# Run the Streamlit app
if __name__ == "__main__":
    st.empty()  # This line is here to trigger a rerun when the state changes
