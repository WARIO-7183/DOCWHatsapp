# WhatsApp Medical Assistant Bot

A customizable WhatsApp chatbot that serves as a conversational medical assistant, powered by the OpenAI API and Twilio's WhatsApp API. The bot can communicate in multiple languages and presents options in an interactive format.

## Features

- **Multi-language Support**: Available in English, Hindi, Tamil, Telugu, Kannada, and Malayalam
- **Interactive Option Selection**: Presents choices as numbered lists for easy selection
- **Conversational Medical Assistance**: Asks about symptoms and offers basic medical guidance
- **Personalized Experience**: Remembers user details throughout the conversation
- **User Data Persistence**: Stores user information and medical history in Supabase database
- **Returning User Recognition**: Automatically identifies returning users by phone number
- **Simple Reset Command**: Type 'reset' to start over at any time

## Requirements

- Python 3.7+
- Supabase account
- OpenAI API key (for the AI language model)
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

### 4. Set up Supabase

1. Create a Supabase account at [supabase.com](https://supabase.com)
2. Create a new project
3. Get your project URL and API key from the project settings

### 5. Set up environment variables

Create a `.env` file in the project root directory with the following variables:

```
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# API Keys
OPENAI_API_KEY=your_openai_api_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
```

## Usage

### 1. Start the application

```bash
python app.py
```

The application will automatically:
- Connect to the Supabase database
- Start the Flask server on port 5000 (or the port specified in your environment variables)

### 2. Expose your local server (for development)

Use ngrok to expose your local server to the internet:

```bash
ngrok http 5000
```

### 3. Configure Twilio webhook

Set up your Twilio WhatsApp sandbox to point to your ngrok URL:

```
https://your-ngrok-url/webhook
```

### 4. Interact with the bot

Send a message to your Twilio WhatsApp number to start interacting with the bot.

## User Flow

### New Users
1. Select preferred language
2. Provide phone number
3. Enter name, age, and gender
4. Share health concerns
5. Receive medical assistance

### Returning Users
1. Select preferred language
2. Provide phone number
3. Bot recognizes the user and loads previous data
4. Continue conversation with medical history context
5. Receive updated medical assistance

## Database Structure

The application uses a Supabase database with the following structure:

- **users table**:
  - `phone_number` (VARCHAR, PRIMARY KEY): User's phone number
  - `name` (VARCHAR): User's name
  - `age` (INT): User's age
  - `gender` (VARCHAR): User's gender
  - `medical_history` (TEXT): JSON string of conversation history
  - `language` (VARCHAR): User's preferred language
  - `created_at` (TIMESTAMP): When the user was first added
  - `updated_at` (TIMESTAMP): When the user's data was last updated

## Special Commands

- Type `reset` at any time to start over
- Type `bye` to end the conversation

## License

This project is licensed under the MIT License - see the LICENSE file for details.
