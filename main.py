import os
import pyaudio
import wave
import tempfile
import time
from dotenv import load_dotenv
from sense_hat import SenseHat
from openai import OpenAI

# Load environment variables
load_dotenv()

# Note: volume of speaker can be set using alsamixer in the terminal

# ============= MODEL SELECTION =============
# OpenAI TTS voices: alloy, echo, fable, onyx, nova, shimmer
TTS_VOICE = "nova"
TTS_MODEL = "tts-1"  # or "tts-1-hd" for higher quality
STT_MODEL = "whisper-1"

# LLM options
LLM_PROVIDER = "openai"  # "openai" or "openrouter"
OPENAI_LLM_MODEL = "gpt-4o-mini"  # cheap and fast
OPENROUTER_LLM_MODEL = "anthropic/claude-haiku-4.5"

# API setup
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
openrouter_key = os.getenv('OPENROUTER_API_KEY')

# Teacher profiles
TEACHER_PROFILES = {
    "adult": "You are a professional English tutor for adults. Use natural, conversational language and correct mistakes gently.",
    "child": "You are a super fun English teacher for kids! Use easy words, lots of encouragement like 'Great job!' and 'You're doing awesome!', and be very playful and excited."
}

# Conversation contexts
CONTEXTS = {
    "restaurant": "We're practicing English at a restaurant. Vocabulary: menu, order, waiter, bill, reservation, appetizer, main course, dessert. Common phrases: 'I'd like to order...', 'Could I have the bill?', 'Do you have a table for two?'",
    "shopping": "We're practicing English while shopping. Vocabulary: price, discount, size, fitting room, cashier, receipt. Common phrases: 'How much is this?', 'Can I try this on?', 'Do you have this in another size?'",
    "health": "We're practicing English in relation with health. We are at the doctor and discuss symptoms, habits, food, sleep.",
    "general": "General English conversation practice."
}

#greetings
CONTEXT_GREETINGS = {
    "restaurant": "Hi! Ready to practice ordering at a restaurant?",
    "shopping": "Hi! Let's practice some shopping conversations!",
    "health": "Hi! Let's practice talking about health and visiting the doctor!",
    "general": "Hi! Wanna practice English?"
}

# Sense HAT setup
sense = SenseHat()
sense.low_light = True

# Audio settings
RATE = 48000
CHUNK = 256
FORMAT = pyaudio.paInt16
CHANNELS = 1

# Conversation history
conversation = []

# LED colors
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
OFF = (0, 0, 0)

def set_led_color(color):
    """Set all LEDs to one color"""
    sense.clear(*color)

def pulse_color(color, duration=0.1):
    """Pulse/breathe effect for waiting state"""
    for brightness in range(0, 255, 15):
        scaled = tuple(int(c * brightness / 255) for c in color)
        sense.clear(*scaled)
        time.sleep(duration / 17)
    for brightness in range(255, 0, -15):
        scaled = tuple(int(c * brightness / 255) for c in color)
        sense.clear(*scaled)
        time.sleep(duration / 17)

def list_audio_devices():
    """List all available audio input and output devices"""
    pa = pyaudio.PyAudio()
    print("\nAvailable audio devices:")
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        print(f"{i}: {info['name']} (in:{info['maxInputChannels']}, out:{info['maxOutputChannels']})")
    pa.terminate()


def select_audio_device():
    """Let user select audio input device"""
    list_audio_devices()
    while True:
        try:
            device_index = int(input("\nSelect input device number: "))
            return device_index
        except ValueError:
            print("Please enter a valid number")

def select_profile_and_context():
    """Let user select teacher profile and conversation context"""
    print("\n=== Teacher Profile ===")
    profiles = list(TEACHER_PROFILES.keys())
    for i, profile in enumerate(profiles, 1):
        print(f"{i}. {profile}")
    
    profile_choice = int(input("Select profile: ")) - 1
    selected_profile = profiles[profile_choice]
    
    print("\n=== Conversation Context ===")
    contexts = list(CONTEXTS.keys())
    for i, context in enumerate(contexts, 1):
        print(f"{i}. {context}")
    
    context_choice = int(input("Select context: ")) - 1
    selected_context = contexts[context_choice]
    
    return selected_profile, selected_context

def record_audio_with_button(input_device):
    """Record audio while button is pressed"""
    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
        input_device_index=input_device
    )
    
    print("Press and hold joystick to speak...")
    frames = []
    recording = False
    
    # Wait for button press with pulsing
    while True:
        pulse_color(PURPLE)
        events = sense.stick.get_events()
        for event in events:
            if event.action == "pressed" and event.direction == "middle":
                recording = True
                set_led_color(RED)
                print("Recording...")
                break
        if recording:
            break
    
    # Record while button held
    while recording:
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
        
        # Check if button released
        events = sense.stick.get_events()
        for event in events:
            if event.action == "released" and event.direction == "middle":
                recording = False
                print("Recording finished")
                break
    
    stream.stop_stream()
    stream.close()
    
    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    wf = wave.open(temp_file.name, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(pa.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    return temp_file.name

def transcribe_audio(audio_file):
    """Convert speech to text using OpenAI Whisper"""
    set_led_color(BLUE)
    print("Transcribing...")
    
    with open(audio_file, 'rb') as f:
        transcript = openai_client.audio.transcriptions.create(
            model=STT_MODEL,
            file=f,
            language="en"
        )
    return transcript.text

def get_llm_response(user_text, system_prompt):
    """Get response from LLM"""
    set_led_color(BLUE)
    print("Getting AI response...")
    
    conversation.append({"role": "user", "content": user_text})
    
    if LLM_PROVIDER == "openai":
        response = openai_client.chat.completions.create(
            model=OPENAI_LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                *conversation
            ]
        )
        assistant_message = response.choices[0].message.content
    elif LLM_PROVIDER == "openrouter":
        import requests
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {openrouter_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": OPENROUTER_LLM_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    *conversation
                ]
            }
        )
        assistant_message = response.json()['choices'][0]['message']['content']
    
    conversation.append({"role": "assistant", "content": assistant_message})
    return assistant_message

def text_to_speech(text):
    """Convert text to speech using OpenAI TTS"""
    set_led_color(BLUE)
    print("Generating speech...")
    
    response = openai_client.audio.speech.create(
        model=TTS_MODEL,
        voice=TTS_VOICE,
        input=text
    )
    
    audio_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    audio_file.write(response.content)
    
    return audio_file.name

def play_audio(audio_file):
    """Play audio through speaker"""
    set_led_color(GREEN)
    # Use device name directly with mpg123
    os.system(f'mpg123 -q -f 32768 {audio_file}')

def main():
    print("Personal Assistant starting...")
    print(f"Using OpenAI:")
    print(f"  STT: {STT_MODEL}")
    print(f"  LLM: {OPENAI_LLM_MODEL if LLM_PROVIDER == 'openai' else OPENROUTER_LLM_MODEL}")
    print(f"  TTS: {TTS_MODEL} (voice: {TTS_VOICE})")
    
    try:
        input_device = select_audio_device()
        
        # Select profile and context
        selected_profile, selected_context = select_profile_and_context()

        # Build system prompt
        system_prompt = f"{TEACHER_PROFILES[selected_profile]} {CONTEXTS[selected_context]}"

        # Greet user immediately
        greeting = CONTEXT_GREETINGS[selected_context]
        print(f"Assistant: {greeting}")
        greeting_audio = text_to_speech(greeting)
        play_audio(greeting_audio)
        os.unlink(greeting_audio)
        
        # Conversation loop
        while True:
            # Record with button
            audio_file = record_audio_with_button(input_device)
            
            # Transcribe
            user_text = transcribe_audio(audio_file)
            print(f"User: {user_text}")
            os.unlink(audio_file)
            
            if not user_text.strip():
                print("No speech detected, ending conversation")
                conversation.clear()
                break
            
            # Get LLM response
            response_text = get_llm_response(user_text, system_prompt)
            print(f"Assistant: {response_text}")
            
            # Speak response
            response_audio = text_to_speech(response_text)
            play_audio(response_audio)
            os.unlink(response_audio)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        set_led_color(OFF)

if __name__ == "__main__":
    main()
