import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Web Server Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production-982374')
    
    # Database Configuration
    # Ensure you set these in your actual environment variables or .env file
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'vaug') # Encrypted/Hidden in env
    MYSQL_DB = os.environ.get('MYSQL_DB', 'statute_checker')
    
    # Email / SMTP Config for "Report Issue"
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Ad Slots (Toggle on/off)
    ENABLE_ADS = True