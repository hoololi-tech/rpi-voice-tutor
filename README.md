# AI English Tutor - Raspberry Pi Voice Assistant

A voice-based English learning assistant that runs on Raspberry Pi with Sense HAT. Practice conversations in different contexts with an AI tutor.

## Features

- Voice interaction using push-to-talk (Sense HAT joystick)
- Multiple teacher profiles (adult/child learners)
- Context-based conversations (restaurant, shopping, health, general)
- Visual feedback via Sense HAT LED matrix
- Powered by OpenAI Whisper (speech-to-text), GPT-4o-mini (conversation), and OpenAI TTS (text-to-speech)

## Hardware Requirements

- Raspberry Pi (tested on Pi 5)
- Sense HAT
- USB microphone/headset
- Speaker or headphones

## Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Install system dependencies:
```bash
sudo apt install mpg123
```
**Note:** If using a virtual environment, create it with `--system-site-packages` to access Sense HAT libraries:
```bash
python3 -m venv venv --system-site-packages
```
4. Create a `.env` file with your API keys:
```bash
OPENAI_API_KEY=your_key_here OPENROUTER_API_KEY=your_key_here
```
5. Adjust speaker volume using `alsamixer` in terminal

## Usage

Run the assistant:
```bash
python3 main.py
```

Follow the prompts to select your audio devices, teacher profile, and conversation context. Press and hold the Sense HAT joystick to speak.

## License

Open source - feel free to modify and share!