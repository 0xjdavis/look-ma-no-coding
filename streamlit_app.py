import streamlit as st
import random
from openai import OpenAI
import json

# Set API Keys (using st.secrets for Streamlit)
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

# Define the OpenAI model
MODEL = 'gpt-4'

# Function to generate the PROMPT based on current form values
def generate_prompt():
    return f"""You are a Dungeon Master in a D&D-style adventure game. The player's character is {st.session_state.Class} named {st.session_state.Name} with {st.session_state.Skills} skills and {st.session_state.Inventory}. Guide the player through the story, prompting them to take actions.

When presenting action choices to the player, format them as a numbered list like this:
Player action:
1. [First action option]
2. [Second action option]
3. [Third action option]

Provide 2-4 options for each action prompt. Ask the player to roll a d6 for skill checks, and at the end of each response, provide a brief description for image generation as: [IMAGE: description]."""

# Initialize session state
if 'game_state' not in st.session_state:
    st.session_state.game_state = "not_started"
    st.session_state.messages = []
    st.session_state.roll_result = None
    st.session_state.current_image = None

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
        generate_and_display_image(ai_message)

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
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return "I apologize, but I'm having trouble connecting to the AI service at the moment. Please try again later."

# Function to generate image using DALL-E
def generate_image(prompt):
    try:
        full_prompt = f"A high-quality fantasy image: {prompt}"
        response = client.images.generate(
            model="dall-e-3",
            prompt=full_prompt,
            size="1024x768",
            n=1,
        )
        image_url = response.data[0].url
        return image_url
    except Exception as e:
        st.error(f"An error occurred while generating the image: {str(e)}")
        return None

# Function to generate and display image
def generate_and_display_image(message):
    if "[IMAGE:" in message:
        try:
            image_prompt = message.split("[IMAGE:")[-1].split("]")[0].strip()
            image_url = generate_image(image_prompt)
            if image_url:
                st.session_state.current_image = image_url
                st.image(image_url, use_column_width=True)
            else:
                st.error("Failed to generate an image. Please try again later.")
        except Exception as e:
            st.error(f"Image prompt extraction failed: {str(e)}")
    else:
        st.error("No valid image prompt found.")

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

# Display current image
if st.session_state.current_image:
    st.image(st.session_state.current_image, st.session_state.current_image, use_column_width=True)

# Start game button
if st.session_state.game_state == "not_started":
    if st.button("Start New Adventure"):
        st.session_state.game_state = "playing"
        initial_prompt = generate_prompt()
        st.session_state.messages = [{"role": "system", "content": initial_prompt}]
        st.session_state.messages.append({
            "role": "user",
            "content": "Start a new adventure game. Introduce the setting."
        })
        ai_message = get_ai_response(st.session_state.messages)
        generate_and_display_image(ai_message)
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
            generate_and_display_image(ai_message)
            st.session_state.messages.append({"role": "assistant", "content": ai_message})
            st.rerun()
    else:
        # User input
        user_input = st.chat_input("What would you like to do?")
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            ai_message = get_ai_response(st.session_state.messages)
            generate_and_display_image(ai_message)
            st.session_state.messages.append({"role": "assistant", "content": ai_message})
            st.rerun()
