from flask import Flask, request, Response
import os
from dotenv import load_dotenv
import requests
import traceback
import logging
from twilio.twiml.messaging_response import MessagingResponse
    
# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Get API keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

logger.info(f"GROQ_API_KEY loaded: {'Yes' if GROQ_API_KEY else 'No'}")
logger.info(f"TWILIO credentials loaded: {'Yes' if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN else 'No'}")

# Print all environment variables for debugging (be careful with sensitive info)
logger.debug("Environment variables:")
for key, value in os.environ.items():
    if 'KEY' in key or 'SECRET' in key or 'SID' in key or 'TOKEN' in key:
        logger.debug(f"{key}: {'[REDACTED]'}")
    else:
        logger.debug(f"{key}: {value}")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Modify system prompt to include formatting for options
SYSTEM_PROMPT = """
You are a friendly, conversational medical assistant. Follow these guidelines:

1. When presenting options to the user, always format them as a numbered list:
   Example:
   Please describe your headache:
   1️⃣ Sharp pain
   2️⃣ Dull ache
   3️⃣ Throbbing sensation
   4️⃣ Other (please describe)
   
   Reply with the number of your choice or type your own response.

2. Once you know their name, always address the user by their name.
3. After getting their name, ask for their age and gender specifically.
4. Only after collecting name, age, and gender, ask about their health concerns or symptoms.
5. When asking about health issues, provide examples as numbered options.
6. Keep track of their name, age, gender and health history throughout the conversation.
7. Keep responses short and conversational - use 1-3 sentences where possible.
8. Speak naturally like a real doctor or nurse would in conversation.
9. Ask focused follow-up questions about symptoms - one question at a time.
10. Present options when appropriate (like pain types, severity, etc.) using the numbered format.
11. Use a warm, empathetic tone while maintaining professionalism.
12. Clearly state you're an AI assistant, not a replacement for professional medical care.
13. When the conversation appears to be concluding OR when discussing serious symptoms, offer to connect the user to a real doctor.
14. Prioritize clarity and brevity over comprehensiveness.

Remember: Be conversational and human-like. Follow the exact sequence: 1) ask name, 2) ask age and gender, 3) ask about medical conditions with examples. Address the user by name throughout the conversation after learning it.
"""

# Available languages and their system prompts
LANGUAGES = {
    "1": {"name": "English", "code": "en"},
    "2": {"name": "Spanish", "code": "es"}, 
    "3": {"name": "Hindi", "code": "hi"},
    "4": {"name": "French", "code": "fr"},
    "5": {"name": "German", "code": "de"}
}

# Translated language selection message
LANGUAGE_SELECTION_MESSAGE = {
    "en": "Welcome to the Medical Assistant! Please select your preferred language:\n1️⃣ English\n2️⃣ Spanish\n3️⃣ Hindi\n4️⃣ French\n5️⃣ German\n\nReply with the number of your choice.",
    "es": "¡Bienvenido al Asistente Médico! Seleccione su idioma preferido:\n1️⃣ Inglés\n2️⃣ Español\n3️⃣ Hindi\n4️⃣ Francés\n5️⃣ Alemán\n\nResponda con el número de su elección.",
    "hi": "मेडिकल असिस्टेंट में आपका स्वागत है! कृपया अपनी पसंदीदा भाषा चुनें:\n1️⃣ अंग्रेज़ी\n2️⃣ स्पेनिश\n3️⃣ हिंदी\n4️⃣ फ्रेंच\n5️⃣ जर्मन\n\nअपनी पसंद का नंबर लिखकर जवाब दें।",
    "fr": "Bienvenue dans l'Assistant Médical ! Veuillez sélectionner votre langue préférée :\n1️⃣ Anglais\n2️⃣ Espagnol\n3️⃣ Hindi\n4️⃣ Français\n5️⃣ Allemand\n\nRépondez avec le numéro de votre choix.",
    "de": "Willkommen beim Medizinischen Assistenten! Bitte wählen Sie Ihre bevorzugte Sprache:\n1️⃣ Englisch\n2️⃣ Spanisch\n3️⃣ Hindi\n4️⃣ Französisch\n5️⃣ Deutsch\n\nAntworten Sie mit der Nummer Ihrer Wahl."
}

# Store chat history per user
user_sessions = {}

def get_chat_history(user_id):
    """Get or initialize chat history for a user"""
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "language_selected": False,
            "language": "en",
            "history": []
        }
        return user_sessions[user_id]
    return user_sessions[user_id]

def reset_chat_history(user_id):
    """Reset chat history for a user"""
    user_sessions[user_id] = {
        "language_selected": False,
        "language": "en",
        "history": []
    }
    return user_sessions[user_id]

def get_system_prompt_for_language(language_code):
    """Get system prompt translated for the specified language"""
    # This is a simplified version - in a real app, you would have complete translations
    # of the system prompt for each language
    if language_code == "en":
        return SYSTEM_PROMPT
    elif language_code == "es":
        # Spanish system prompt
        return SYSTEM_PROMPT.replace("You are a friendly", "Eres un amigable").replace("medical assistant", "asistente médico")
    elif language_code == "hi":
        # Hindi system prompt
        return SYSTEM_PROMPT.replace("You are a friendly", "आप एक मित्रवत").replace("medical assistant", "चिकित्सा सहायक हैं")
    elif language_code == "fr":
        # French system prompt
        return SYSTEM_PROMPT.replace("You are a friendly", "Vous êtes un").replace("medical assistant", "assistant médical amical")
    elif language_code == "de":
        # German system prompt
        return SYSTEM_PROMPT.replace("You are a friendly", "Sie sind ein freundlicher").replace("medical assistant", "medizinischer Assistent")
    else:
        return SYSTEM_PROMPT

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming WhatsApp messages"""
    # Get the message content
    incoming_msg = request.values.get('Body', '').strip()
    user_id = request.values.get('From', '')
    
    # Initialize Twilio response
    resp = MessagingResponse()
    
    # Reset command
    if incoming_msg.lower() == 'reset':
        user_data = reset_chat_history(user_id)
        resp.message(LANGUAGE_SELECTION_MESSAGE["en"])
        return str(resp)
    
    # Get user data
    user_data = get_chat_history(user_id)
    
    # Check if language is already selected
    if not user_data["language_selected"]:
        # Check if the message is a valid language selection
        if incoming_msg in LANGUAGES:
            # Set the selected language
            selected_lang = LANGUAGES[incoming_msg]["code"]
            user_data["language"] = selected_lang
            user_data["language_selected"] = True
            
            # Add initial assistant message in the selected language
            initial_greeting = ""
            if selected_lang == "en":
                initial_greeting = "Hello! I'm your medical assistant. Could you please tell me your name?"
            elif selected_lang == "es":
                initial_greeting = "¡Hola! Soy tu asistente médico. ¿Podrías decirme tu nombre?"
            elif selected_lang == "hi":
                initial_greeting = "नमस्ते! मैं आपका मेडिकल असिस्टेंट हूँ। क्या आप मुझे अपना नाम बता सकते हैं?"
            elif selected_lang == "fr":
                initial_greeting = "Bonjour! Je suis votre assistant médical. Pourriez-vous me dire votre nom s'il vous plaît?"
            elif selected_lang == "de":
                initial_greeting = "Hallo! Ich bin Ihr medizinischer Assistent. Könnten Sie mir bitte Ihren Namen mitteilen?"
            
            user_data["history"] = [{"role": "assistant", "content": initial_greeting}]
            resp.message(initial_greeting)
            return str(resp)
        else:
            # Invalid language selection, send language options again
            resp.message(LANGUAGE_SELECTION_MESSAGE["en"])
            return str(resp)
    
    # Add user message to chat history
    user_data["history"].append({"role": "user", "content": incoming_msg})
    
    try:
        # Check if API key is available
        if not GROQ_API_KEY:
            logger.error("GROQ_API_KEY not found in environment variables")
            resp.message("I'm sorry, the server is not properly configured. Please contact support.")
            return str(resp)
        
        # Get the appropriate system prompt for the selected language
        system_prompt = get_system_prompt_for_language(user_data["language"])
        
        # Prepare the full conversation history for the API
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(user_data["history"])
        
        # Call Groq API
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 800
        }
        
        logger.info(f"Sending request to Groq API: {GROQ_API_URL}")
        
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Groq API error: {response.status_code} - {response.text}")
            resp.message("I'm sorry, I'm having trouble connecting to my knowledge source. Please try again in a moment.")
        else:
            response_json = response.json()
            assistant_message = response_json["choices"][0]["message"]["content"]
            user_data["history"].append({"role": "assistant", "content": assistant_message})
            resp.message(assistant_message)
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        logger.error(traceback.format_exc())
        resp.message(f"I'm sorry, I encountered an error: {str(e)}")
    
    return str(resp)

@app.route('/', methods=['GET'])
def index():
    """Home page with instructions"""
    return """
    <html>
        <head>
            <title>WhatsApp Medical Assistant</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    line-height: 1.6;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                }
                h1 {
                    color: #4CAF50;
                }
                .step {
                    margin-bottom: 20px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>WhatsApp Medical Assistant</h1>
                <p>This is a WhatsApp bot that provides medical assistance.</p>
                
                <h2>How to Use</h2>
                <div class="step">
                    <h3>Step 1: Connect to WhatsApp</h3>
                    <p>Connect to the bot via WhatsApp by sending a message to the Twilio WhatsApp number.</p>
                </div>
                
                <div class="step">
                    <h3>Step 2: Select Your Language</h3>
                    <p>Choose your preferred language by responding with the corresponding number.</p>
                </div>
                
                <div class="step">
                    <h3>Step 3: Start Conversing</h3>
                    <p>The bot will guide you through a medical conversation, asking for your name, age, gender, and health concerns.</p>
                </div>
                
                <div class="step">
                    <h3>Special Commands</h3>
                    <p>Type 'reset' at any time to start over.</p>
                </div>
            </div>
        </body>
    </html>
    """

@app.route('/check', methods=['GET'])
def check():
    """Simple endpoint to verify the server is running"""
    return "WhatsApp Medical Assistant is running!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port) 