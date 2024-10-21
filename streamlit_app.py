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

# Initialize session state
if 'game_state' not in st.session_state:
    st.session_state.game_state = "not_started"
    st.session_state.messages = [{
        "role": "system",
        "content": "You are a Dungeon Master in a D&D-style adventure game. Guide the player through the story, prompting them to take actions and roll dice when necessary. Use a d6 (six-sided die) for all rolls."
    }]

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

# Function to handle user input
def handle_user_input(user_input):
    st.session_state.messages.append({"role": "user", "content": user_input})
    ai_message = get_ai_response(st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": ai_message})
    
    with st.chat_message("assistant"):
        st.write(ai_message)
    
    if "roll" in ai_message.lower() and "dice" in ai_message.lower():
        st.session_state.game_state = "waiting_for_roll"

# Function to handle dice roll
def handle_dice_roll():
    roll_result = roll_d6()
    roll_message = f"You rolled a {roll_result}."
    st.session_state.messages.append({"role": "user", "content": roll_message})
    
    with st.chat_message("user"):
        st.write(roll_message)
    
    ai_message = get_ai_response(st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": ai_message})
    
    with st.chat_message("assistant"):
        st.write(ai_message)
    
    st.session_state.game_state = "continue"

# Streamlit UI
st.title("D&D Adventure Game")

# Main game container
game_container = st.empty()

# Game loop
while True:
    with game_container.container():
        if st.session_state.game_state == "not_started":
            if st.button("Start New Adventure"):
                st.session_state.game_state = "intro"
                st.session_state.messages.append({
                    "role": "user",
                    "content": "Start a new adventure game. Introduce the setting and the player's character."
                })
                st.experimental_rerun()
        
        elif st.session_state.game_state in ["intro", "continue"]:
            display_chat_history()
            user_input = st.chat_input("What would you like to do?")
            if user_input:
                handle_user_input(user_input)
                st.experimental_rerun()
        
        elif st.session_state.game_state == "waiting_for_roll":
            display_chat_history()
            if st.button("Roll Dice"):
                handle_dice_roll()
                st.experimental_rerun()
    
    # Break the loop to prevent infinite rerunning
    break

# Run the Streamlit app
if __name__ == "__main__":
    st.empty()  # This line is here to trigger a rerun when the state changes
