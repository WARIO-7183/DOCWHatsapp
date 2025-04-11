import os
import json
import requests
import logging
from dotenv import load_dotenv
from database import get_user

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY not found in environment variables")
    raise ValueError("OPENAI_API_KEY environment variable is required")

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

def summarize_medical_history(phone_number):
    """
    Summarize a patient's medical history using OpenAI LLM
    
    Args:
        phone_number (str): The patient's phone number
        
    Returns:
        dict: A dictionary containing the summary and status
    """
    # Check if API key is available
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not found in environment variables")
        return {
            "success": False,
            "error": "API key not configured",
            "summary": None
        }
    
    # Get user from database
    user = get_user(phone_number)
    
    if not user:
        logger.error(f"User with phone number {phone_number} not found")
        return {
            "success": False,
            "error": "User not found",
            "summary": None
        }
    
    # Extract medical history
    medical_history = user.get("medical_history", "")
    
    if not medical_history:
        logger.info(f"No medical history found for user {phone_number}")
        return {
            "success": True,
            "error": None,
            "summary": "No medical history available for this patient."
        }
    
    try:
        # Prepare the prompt for the LLM
        system_prompt = """
        You are a medical assistant tasked with summarizing a patient's medical history.
        Please provide a concise, well-structured summary of the patient's medical history,
        highlighting key information such as:
        
        1. Patient's basic information (name, age, gender)
        2. Chronic conditions or ongoing health issues
        3. Past medical procedures or surgeries
        4. Current medications
        5. Allergies or adverse reactions
        6. Family history of significant conditions
        
        Format your response in a clear, professional manner that would be useful for a healthcare provider.
        """
        
        # Prepare the messages for the API
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Please summarize the following medical history:\n\n{medical_history}"}
        ]
        
        # Call OpenAI API
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4o",
            "messages": messages,
            "temperature": 0.3,  # Lower temperature for more focused, consistent output
            "max_tokens": 1000
        }
        
        logger.info(f"Sending request to OpenAI API for summarizing medical history of {phone_number}")
        
        response = requests.post(OPENAI_API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
            return {
                "success": False,
                "error": f"API error: {response.status_code}",
                "summary": None
            }
        
        # Extract the summary from the response
        response_json = response.json()
        summary = response_json["choices"][0]["message"]["content"]
        
        return {
            "success": True,
            "error": None,
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Error summarizing medical history: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "summary": None
        }

def main():
    """Main function to run the summarization tool"""
    print("Medical History Summarization Tool")
    print("==================================")
    
    phone_number = input("Enter patient's phone number: ")
    
    result = summarize_medical_history(phone_number)
    
    if result["success"]:
        print("\nSummary of Medical History:")
        print("===========================")
        print(result["summary"])
    else:
        print(f"\nError: {result['error']}")

if __name__ == "__main__":
    main() 