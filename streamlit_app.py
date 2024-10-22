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

def generate_prompt():
    return f"""You are a Dungeon Master in a D&D-style adventure game. The player's character is defined as a {st.session_state.Race} named {st.session_state.Name} who is a {st.session_state.Class} with a {st.session_state.Background} banckground and {st.session_state.Skills} skills with {st.session_state.Inventory} as inventory. The player has {st.session_state.health}/10 health remaining. Guide the player through the story, prompting them to take actions.

When the player gains health (through potions, healing, rest, etc.), format it as: [HEAL:amount] where 'amount' is the number of health points gained.
For example: "You drink the healing potion and feel its magic course through you. [HEAL:3]"

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

At the end of each response, provide a brief description (1-2 sentences) of the current scene or action for image generation. Format it as: [IMAGE_PROMPT: summarize the scene described.]"""

# Initialize session state
if 'game_state' not in st.session_state:
    st.session_state.game_state = "not_started"
    st.session_state.messages = []
    st.session_state.roll_result = None
    st.session_state.current_image = None
    st.session_state.image_prompt = None
    st.session_state.health = 10  # Initialize health at 10


# CHARACTER
# Initialize form values in session state
if 'Name' not in st.session_state:
    st.session_state.Name = "Ildar"
    st.session_state.Race = st.selectbox(
        "Race",
        ("Dwarf", "Elf", "Halfling", "Human", "Dragonborn", "Gnome", "Half-Elf", "Half-Orc", "Tiefling"),
    )
    
    st.session_state.Class = st.selectbox(
        "Class",
        ("Barbarian", "Bard", "Cleric", "Druid", "Fighter", "Monk", "Paladin", "Ranger", "Rogue", "Sorcerer", "Warlock", "Wizard"),
    )
    
    st.session_state.Background = st.selectbox(
        "Background",
        ("Acolyte", "Charlatan", "Criminal", "Entertainer", "Folk Hero", "Guild Artisan", "Hermit", "Noble", "Outlander", "Sage", "Sailor", "Soldier", "Urchin"),
    )
    st.session_state.Skills = "Archer, Tracking, Animal Handling"
    st.session_state.Inventory = "1 Bow, Quiver of arrows"


# Function for monitoring health change
def process_health_changes(message):
    # Check for healing
    if "[HEAL:" in message:
        try:
            heal_amount = int(message.split("[HEAL:")[1].split("]")[0])
            update_health(heal_amount)
            # Remove the heal tag from the message
            message = message.replace(f"[HEAL:{heal_amount}]", "")
        except ValueError:
            st.error("Invalid healing amount specified")
    
    # Check for damage (if you have specific damage tags)
    if "[DAMAGE:" in message:
        try:
            damage_amount = int(message.split("[DAMAGE:")[1].split("]")[0])
            update_health(-damage_amount)
            # Remove the damage tag from the message
            message = message.replace(f"[DAMAGE:{damage_amount}]", "")
        except ValueError:
            st.error("Invalid damage amount specified")
    
    return message

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
        return "I apologize, but I'm having trouble connecting to the AI service in the real world. Maybe go outside and get some fresh air."

# Ensure the directory exists
if not os.path.exists('data/images'):
    os.makedirs('data/images')

# Function to generate and save the image locally
def generate_image(prompt):
    try:
        full_prompt = f"Create a highly detailed fantasy scene: {prompt}. Include rich, vivid colors, magical elements, and a sense of adventure. Use the fantasy artwork stylings of artist Frank Frazetta as an influence of the images. Create consistent imagery using the same character for the entire game. Don't change styles."
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=full_prompt,
            size="1024x1024",
            n=1
        )
        image_url = response.data[0].url
        
        # Download the image
        image_response = requests.get(image_url)
        if image_response.status_code == 200:
            # Save the image to /data/images/ directory
            image_path = f"data/images/{prompt.replace(' ', '_')[:50]}.jpg"
            with open(image_path, 'wb') as f:
                f.write(image_response.content)
            return image_path
        else:
            st.error("Failed to download the image.")
            return None
    except Exception as e:
        st.error(f"An error occurred while generating the image: {str(e)}")
        return None

# Function to extract image prompt and generate image
def generate_and_display_image(message):
    # Process health changes first
    message = process_health_changes(message)
    
    # Then handle image generation as before
    if "[IMAGE_PROMPT:" in message:
        try:
            image_prompt = message.split("[IMAGE_PROMPT:")[-1].split("]")[0].strip()
            
            if image_prompt:
                image_url = generate_image(image_prompt)
                
                if image_url:
                    st.session_state.current_image = image_url
                    st.sidebar.image(image_url, caption="Current Scene", use_column_width=True)
                else:
                    st.error("Failed to generate an image. Please try again.")
            else:
                st.error("No valid image prompt found.")
        except Exception as e:
            st.error(f"Error generating image: {str(e)}")
    
    # Remove the image prompt from the message
    return message.split("[IMAGE_PROMPT:")[0].strip()

# Function to list and display images from the /data/images/ directory
def display_image_directory(directory="data/images"):
    if not os.path.exists(directory):
        st.sidebar.write("The images directory does not exist.")
        return

    image_files = os.listdir(directory)
    
    if len(image_files) == 0:
        st.sidebar.write("No images found in the directory.")
        return

    image_path = st.query_params.get("data/images/")
    if image_path:
        image = Image.open(image_path)
        st.image(image)

# Function to read the story out loud using gTTS (Google Text-to-Speech)
def read_story_aloud(text):
    try:
        tts = gTTS(text, lang='en', tld='us')
        mp3_fp = BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        st.audio(mp3_fp, format="audio/mp3")
    except Exception as e:
        st.error(f"An error occurred while generating audio: {str(e)}")

# Display chat history
def display_chat_history():
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.write(message["content"])
                # Play the audio after each message by the assistant
                if message["role"] == "assistant":
                    read_story_aloud(message["content"])

# Function to check if AI is requesting a dice roll
def is_roll_request(message):
    return '[ROLL THE DICE:' in message

# Streamlit UI
st.title("D&D Adventure Game")

# Character creation form in sidebar
st.sidebar.subheader("Create your character")
st.session_state.Name = st.sidebar.text_input("Name", st.session_state.Name)
st.session_state.Race = st.sidebar.text_input("Race", st.session_state.Race)
st.session_state.Class = st.sidebar.text_input("Class", st.session_state.Class)
st.session_state.Background = st.sidebar.text_input("Background", st.session_state.Background)
st.session_state.Skills = st.sidebar.text_input("Skills", st.session_state.Skills)
st.session_state.Inventory = st.sidebar.text_input("Inventory", st.session_state.Inventory)

# Display health bar in sidebar
st.sidebar.subheader("Character Health")
st.sidebar.progress(st.session_state.health / 10)
st.sidebar.write(f"Health: {st.session_state.health}/10")

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
            "content": "Start a new adventure Dungeon Master. Describe the setting."
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
            
            # Append the roll message without calling st.rerun
            st.session_state.messages.append({"role": "user", "content": roll_message})
            
            ai_message = get_ai_response(st.session_state.messages)
            cleaned_message = generate_and_display_image(ai_message)
            
            # Process game end conditions before updating health
            if check_game_end(cleaned_message):
                st.session_state.messages.append({"role": "assistant", "content": cleaned_message})
                # No need to call st.rerun if we process messages in the same render pass
            
            # Update health based on roll result
            if roll_result <= 2:
                cleaned_message += f" [DAMAGE:2]"  # Add damage tag for processing
            elif roll_result <= 4:
                cleaned_message += f" [DAMAGE:1]"  # Add damage tag for processing
            
            # Process health and append AI response
            cleaned_message = process_health_changes(cleaned_message)
            st.session_state.messages.append({"role": "assistant", "content": cleaned_message})
            
            # Check if health reached 0 and end the game
            if st.session_state.health <= 0:
                cleaned_message += "\n[DEFEAT: Your health has reached 0. Game Over.]"
                check_game_end(cleaned_message)
                st.session_state.messages.append({"role": "assistant", "content": cleaned_message})
    else:
        # Allow the user to input and process their message
        user_input = st.chat_input("What would you like to do?")
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            ai_message = get_ai_response(st.session_state.messages)
            cleaned_message = generate_and_display_image(ai_message)
            
            # Process game end conditions
            if check_game_end(cleaned_message):
                st.session_state.messages.append({"role": "assistant", "content": cleaned_message})
            
            st.session_state.messages.append({"role": "assistant", "content": cleaned_message})
