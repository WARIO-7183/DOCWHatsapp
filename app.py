from flask import Flask, request, Response
import os
from dotenv import load_dotenv
import requests
import traceback
import logging
from twilio.twiml.messaging_response import MessagingResponse
import json
from database import init_db, get_user, create_user, update_user_medical_history, update_user_language
    
# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Common Indian medicines by category
COMMON_MEDICINES = {
    "fever": [
        {"name": "Crocin", "brand": "GSK", "generic": "Paracetamol"},
        {"name": "Dolo 650", "brand": "Micro Labs", "generic": "Paracetamol"},
        {"name": "Calpol", "brand": "GSK", "generic": "Paracetamol"},
        {"name": "Sumo", "brand": "CFL Pharma", "generic": "Paracetamol"},
        {"name": "Febrinil", "brand": "Aristo", "generic": "Paracetamol"}
    ],
    "headache": [
        {"name": "Saridon", "brand": "Bayer", "generic": "Propyphenazone+Paracetamol"},
        {"name": "Dart", "brand": "Cipla", "generic": "Paracetamol+Caffeine"},
        {"name": "Disprin", "brand": "Reckitt", "generic": "Aspirin"},
        {"name": "Combiflam", "brand": "Sanofi", "generic": "Ibuprofen+Paracetamol"}
    ],
    "cold": [
        {"name": "Vicks Action 500", "brand": "P&G", "generic": "Paracetamol+Phenylephrine"},
        {"name": "D'Cold Total", "brand": "Reckitt", "generic": "Paracetamol+Phenylephrine"},
        {"name": "Coldarin", "brand": "Alkem", "generic": "Phenylephrine+Chlorpheniramine"},
        {"name": "Sinarest", "brand": "Centaur", "generic": "Paracetamol+Phenylephrine+Caffeine"},
        {"name": "Nasivion", "brand": "Merck", "generic": "Oxymetazoline"}
    ],
    "allergies": [
        {"name": "Allegra", "brand": "Sanofi", "generic": "Fexofenadine"},
        {"name": "Cetrizine", "brand": "Various", "generic": "Cetirizine"},
        {"name": "Montek LC", "brand": "Sun Pharma", "generic": "Montelukast+Levocetirizine"},
        {"name": "Avil", "brand": "Sanofi", "generic": "Pheniramine Maleate"},
        {"name": "Teczine", "brand": "GSK", "generic": "Levocetirizine"}
    ],
    "stomach_pain": [
        {"name": "Buscopan", "brand": "Sanofi", "generic": "Hyoscine Butylbromide"},
        {"name": "Cyclopam", "brand": "Indoco", "generic": "Dicyclomine"},
        {"name": "Meftal Spas", "brand": "Blue Cross", "generic": "Mefenamic Acid+Dicyclomine"},
        {"name": "Spasmo Proxyvon", "brand": "Wockhardt", "generic": "Dicyclomine+Paracetamol"}
    ],
    "acidity": [
        {"name": "Eno", "brand": "GSK", "generic": "Sodium Bicarbonate+Citric Acid"},
        {"name": "Digene", "brand": "Abbott", "generic": "Magnesium Hydroxide+Simethicone"},
        {"name": "Gelusil", "brand": "Pfizer", "generic": "Aluminium Hydroxide+Magnesium Hydroxide"},
        {"name": "Pan-D", "brand": "Alkem", "generic": "Pantoprazole+Domperidone"},
        {"name": "Aciloc", "brand": "Cadila", "generic": "Ranitidine"}
    ],
    "diarrhea": [
        {"name": "Lopamide", "brand": "Cipla", "generic": "Loperamide"},
        {"name": "Eldoper", "brand": "Micro Labs", "generic": "Loperamide"},
        {"name": "Norflox-TZ", "brand": "Cipla", "generic": "Norfloxacin+Tinidazole"},
        {"name": "Enteroquinol", "brand": "Sanofi", "generic": "Clioquinol"},
        {"name": "ORS", "brand": "Various", "generic": "Oral Rehydration Solution"}
    ],
    "pain_relief": [
        {"name": "Combiflam", "brand": "Sanofi", "generic": "Ibuprofen+Paracetamol"},
        {"name": "Brufen", "brand": "Abbott", "generic": "Ibuprofen"},
        {"name": "Voveran", "brand": "Novartis", "generic": "Diclofenac"},
        {"name": "Ultracet", "brand": "J&J", "generic": "Tramadol+Paracetamol"},
        {"name": "Flexon", "brand": "Dr. Reddy's", "generic": "Etoricoxib"}
    ],
    "cough": [
        {"name": "Benadryl", "brand": "J&J", "generic": "Diphenhydramine"},
        {"name": "Honitus", "brand": "Dabur", "generic": "Herbal Formulation"},
        {"name": "Ascoril", "brand": "Glenmark", "generic": "Terbutaline+Bromhexine"},
        {"name": "Koflet", "brand": "Himalaya", "generic": "Herbal Formulation"},
        {"name": "Chericof", "brand": "Cipla", "generic": "Codeine+Chlorpheniramine"}
    ],
    "vitamins": [
        {"name": "Becosules", "brand": "Pfizer", "generic": "B-Complex+Vitamin C"},
        {"name": "Supradyn", "brand": "Bayer", "generic": "Multivitamin+Minerals"},
        {"name": "Shelcal", "brand": "Torrent", "generic": "Calcium+Vitamin D3"},
        {"name": "Neurobion", "brand": "Merck", "generic": "B1+B6+B12"},
        {"name": "Zincovit", "brand": "Apex", "generic": "Multivitamin+Zinc"}
    ]
}

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
12. For common ailments, suggest 2-3 specific over-the-counter medicines available in India from our medicine list, including both brand name and generic name. For example: "For your fever, you might consider taking Dolo 650 (Paracetamol) or Crocin (Paracetamol)."
13. After suggesting medication, recommend consulting a healthcare professional for proper diagnosis and treatment.
14. DO NOT repeatedly state that you're an AI assistant or that you're not a replacement for professional medical care. Only mention this at the very end of the conversation.
15. When discussing serious symptoms, recommend seeing a doctor immediately.
16. Prioritize clarity and brevity over comprehensiveness.

Remember: Be conversational and human-like. Follow the exact sequence: 1) ask name, 2) ask age and gender, 3) ask about medical conditions with examples.
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
    "en": "Welcome to the Medical Assistant! Please select your preferred language:\n1️⃣ English\n2️⃣ Hindi\n3️⃣ Tamil\n4️⃣ Telugu\n5️⃣ Kannada\n6️⃣ Malayalam\n\nReply with the number of your choice.",
    "hi": "मेडिकल असिस्टेंट में आपका स्वागत है! कृपया अपनी पसंदीदा भाषा चुनें:\n1️⃣ अंग्रे़ी\n2️⃣ हिंदी\n3️⃣ तमिल\n4️⃣ तेलुगु\n5️⃣ कन्नड़\n6️⃣ मलयालम\n\nअपनी पसंद का नंबर लिखकर जवाब दें।",
    "ta": "மருத்துவ உதவியாளருக்கு வரவேற்கிறோம்! உங்கள் விருப்பமான மொழியைத் தேர்ந்தெடுக்கவும்:\n1️⃣ ஆங்கிலம்\n2️⃣ இந்தி\n3️⃣ தமிழ்\n4️⃣ தெலுங்கு\n5️⃣ கன்னடம்\n6️⃣ மலையாளம்\n\nஉங்கள் தேர்வின் எண்ணுடன் பதிலளிக்கவும்.",
    "te": "మెడికల్ అసిస్టెంట్‌ని ఉపయోగించినందుకు ధన్యవాదాలు. మీ సంభాషణ ముగిసింది. భవిష్యత్తులో కొత్త సంభాషణను ప్రారంభించాలనుకుంటే 'reset' టైప్ చేయండి.",
    "kn": "ವೈದ್ಯಕೀಯ ಸಹಾಯಕಕ್ಕೆ ಸುಸ್ವಾಗತ! ದಯವಿಟ್ಟು ನಿಮ್ಮ ಆದ್ಯತೆಯ ಭಾಷೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ:\n1️⃣ ಇಂಗ್ಲಿಷ್\n2️⃣ ಹಿಂದಿ\n3️⃣ ತಮಿಳು\n4️⃣ ತೆಲುಗು\n5️⃣ ಕನ್ನಡ\n6️⃣ ಮಲಯಾಳಂ\n\nನಿಮ್ಮ ಆಯ್ಕೆಯ ಸಂಖ್ಯೆಯೊಂದಿಗೆ ಉತ್ತರಿಸಿ.",
    "ml": "മെഡിക്കൽ അസിസ്റ്റന്റ് ആണ്! നിങ്ങളുടെ ഇഷ്ടപ്പെട്ട ഭാഷ തിരഞ്ഞെടുക്കുക:\n1️⃣ ഇംഗ്ലീഷ്\n2️⃣ ഹിന്ദി\n3️⃣ തമിഴ്\n4️⃣ തെലുങ്ക്\n5️⃣ കന്നഡ\n6️⃣ മലയാളം\n\nനിങ്ങളുടെ തിരഞ്ഞെടുക്കലിന്റെ നമ്പർ ഉപയോഗിച്ച് മറുപടി നൽകുക."
}

# Initialize database on startup
init_db()

# Store chat history per user
user_sessions = {}

def get_chat_history(user_id):
    """Get or initialize chat history for a user"""
    if user_id not in user_sessions:
        # Check if user exists in database
        user = get_user(user_id)
        if user:
            # Initialize session with user data from database
            user_sessions[user_id] = {
                "language_selected": True,
                "language": user['language'],
                "history": [],
                "name": user['name'],
                "age": user['age'],
                "gender": user['gender'],
                "medical_history": user['medical_history']
            }
        else:
            # Initialize new session
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
    
    # Bye command
    if incoming_msg.lower() == 'bye':
        # Reset chat history and add a goodbye message based on user's selected language
        user_data = reset_chat_history(user_id)
        lang_code = user_data.get("language", "en")
        
        goodbye_messages = {
            "en": "Thank you for using the Medical Assistant. Your conversation has been ended. Type 'bye' if you'd like to end the conversation and start a new one.",
            "hi": "मेडिकल असिस्टेंट का उपयोग करने के लिए धन्यवाद। आपकी बातचीत समाप्त हो गई है। यदि आप बातचीत समाप्त करना और एक नई बातचीत शुरू करना चाहते हैं तो 'bye' टाइप करें।",
            "ta": "மருத்துவ உதவியாளரைப் பயன்படுத்தியதற்கு நன்றி. உங்கள் உரையாடல் முடிந்தது. உரையாடலை முடிக்கவும் புதிய உரையாடலைத் தொடங்கவும் 'bye' என்று தட்டச்சு செய்யவும்.",
            "te": "మెడికల్ అసిస్టెంట్‌ని ఉపయోగించినందుకు ధన్యవాదాలు. మీ సంభాషణ ముగిసింది. సంభాషణను ముగించడానికి మరియు కొత్త సంభాషణను ప్రారంభించడానికి 'bye' టైప్ చేయండి.",
            "kn": "ವೈದ್ಯಕೀಯ ಸಹಾಯಕವನ್ನು ಬಳಸಿದ್ದಕ್ಕಾಗಿ ಧನ್ಯವಾದಗಳು. ನಿಮ್ಮ ಸಂಭಾಷಣೆಯನ್ನು ಕೊನೆಗೊಳಿಸಲಾಗಿದೆ. ಸಂಭಾಷಣೆಯನ್ನು ಕೊನೆಗೊಳಿಸಲು ಮತ್ತು ಹೊಸ ಸಂಭಾಷಣೆಯನ್ನು ಪ್ರಾರಂಭಿಸಲು ನೀವು 'bye' ಎಂದು ಟೈಪ್ ಮಾಡಬಹುದು.",
            "ml": "മെഡിക്കൽ അസിസ്റ്റന്റ് ഉപയോഗിച്ചതിന് നന്ദി. നിങ്ങളുടെ സംഭാഷണം അവസാനിച്ചു. സംഭാഷണനു മുഗ്യിക്കാൻ മത്തു സംഭാഷണനു പ്രാരംഭിസ്റ്റുകയും നിങ്ങൾക്ക് ആഗ്രഹിക്കുന്നുവെങ്കിൽ 'bye' എന്ന് ടൈപ്പ് ചെയ്യാം."
        }
        
        goodbye_message = goodbye_messages.get(lang_code, goodbye_messages["en"])
        resp.message(goodbye_message)
        
        # Prompt user to select language again
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
            
            # Update language in database if user exists
            if "name" in user_data:
                update_user_language(user_id, selected_lang)
            
            # Add initial assistant message in the selected language
            initial_greeting = ""
            if selected_lang == "en":
                initial_greeting = "Hello! I'm your medical assistant. Could you please tell me your phone number?"
            elif selected_lang == "hi":
                initial_greeting = "नमस्ते! मैं आपका मेडिकल असिस्टेंट हूँ। क्या आप मुझे अपना फोन नंबर बता सकते हैं?"
            elif selected_lang == "ta":
                initial_greeting = "வணக்கம்! நான் உங்கள் மருத்துவ உதவியாளர். உங்கள் தொலைபேசி எண்ணை தயவுசெய்து சொல்ல முடியுமா?"
            elif selected_lang == "te":
                initial_greeting = "హలో! నేను మీ మెడికల్ అసిస్టెంట్‌ని. దయచేసి మీ ఫోన్ నంబర్ చెప్పగలరా?"
            elif selected_lang == "kn":
                initial_greeting = "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ವೈದ್ಯಕೀಯ ಸಹಾಯಕ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ಫೋನ್ ಸಂಖ್ಯೆಯನ್ನು ತಿಳಿಸಬಹುದೇ?"
            elif selected_lang == "ml":
                initial_greeting = "ഹലോ! ഞാൻ നിങ്ങളുടെ മെഡിക്കൽ അസിസ്റ്റന്റാണ്. നിങ്ങളുടെ ഫോൺ നമ്പർ ദയവായി പറയാമോ?"
            
            user_data["history"] = [{"role": "assistant", "content": initial_greeting}]
            resp.message(initial_greeting)
            return str(resp)
        else:
            # Invalid language selection, send language options again
            resp.message(LANGUAGE_SELECTION_MESSAGE["en"])
            return str(resp)
    
    # Add user message to chat history
    user_data["history"].append({"role": "user", "content": incoming_msg})
    
    # Check if phone number is provided
    if "phone_number" not in user_data:
        user_data["phone_number"] = incoming_msg
        # Check if user exists in database
        db_user = get_user(incoming_msg)
        if db_user:
            # User exists, load their data
            user_data.update({
                "name": db_user["name"],
                "age": db_user["age"],
                "gender": db_user["gender"],
                "medical_history": db_user["medical_history"]
            })
            # Ask about current health concerns
            next_question = f"Welcome back {db_user['name']}! How can I help you today?"
        else:
            # New user, ask for name
            next_question = "Could you please tell me your name?"
        
        user_data["history"].append({"role": "assistant", "content": next_question})
        resp.message(next_question)
        return str(resp)
    
    # Check if name is provided
    if "name" not in user_data:
        user_data["name"] = incoming_msg
        next_question = "Thank you! Could you please tell me your age?"
        user_data["history"].append({"role": "assistant", "content": next_question})
        resp.message(next_question)
        return str(resp)
    
    # Check if age is provided
    if "age" not in user_data:
        user_data["age"] = incoming_msg
        next_question = "Please select your gender:\n1️⃣ Male\n2️⃣ Female\n3️⃣ Other (please specify)"
        user_data["history"].append({"role": "assistant", "content": next_question})
        resp.message(next_question)
        return str(resp)
    
    # Check if gender is provided
    if "gender" not in user_data:
        # Process gender selection
        if incoming_msg == "1":
            user_data["gender"] = "Male"
        elif incoming_msg == "2":
            user_data["gender"] = "Female"
        else:
            user_data["gender"] = incoming_msg  # Store the custom gender input
        
        # Create new user in database
        create_user(
            user_data["phone_number"],
            user_data["name"],
            user_data["age"],
            user_data["gender"],
            language=user_data["language"]
        )
        next_question = "Do you have any of the following health issues? (Reply with the number or type 'none' if you don't have any):\n1️⃣ Diabetes\n2️⃣ Blood Pressure\n3️⃣ Chronic Problems\n4️⃣ Kidney or Liver Issues\n5️⃣ Other (please specify)"
        user_data["history"].append({"role": "assistant", "content": next_question})
        resp.message(next_question)
        return str(resp)
    
    # Check if previous health issues are provided
    if "previous_health_issues" not in user_data:
        user_data["previous_health_issues"] = incoming_msg
        next_question = "Have you undergone any surgeries? (Reply with the number or type 'none' if you haven't):\n1️⃣ Appendectomy\n2️⃣ C-section\n3️⃣ Knee/Hip Replacement\n4️⃣ Heart Surgery\n5️⃣ Other (please specify)"
        user_data["history"].append({"role": "assistant", "content": next_question})
        resp.message(next_question)
        return str(resp)
    
    # Check if surgeries are provided
    if "surgeries" not in user_data:
        user_data["surgeries"] = incoming_msg
        next_question = "What health concerns or symptoms would you like to discuss today?"
        user_data["history"].append({"role": "assistant", "content": next_question})
        resp.message(next_question)
        return str(resp)
    
    try:
        # Check if API key is available
        if not GROQ_API_KEY:
            logger.error("GROQ_API_KEY not found in environment variables")
            resp.message("I'm sorry, the server is not properly configured. Please contact support.")
            return str(resp)
        
        # Get the appropriate system prompt for the selected language
        system_prompt = get_system_prompt_for_language(user_data["language"])
        
        # Add medicine data to the system prompt
        medicine_info = f"\n\nAvailable medicines by category: {json.dumps(COMMON_MEDICINES, indent=2)}"
        enhanced_system_prompt = system_prompt + medicine_info
        
        # Prepare the full conversation history for the API
        messages = [{"role": "system", "content": enhanced_system_prompt}]
        messages.extend(user_data["history"])
        
        # Call Groq API
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gemma2-9b-it",
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
            
            # Update medical history in database
            medical_history = json.dumps(user_data["history"])
            update_user_medical_history(user_data["phone_number"], medical_history)
            
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
                    <p>Type 'bye' at any time to end the conversation.</p>
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