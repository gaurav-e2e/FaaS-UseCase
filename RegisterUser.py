

import json
import os
import random
import logging
import asyncio
import aiohttp
import mysql.connector
from mysql.connector import Error

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Environment variables
DB_CONFIG = {
    'host': os.environ['DB_HOST'],
    'user': os.environ['DB_USER'],
    'password': os.environ['DB_PASSWORD'],
    'database': 'webhook'
}
EMAIL_FUNCTION_URL = os.environ['EMAIL_FUNCTION_URL']

def handle(event, context):
    logger.info("Function invoked")
    payload = json.loads(event.body)
    
    user_data = validate_user(payload)
    if not user_data:
        logger.warning("User validation failed")
        return {"statusCode": 400, "body": "Details are not correct"}
    
    db_response = asyncio.run(register_user(user_data))
    return db_response

def validate_user(user_data):
    logger.info("Validating user data")
    required_fields = ['name', 'email', 'password']
    if not all(user_data.get(field) for field in required_fields):
        logger.warning("Missing required user data fields")
        return None

    logger.info("User data validation successful")
    return {field: user_data[field] for field in required_fields}

class Database:
    def __init__(self, config):
        logger.info("Initializing database connection")
        self.conn = mysql.connector.connect(**config)
        self.cursor = self.conn.cursor()

    def save_user_data(self, user_data):
        logger.info(f"Saving user data for: {user_data['email']}")
        query = "INSERT INTO Customer (name, email, password, otp) VALUES (%s, %s, %s, %s)"
        try:
            self.cursor.execute(query, (user_data["name"], user_data["email"], user_data["password"], user_data["otp"]))
            self.conn.commit()
            logger.info("User data saved successfully")
            return {"statusCode": 200, "body": json.dumps({"message": "Customer added successfully"})}
        except Error as e:
            logger.error(f"Database error: {e}")
            return {"statusCode": 500, "body": f"Database error: {e}"}
        finally:
            self.cursor.close()
            self.conn.close()

def generate_otp():
    otp = str(random.randint(100000, 999999))
    logger.info(f"OTP generated: {otp}")
    return otp

async def send_otp(email, otp):
    logger.info(f"Sending OTP to: {email}")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(EMAIL_FUNCTION_URL, json={"email": email, "otp": otp}) as response:
                await response.text()
            logger.info("OTP sent successfully")
        except Exception as e:
            logger.error(f"Error sending OTP: {e}")

async def register_user(user_data):
    logger.info(f"Registering user: {user_data['email']}")
    user_data["otp"] = generate_otp()
    
    db = Database(DB_CONFIG)
    db_response = db.save_user_data(user_data)
    if db_response["statusCode"] != 200:
        return db_response
    
    await send_otp(user_data["email"], user_data["otp"])
    return {"statusCode": 200, "body": json.dumps({"message": "OTP sent to your email"})}
