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
    "2": {"name": "Hindi", "code": "hi"}, 
    "3": {"name": "Tamil", "code": "ta"},
    "4": {"name": "Telugu", "code": "te"},
    "5": {"name": "Kannada", "code": "kn"},
    "6": {"name": "Malayalam", "code": "ml"}
}

# Translated language selection message
LANGUAGE_SELECTION_MESSAGE = {
    "en": "Welcome to the Medical Assistant! Please select your preferred language:\n1️⃣ English\n2️⃣ Hindi\n3️⃣ Tamil\n4️⃣ Telugu\n5️⃣ Kannada\n6️⃣ Malayalam\n\nReply with the number of your choice. You can type 'stop' at any time to end our conversation.",
    "hi": "मेडिकल असिस्टेंट में आपका स्वागत है! कृपया अपनी पसंदीदा भाषा चुनें:\n1️⃣ अंग्रे़ी\n2️⃣ हिंदी\n3️⃣ तमिल\n4️⃣ तेलुगु\n5️⃣ कन्नड़\n6️⃣ मलयालम\n\nअपनी पसंद का नंबर लिखकर जवाब दें। आप किसी भी समय बातचीत समाप्त करने के लिए 'stop' टाइप कर सकते हैं।",
    "ta": "மருத்துவ உதவியாளருக்கு வரவேற்கிறோம்! உங்கள் விருப்பமான மொழியைத் தேர்ந்தெடுக்கவும்:\n1️⃣ ஆங்கிலம்\n2️⃣ இந்தி\n3️⃣ தமிழ்\n4️⃣ தெலுங்கு\n5️⃣ கன்னடம்\n6️⃣ மலையாளம்\n\nஉங்கள் தேர்வின் எண்ணுடன் பதிலளிக்கவும். எந்த நேரத்திலும் உரையாடலை முடிக்க 'stop' என்று தட்டச்சு செய்யலாம்.",
    "te": "మెడికల్ అసిస్టెంట్‌కి స్వాగతం! దయచేసి మీ ప్రాధాన్య భాషను ఎంచుకోండి:\n1️⃣ ఇంగ్లీష్\n2️⃣ హిందీ\n3️⃣ తమిళం\n4️⃣ తెలుగు\n5️⃣ కన్నడ\n6️⃣ మలయాళం\n\nమీ ఎంపిక సంఖ్యతో ప్రతిస్పందించండి. మీరు ఎప్పుడైనా సంభాషణను ముగించడానికి 'stop' అని టైప్ చేయవచ్చు.",
    "kn": "ವೈದ್ಯಕೀಯ ಸಹಾಯಕಕ್ಕೆ ಸುಸ್ವಾಗತ! ದಯವಿಟ್ಟು ನಿಮ್ಮ ಆದ್ಯತೆಯ ಭಾಷೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ:\n1️⃣ ಇಂಗ್ಲಿಷ್\n2️⃣ ಹಿಂದಿ\n3️⃣ ತಮಿಳು\n4️⃣ ತೆಲುಗು\n5️⃣ ಕನ್ನಡ\n6️⃣ ಮಲಯಾಳಂ\n\nನಿಮ್ಮ ಆಯ್ಕೆಯ ಸಂಖ್ಯೆಯೊಂದಿಗೆ ಉತ್ತರಿಸಿ. ಯಾವುದೇ ಸಮಯದಲ್ಲಿ ಸಂಭಾಷಣೆಯನ್ನು ಕೊನೆಗೊಳಿಸಲು ನೀವು 'stop' ಎಂದು ಟೈಪ್ ಮಾಡಬಹುದು.",
    "ml": "മെഡിക്കൽ അസിസ്റ്റന്റിലേക്ക് സ്വാഗതം! നിങ്ങളുടെ ഇഷ്ടപ്പെട്ട ഭാഷ തിരഞ്ഞെടുക്കുക:\n1️⃣ ഇംഗ്ലീഷ്\n2️⃣ ഹിന്ദി\n3️⃣ തമിഴ്\n4️⃣ തെലുങ്ക്\n5️⃣ കന്നഡ\n6️⃣ മലയാളം\n\nനിങ്ങളുടെ തിരഞ്ഞെടുക്കലിന്റെ നമ്പർ ഉപയോഗിച്ച് മറുപടി നൽകുക. നിങ്ങൾക്ക് എപ്പോൾ വേണമെങ്കിലും സംഭാഷണം അവസാനിപ്പിക്കാൻ 'stop' എന്ന് ടൈപ്പ് ചെയ്യാം."
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
    elif language_code == "hi":
        # Hindi system prompt
        return SYSTEM_PROMPT.replace("You are a friendly", "आप एक मित्रवत").replace("medical assistant", "चिकित्सा सहायक हैं")
    elif language_code == "ta":
        # Tamil system prompt
        return SYSTEM_PROMPT.replace("You are a friendly", "நீங்கள் ஒரு நட்பான").replace("medical assistant", "மருத்துவ உதவியாளர்")
    elif language_code == "te":
        # Telugu system prompt
        return SYSTEM_PROMPT.replace("You are a friendly", "మీరు స్నేహపూర్వకమైన").replace("medical assistant", "వైద్య సహాయకులు")
    elif language_code == "kn":
        # Kannada system prompt
        return SYSTEM_PROMPT.replace("You are a friendly", "ನೀವು ಸ್ನೇಹಪರ").replace("medical assistant", "ವೈದ್ಯಕೀಯ ಸಹಾಯಕ")
    elif language_code == "ml":
        # Malayalam system prompt
        return SYSTEM_PROMPT.replace("You are a friendly", "നിങ്ങൾ ഒരു സൗഹൃദപരമായ").replace("medical assistant", "മെഡിക്കൽ അസിസ്റ്റന്റ് ആണ്")
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
    
    # Stop command
    if incoming_msg.lower() == 'stop':
        # Add a goodbye message based on user's selected language
        user_data = get_chat_history(user_id)
        lang_code = user_data.get("language", "en")
        
        goodbye_messages = {
            "en": "Thank you for using the Medical Assistant. Your conversation has been ended. Type 'reset' if you'd like to start a new conversation in the future.",
            "hi": "मेडिकल असिस्टेंट का उपयोग करने के लिए धन्यवाद। आपकी बातचीत समाप्त हो गई है। यदि आप भविष्य में नई बातचीत शुरू करना चाहते हैं तो 'reset' टाइप करें।",
            "ta": "மருத்துவ உதவியாளரைப் பயன்படுத்தியதற்கு நன்றி. உங்கள் உரையாடல் முடிந்தது. எதிர்காலத்தில் புதிய உரையாடலைத் தொடங்க விரும்பினால் 'reset' என்று தட்டச்சு செய்யவும்.",
            "te": "మెడికల్ అసిస్టెంట్‌ని ఉపయోగించినందుకు ధన్యవాదాలు. మీ సంభాషణ ముగిసింది. భవిష్యత్తులో కొత్త సంభాషణను ప్రారంభించాలనుకుంటే 'reset' టైప్ చేయండి.",
            "kn": "ವೈದ್ಯಕೀಯ ಸಹಾಯಕವನ್ನು ಬಳಸಿದ್ದಕ್ಕಾಗಿ ಧನ್ಯವಾದಗಳು. ನಿಮ್ಮ ಸಂಭಾಷಣೆಯನ್ನು ಕೊನೆಗೊಳಿಸಲಾಗಿದೆ. ಭವಿಷ್ಯದಲ್ಲಿ ಹೊಸ ಸಂಭಾಷಣೆಯನ್ನು ಪ್ರಾರಂಭಿಸಲು ನೀವು 'stop' ಎಂದು ಟೈಪ್ ಮಾಡಬಹುದು.",
            "ml": "മെഡിക്കൽ അസിസ്റ്റന്റ് ഉപയോഗിച്ചതിന് നന്ദി. നിങ്ങളുടെ സംഭാഷണം അവസാനിച്ചു. ഭാവിയിൽ പുതിയ സംഭാഷണം ആരംഭിക്കാൻ നിങ്ങൾക്ക് ആഗ്രഹിക്കുന്നുവെങ്കിൽ 'reset' എന്ന് ടൈപ്പ് ചെയ്യാം."
        }
        
        goodbye_message = goodbye_messages.get(lang_code, goodbye_messages["en"])
        resp.message(goodbye_message)
        
        # We don't actually delete the session data to allow them to resume with 'reset'
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
                initial_greeting = "Hello! I'm your medical assistant. Could you please tell me your name? You can type 'stop' at any time to end our conversation."
            elif selected_lang == "hi":
                initial_greeting = "नमस्ते! मैं आपका मेडिकल असिस्टेंट हूँ। क्या आप मुझे अपना नाम बता सकते हैं? आप किसी भी समय बातचीत समाप्त करने के लिए 'stop' टाइप कर सकते हैं।"
            elif selected_lang == "ta":
                initial_greeting = "வணக்கம்! நான் உங்கள் மருத்துவ உதவியாளர். உங்கள் பெயரை தயவுசெய்து சொல்ல முடியுமா? எந்த நேரத்திலும் உரையாடலை முடிக்க 'stop' என்று தட்டச்சு செய்யலாம்."
            elif selected_lang == "te":
                initial_greeting = "హలో! నేను మీ మెడికల్ అసిస్టెంట్‌ని. దయచేసి మీ పేరు చెప్పగలరా? మీరు ఎప్పుడైనా సంభాషణను ముగించడానికి 'stop' అని టైప్ చేయవచ్చు."
            elif selected_lang == "kn":
                initial_greeting = "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ವೈದ್ಯಕೀಯ ಸಹಾಯಕ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ಹೆಸರನ್ನು ತಿಳಿಸಬಹುದೇ? ಯಾವುದೇ ಸಮಯದಲ್ಲಿ ಸಂಭಾಷಣೆಯನ್ನು ಕೊನೆಗೊಳಿಸಲು ನೀವು 'stop' ಎಂದು ಟೈಪ್ ಮಾಡಬಹುದು."
            elif selected_lang == "ml":
                initial_greeting = "ഹലോ! ഞാൻ നിങ്ങളുടെ മെഡിക്കൽ അസിസ്റ്റന്റാണ്. നിങ്ങളുടെ പേര് ദയവായി പറയാമോ? നിങ്ങൾക്ക് എപ്പോൾ വേണമെങ്കിലും സംഭാഷണം അവസാനിപ്പിക്കാൻ 'stop' എന്ന് ടൈപ്പ് ചെയ്യാം."
            
            user_data["history"] = [{"role": "assistant", "content": initial_greeting}]
            resp.message(initial_greeting)
            return str(resp)
        else:
            # Invalid language selection, send language options again
            resp.message(LANGUAGE_SELECTION_MESSAGE["en"] + "\n\nYou can type 'stop' at any time to end our conversation.")
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
                    <p>Type 'stop' at any time to end the conversation.</p>
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