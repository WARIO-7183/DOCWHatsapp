import os
from dotenv import load_dotenv
import logging
from supabase import create_client, Client
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Initialize Supabase client
supabase: Client = None

def get_supabase_client():
    """Create and return a Supabase client"""
    global supabase
    if supabase is None:
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Error connecting to Supabase: {e}")
            return None
    return supabase

def init_db():
    """Initialize the database and create tables if they don't exist"""
    try:
        client = get_supabase_client()
        if client:
            # In Supabase, tables are created through the dashboard or migrations
            # This function is kept for compatibility with the existing code
            logger.info("Database initialized successfully")
            return True
        else:
            logger.error("Failed to initialize database")
            return False
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

def get_user(phone_number):
    """Get user details from the database"""
    try:
        client = get_supabase_client()
        if client:
            response = client.table('users').select('*').eq('phone_number', phone_number).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return None

def create_user(phone_number, name, age, gender, medical_history="", language="en"):
    """Create a new user in the database"""
    try:
        client = get_supabase_client()
        if client:
            now = datetime.now().isoformat()
            user_data = {
                'phone_number': phone_number,
                'name': name,
                'age': age,
                'gender': gender,
                'medical_history': medical_history,
                'language': language,
                'created_at': now,
                'updated_at': now
            }
            response = client.table('users').insert(user_data).execute()
            return True
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return False

def update_user_medical_history(phone_number, medical_history):
    """Update user's medical history"""
    try:
        client = get_supabase_client()
        if client:
            now = datetime.now().isoformat()
            response = client.table('users').update({
                'medical_history': medical_history,
                'updated_at': now
            }).eq('phone_number', phone_number).execute()
            return True
    except Exception as e:
        logger.error(f"Error updating user medical history: {e}")
        return False

def update_user_language(phone_number, language):
    """Update user's preferred language"""
    try:
        client = get_supabase_client()
        if client:
            now = datetime.now().isoformat()
            response = client.table('users').update({
                'language': language,
                'updated_at': now
            }).eq('phone_number', phone_number).execute()
            return True
    except Exception as e:
        logger.error(f"Error updating user language: {e}")
        return False 