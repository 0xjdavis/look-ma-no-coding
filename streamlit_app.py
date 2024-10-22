import streamlit as st
import random
import os
import requests
from openai import OpenAI
import time
from gtts import gTTS
from io import BytesIO
from PIL import Image

# Set API Keys (using st.secrets for Streamlit)
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

# Define the OpenAI model
MODEL = 'gpt-4'

# Function to generate the PROMPT based on current form values
def generate_prompt():
    return f"""You are a Dungeon Master in a D&D-style adventure game. The player's character is defined as {st.session_state.Class} named {st.session_state.Name} with {st.session_state.Skills} skills and {st.session_state.Inventory}. The player has {st.session_state.health}/10 health remaining. Guide the player through the story, prompting them to take actions.

Your goal is to guide the player towards finding a magical artifact called the Crystal of Power. Finding this artifact is the win condition for the game.

Include opportunities for the player to heal (finding healing potions, friendly healers, etc.) or take damage (combat, traps, etc.). Track their health carefully.

When presenting action choices to the player, format them as a numbered list like this:
Player action:
1. [First action option]
2. [Second action option]
3. [Third action option]

Provide 2-4 options for each action prompt. The player will respond with their chosen action.

When a situation requires a skill check or an action with uncertain outcome, explicitly ask the player to roll a d6 (six-sided die). Format your request for a dice roll as follows: '[ROLL THE DICE: reason for rolling]' For example: '[ROLL THE DICE: to see if you successfully track the creature]'

After the player rolls, interpret the result as follows:
1-2 = Failure (may cause 1-3 damage)
3-4 = Partial success (may cause 0-1 damage)
5-6 = Complete success (no damage)

If the player finds the Crystal of Power, respond with: [VICTORY: Congratulations! You have won the game!]
If the player's health reaches 0, respond with: [DEFEAT: Your health has reached 0. Game Over.]

Wait for the player's roll or action choice before continuing the story.

At the end of each response, provide a brief description (1-2 sentences) of the current scene or action for image generation. Format it as: [IMAGE_PROMPT: description for image generation]"""

# Initialize session state
if 'game_state' not in st.session_state:
    st.session_state.game_state = "not_started"
    st.session_state.messages = []
    st.session_state.roll_result = None
    st.session_state.current_image = None
    st.session_state.image_prompt = None
    st.session_state.health = 10  # Initialize health at 10

# Initialize form values in session state
if 'Name' not in st.session_state:
    st.session_state.Name = "Ildar"
    st.session_state.Class = "Hunter"
    st.session_state.Skills = "Archer, Tracking, Animal Handling"
    st.session_state.Inventory = "1 Bow, Quiver of 40 arrows"

# Function to update health
def update_health(change):
    st.session_state.health = max(0, min(10, st.session_state.health + change))
    return st.session_state.health

# Function to check for game end conditions in AI response
def check_game_end(message):
    if "[VICTORY:" in message:
        st.session_state.game_state = "won"
        return True
    elif "[DEFEAT:" in message:
        st.session_state.game_state = "lost"
        return True
    return False

# Function to display game over screen
def display_game_over():
    if st.session_state.game_state == "won":
        st.balloons()
        st.success("🎉 Congratulations! You have won the game! 🎉")
    elif st.session_state.game_state == "lost":
        st.error("💀 Game Over - Your health reached zero 💀")
    
    if st.button("Start New Game"):
        st.session_state.game_state = "not_started"
        st.session_state.messages = []
        st.session_state.health = 10
        st.rerun()

[Previous functions remain the same: roll_d6(), get_ai_response(), generate_image(), 
generate_and_display_image(), display_image_directory(), read_story_aloud(), 
display_chat_history(), is_roll_request()]

# Streamlit UI
st.title("D&D Adventure Game")

# Display health bar in sidebar
st.sidebar.title("Character Status")
st.sidebar.progress(st.session_state.health / 10)
st.sidebar.write(f"Health: {st.session_state.health}/10")

# Character creation form in sidebar
st.sidebar.title("Create your character")
st.session_state.Name = st.sidebar.text_input("Name", st.session_state.Name)
st.session_state.Class = st.sidebar.text_input("Class", st.session_state.Class)
st.session_state.Skills = st.sidebar.text_input("Skills", st.session_state.Skills)
st.session_state.Inventory = st.sidebar.text_input("Inventory", st.session_state.Inventory)

with st.sidebar:
    display_image_directory()

# Display current image
if st.session_state.current_image:
    st.sidebar.image(st.session_state.current_image, use_column_width=True)

# Handle game states
if st.session_state.game_state in ["won", "lost"]:
    display_game_over()
elif st.session_state.game_state == "not_started":
    if st.button("Start New Adventure"):
        st.session_state.game_state = "playing"
        initial_prompt = generate_prompt()
        st.session_state.messages = [{"role": "system", "content": initial_prompt}]
        st.session_state.messages.append({
            "role": "user",
            "content": "Start a new adventure Dungeon Master. Introduce the characters and setting."
        })
        ai_message = get_ai_response(st.session_state.messages)
        cleaned_message = generate_and_display_image(ai_message)
        st.session_state.messages.append({"role": "assistant", "content": cleaned_message})
        st.rerun()
elif st.session_state.game_state == "playing":
    display_chat_history()

    # Check if the last message is a roll request
    if st.session_state.messages and is_roll_request(st.session_state.messages[-1]["content"]):
        if st.button("Roll Dice"):
            roll_result = roll_d6()
            roll_message = f"You rolled a {roll_result}."
            st.session_state.messages.append({"role": "user", "content": roll_message})
            ai_message = get_ai_response(st.session_state.messages)
            cleaned_message = generate_and_display_image(ai_message)
            
            # Check for game end conditions
            if check_game_end(cleaned_message):
                st.session_state.messages.append({"role": "assistant", "content": cleaned_message})
                st.rerun()
            
            # Update health based on roll result
            if roll_result <= 2:
                update_health(-2)  # Failed roll causes 2 damage
            elif roll_result <= 4:
                update_health(-1)  # Partial success causes 1 damage
            
            # Check if health reached 0
            if st.session_state.health <= 0:
                cleaned_message += "\n[DEFEAT: Your health has reached 0. Game Over.]"
                check_game_end(cleaned_message)
            
            st.session_state.messages.append({"role": "assistant", "content": cleaned_message})
            st.rerun()
    else:
        # User input
        user_input = st.chat_input("What would you like to do?")
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            ai_message = get_ai_response(st.session_state.messages)
            cleaned_message = generate_and_display_image(ai_message)
            
            # Check for game end conditions
            if check_game_end(cleaned_message):
                st.session_state.messages.append({"role": "assistant", "content": cleaned_message})
                st.rerun()
                
            st.session_state.messages.append({"role": "assistant", "content": cleaned_message})
            st.rerun()
