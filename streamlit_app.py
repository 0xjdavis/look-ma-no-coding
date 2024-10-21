import streamlit as st
import random
from openai import OpenAI
import time
import pyttsx3  # New import for offline TTS

# Set API Keys (using st.secrets for Streamlit)
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except KeyError:
    st.error("Missing OpenAI API key in Streamlit secrets.")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

# Define the OpenAI model
MODEL = 'gpt-4'

# Initialize the TTS engine for pyttsx3
engine = pyttsx3.init()

# Function to generate the PROMPT based on current form values
def generate_prompt():
    return f"""You are a Dungeon Master in a D&D-style adventure game. The player's character is defined as {st.session_state.Class} named {st.session_state.Name} with {st.session_state.Skills} skills and {st.session_state.Inventory}. Guide the player through the story, prompting them to take actions.

When presenting action choices to the player, format them as a numbered list like this:
Player action:
1. [First action option]
2. [Second action option]
3. [Third action option]

Provide 2-4 options for each action prompt. The player will respond with their chosen action.

When a situation requires a skill check or an action with uncertain outcome, explicitly ask the player to roll a d6 (six-sided die). Format your request for a dice roll as follows: '[ROLL THE DICE: reason for rolling]' For example: '[ROLL THE DICE: to see if you successfully track the creature]'

After the player rolls, interpret the result as follows:
1-2 = Failure
3-4 = Partial success
5-6 = Complete success

Wait for the player's roll or action choice before continuing the story.

At the end of each response, provide a brief description (1-2 sentences) of the current scene or action for image generation. Format it as: [IMAGE: description for image generation]"""

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

# Sidebar form
st.sidebar.title("Create your character")
st.session_state.Name = st.sidebar.text_input("Name", st.session_state.Name)
st.session_state.Class = st.sidebar.text_input("Class", st.session_state.Class)
st.session_state.Skills = st.sidebar.text_input("Skills", st.session_state.Skills)
st.session_state.Inventory = st.sidebar.text_input("Inventory", st.session_state.Inventory)

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
        st.error(f"An error occurred connecting to OpenAI: {str(e)}")
        return "I apologize, but I'm having trouble connecting to the AI service at the moment. Maybe take a break or check your connection."

# Function to generate image using DALL-E
def generate_image(prompt):
    try:
        full_prompt = f"Create a highly detailed fantasy scene: {prompt}. Include rich, vivid colors, magical elements, and a sense of adventure."
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=full_prompt,
            size="1024x1024",
            n=1
        )
        return response.data[0].url
    except Exception as e:
        st.error(f"An error occurred while generating the image: {str(e)}")
        time.sleep(5) 
        return None

# Function to extract and display image
def generate_and_display_image(message):
    if "[IMAGE:" in message:
        try:
            # Extract the image prompt from the message
            image_prompt = message.split("[IMAGE:")[-1].split("]")[0].strip()
            
            if image_prompt:
                image_url = generate_image(image_prompt)
                
                # Check if the image was successfully generated
                if image_url:
                    st.session_state.current_image = image_url
                    st.image(image_url, caption=image_url, use_column_width=True)
                else:
                    st.error("Failed to generate an image. Please try again.")
            else:
                st.error("No valid image prompt found.")
        except Exception as e:
            st.error(f"Error generating image: {str(e)}")

# Function to read the story out loud using pyttsx3
def read_story_aloud(text):
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        st.error(f"An error occurred while generating audio: {str(e)}")

# Display chat history
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
    st.image(st.session_state.current_image, use_column_width=True)

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
        st.session_state.messages.append({"role": "assistant", "content": ai_message})
        generate_and_display_image(ai_message)
        read_story_aloud(ai_message)
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
            generate_and_display_image(ai_message)
            read_story_aloud(ai_message)
            st.rerun()
    else:
        # User input
        user_input = st.chat_input("What would you like to do?")
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            ai_message = get_ai_response(st.session_state.messages)
            st.session_state.messages.append({"role": "assistant", "content": ai_message})
            generate_and_display_image(ai_message)
            read_story_aloud(ai_message)
            st.rerun()
