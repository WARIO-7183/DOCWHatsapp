import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'Ayush@72'),
    'database': os.getenv('DB_NAME', 'medical_assistant')
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        logger.error(f"Error connecting to MySQL: {e}")
        return None

def init_db():
    """Initialize the database and create tables if they don't exist"""
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    phone_number VARCHAR(20) PRIMARY KEY,
                    name VARCHAR(100),
                    age INT,
                    gender VARCHAR(10),
                    medical_history TEXT,
                    language VARCHAR(10) DEFAULT 'en',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            connection.commit()
            logger.info("Database initialized successfully")
        else:
            logger.error("Failed to initialize database")
    except Error as e:
        logger.error(f"Error initializing database: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def get_user(phone_number):
    """Get user details from the database"""
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE phone_number = %s", (phone_number,))
            user = cursor.fetchone()
            return user
    except Error as e:
        logger.error(f"Error getting user: {e}")
        return None
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def create_user(phone_number, name, age, gender, medical_history="", language="en"):
    """Create a new user in the database"""
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO users (phone_number, name, age, gender, medical_history, language)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (phone_number, name, age, gender, medical_history, language))
            connection.commit()
            return True
    except Error as e:
        logger.error(f"Error creating user: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def update_user_medical_history(phone_number, medical_history):
    """Update user's medical history"""
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE users 
                SET medical_history = %s
                WHERE phone_number = %s
            """, (medical_history, phone_number))
            connection.commit()
            return True
    except Error as e:
        logger.error(f"Error updating user medical history: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def update_user_language(phone_number, language):
    """Update user's preferred language"""
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE users 
                SET language = %s
                WHERE phone_number = %s
            """, (language, phone_number))
            connection.commit()
            return True
    except Error as e:
        logger.error(f"Error updating user language: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close() 