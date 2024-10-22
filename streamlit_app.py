import streamlit as st
import random, os, requests
from openai import OpenAI
from gtts import gTTS
from io import BytesIO
from PIL import Image

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)
MODEL = 'gpt-4'

def gen_prompt():
    return f"""You are a D&D Dungeon Master. Create a story and scene for the player. Player: {st.session_state.Class} {st.session_state.Name}, Skills: {st.session_state.Skills}, Inventory: {st.session_state.Inventory}. Guide the player, prompt for actions.

Present choices as:
Player action:
1. [Option 1]
2. [Option 2]
3. [Option 3]

Provide 2-4 options. Player responds with chosen action.

For skill checks: '[ROLL THE DICE: reason]'
Interpret roll:
1-2 = Fail, 3-4 = Partial success, 5-6 = Success

Wait for player's roll/choice before continuing.

End with: [IMAGE: brief scene description]"""

if 'game_state' not in st.session_state:
    st.session_state.game_state = "not_started"
    st.session_state.messages = []
    st.session_state.current_image = None

for attr in ['Name', 'Class', 'Skills', 'Inventory']:
    if attr not in st.session_state:
        st.session_state[attr] = ""

st.sidebar.title("Create character")
for attr in ['Name', 'Class', 'Skills', 'Inventory']:
    st.session_state[attr] = st.sidebar.text_input(attr, st.session_state[attr])

def roll_d6(): return random.randint(1, 6)

def get_ai_response(msgs):
    try:
        return client.chat.completions.create(model=MODEL, messages=msgs).choices[0].message.content
    except Exception as e:
        return f"Error connecting to AI: {str(e)}"

if not os.path.exists('data/images'): os.makedirs('data/images')

def gen_image(prompt):
    try:
        full_prompt = f"Detailed fantasy scene: {prompt}. Vivid colors, magical elements, adventure. Frank Frazetta style. Consistent imagery."
        img_url = client.images.generate(model="dall-e-3", prompt=full_prompt, size="1024x1024", n=1).data[0].url
        img_resp = requests.get(img_url)
        if img_resp.status_code == 200:
            img_path = f"data/images/{prompt.replace(' ', '_')[:50]}.jpg"
            with open(img_path, 'wb') as f: f.write(img_resp.content)
            return img_path
    except Exception as e:
        st.error(f"Image generation error: {str(e)}")
    return None

def gen_and_show_image(msg):
    if "[IMAGE:" in msg:
        img_prompt = msg.split("[IMAGE:")[-1].split("]")[0].strip()
        if img_prompt:
            img_url = gen_image(img_prompt)
            if img_url:
                st.session_state.current_image = img_url
                st.sidebar.image(img_url, use_column_width=True)

def show_image_dir(dir="data/images"):
    if os.path.exists(dir):
        for img_file in os.listdir(dir):
            img_path = os.path.join(dir, img_file)
            st.sidebar.image(img_path, use_column_width=True)

def read_aloud(text):
    try:
        tts = gTTS(text, lang='en', tld='us')
        mp3_fp = BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        st.audio(mp3_fp, format="audio/mp3")
    except Exception as e:
        st.error(f"Audio generation error: {str(e)}")

def show_chat():
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if msg["role"] == "assistant": read_aloud(msg["content"])

def is_roll_req(msg): return '[ROLL THE DICE:' in msg

st.title("D&D Adventure Game")
with st.sidebar: show_image_dir()
if st.session_state.current_image: st.sidebar.image(st.session_state.current_image, use_column_width=True)

if st.session_state.game_state == "not_started":
    if st.button("Start New Adventure"):
        st.session_state.game_state = "playing"
        init_prompt = gen_prompt()
        st.session_state.messages = [{"role": "system", "content": init_prompt}, {"role": "user", "content": "Start a new adventure. Introduce the setting."}]
        ai_msg = get_ai_response(st.session_state.messages)
        gen_and_show_image(ai_msg)
        st.session_state.messages.append({"role": "assistant", "content": ai_msg})
        st.rerun()

if st.session_state.game_state == "playing":
    show_chat()
    if st.session_state.messages and is_roll_req(st.session_state.messages[-1]["content"]):
        if st.button("Roll Dice"):
            roll = roll_d6()
            st.session_state.messages.append({"role": "user", "content": f"You rolled a {roll}."})
            ai_msg = get_ai_response(st.session_state.messages)
            gen_and_show_image(ai_msg)
            st.session_state.messages.append({"role": "assistant", "content": ai_msg})
            st.rerun()
    else:
        user_input = st.chat_input("What would you like to do?")
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            ai_msg = get_ai_response(st.session_state.messages)
            gen_and_show_image(ai_msg)
            st.session_state.messages.append({"role": "assistant", "content": ai_msg})
            st.rerun()
