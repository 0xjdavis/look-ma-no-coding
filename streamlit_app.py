import streamlit as st
import random
from openai import OpenAI

# Set API Keys (using st.secrets for Streamlit)
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

# Define the OpenAI model
MODEL = 'gpt-4'  # Adjust this to the appropriate model

# Function to generate the PROMPT based on current form values
def generate_prompt():
    return f"""You are a Dungeon Master in a D&D-style adventure game. The player's character is defined as {st.session_state.Class} named {st.session_state.Name} with {st.session_state.Skills} skills and {st.session_state.Inventory}. Guide the player through the story, prompting them to take actions.

When presenting action choices to the player, format them as a numbered list like this:
Player action:
1. [First action option]
2. [Second action option]
3. [Third action option]

Provide 2-4 options for each action prompt. The player will respond with the number of their chosen action.

When a situation requires a skill check or an action with uncertain outcome, explicitly ask the player to roll a d6 (six-sided die). Format your request for a dice roll as follows: '[ROLL THE DICE: reason for rolling]' For example: '[ROLL THE DICE: to see if you successfully track the creature]'

After the player rolls, interpret the result as follows:
1-2 = Failure
3-4 = Partial success
5-6 = Complete success

Wait for the player's roll or action choice before continuing the story."""

# Initialize session state
if 'game_state' not in st.session_state:
    st.session_state.game_state = "not_started"
    st.session_state.messages = []
    st.session_state.roll_result = None
    st.session_state.action_options = []

# Initialize form values in session state
if 'Name' not in st.session_state:
    st.session_state.Name = "Eldar"
    st.session_state.Class = "Hunter"
    st.session_state.Skills = "tracking, animal handling"
    st.session_state.Inventory = "1 Bow, Quiver of 40 arrows"

# Function to update game with new character details
def update_game():
    if st.session_state.game_state == "playing":
        new_prompt = generate_prompt()
        st.session_state.messages[0] = {"role": "system", "content": new_prompt}
        st.session_state.messages.append({
            "role": "system",
            "content": "The player has updated their character. Please acknowledge the changes and continue the story."
        })
        ai_message = get_ai_response(st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": ai_message})
        parse_action_options(ai_message)

# Sidebar form
st.sidebar.title("Create your character")
st.session_state.Name = st.sidebar.text_input("Name", st.session_state.Name, on_change=update_game)
st.session_state.Class = st.sidebar.text_input("Class", st.session_state.Class, on_change=update_game)
st.session_state.Skills = st.sidebar.text_input("Skills", st.session_state.Skills, on_change=update_game)
st.session_state.Inventory = st.sidebar.text_input("Inventory", st.session_state.Inventory, on_change=update_game)

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

# Function to parse action options from AI message
def parse_action_options(message):
    if "Player action:" in message:
        options = message.split("Player action:")[1].strip().split("\n")
        st.session_state.action_options = [opt.split(". ", 1)[1] for opt in options if opt.strip()]
    else:
        st.session_state.action_options = []

# Streamlit UI
st.title("D&D Adventure Game")

# Start game button
if st.session_state.game_state == "not_started":
    if st.button("Start New Adventure"):
        st.session_state.game_state = "playing"
        initial_prompt = generate_prompt()
        st.session_state.messages = [{"role": "system", "content": initial_prompt}]
        st.session_state.messages.append({
            "role": "user",
            "content": "Start a new adventure game. Introduce the setting and provide the first set of action options."
        })
        ai_message = get_ai_response(st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": ai_message})
        parse_action_options(ai_message)
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
            parse_action_options(ai_message)
            st.rerun()
    elif st.session_state.action_options:
        # Display action options
        st.write("Choose your action:")
        for i, option in enumerate(st.session_state.action_options, 1):
            st.write(f"{i}. {option}")
        
        # User input for action choice
        action_choice = st.number_input("Enter the number of your chosen action:", min_value=1, max_value=len(st.session_state.action_options), step=1)
        if st.button("Confirm Action"):
            chosen_action = st.session_state.action_options[action_choice - 1]
            user_message = f"I choose to: {chosen_action}"
            st.session_state.messages.append({"role": "user", "content": user_message})
            ai_message = get_ai_response(st.session_state.messages)
            st.session_state.messages.append({"role": "assistant", "content": ai_message})
            parse_action_options(ai_message)
            st.rerun()
    else:
        st.write("Waiting for the Dungeon Master...")

# Run the Streamlit app
if __name__ == "__main__":
    st.empty()  # This line is here to trigger a rerun when the state changes
