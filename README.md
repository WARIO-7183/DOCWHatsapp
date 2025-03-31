
# WhatsApp Medical Assistant Bot

A customizable WhatsApp chatbot that serves as a conversational medical assistant, powered by the Groq AI API and Twilio's WhatsApp API. The bot can communicate in multiple languages and presents options in an interactive format.

## Features

- **Multi-language Support**: Available in English, Spanish, Hindi, French, and German
- **Interactive Option Selection**: Presents choices as numbered lists for easy selection
- **Conversational Medical Assistance**: Asks about symptoms and offers basic medical guidance
- **Personalized Experience**: Remembers user details throughout the conversation
- **Simple Reset Command**: Type 'reset' to start over at any time

## Requirements

- Python 3.7+
- Groq API key (for the AI language model)
- Twilio account with WhatsApp sandbox or Business API
- Ngrok (for local development)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/whatsapp-medical-assistant.git
cd whatsapp-medical-assistant
```

### 2. Create a virtual environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the project root directory: 
=======
# AIDocWhatsapp
>>>>>>> origin/main
