from flask import Flask, request, jsonify
from flask_cors import CORS
try:
    from pymongo import MongoClient
    from werkzeug.security import generate_password_hash, check_password_hash
except ImportError:
    raise ImportError("Required modules not found. Ensure 'pymongo' and 'werkzeug' are installed.")

from dotenv import load_dotenv
import os
import jwt
import datetime

load_dotenv()

# Secret key for JWT (you should keep this secret and not expose it in your code)
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key_here")

app = Flask(__name__)
CORS(app)  

try:
    client = MongoClient("mongodb+srv://suchetavadakkepat:6EHrFpVzLxvGzgbe@cluster0.kmlv7.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    db = client["loyalty_program"]
    users_collection = db["users"]
except Exception as e:
    raise ConnectionError(f"Failed to connect to the database: {e}")

# Function to generate JWT token
def generate_token(user_email):
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Token expires in 1 hour
    token = jwt.encode({"email": user_email, "exp": expiration_time}, SECRET_KEY, algorithm="HS256")
    return token

# Function to decode and verify JWT token
def decode_token(token):
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded["email"]
    except jwt.ExpiredSignatureError:
        return None  # Token has expired
    except jwt.InvalidTokenError:
        return None  # Invalid token

# Function to check for token authorization
def token_required(f):
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"message": "Token is missing"}), 403

        # Check if the token is valid
        email = decode_token(token)
        if not email:
            return jsonify({"message": "Invalid or expired token"}), 401

        # Add the email to the request context to be used in the route
        request.user_email = email
        return f(*args, **kwargs)
    return wrapper

@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    
    # Extract values from request
    email = data.get("email")
    instagram_id = data.get("instagram_id")  
    password = data.get("password")

    if not email or not instagram_id or not password:
        return jsonify({"message": "All fields are required"}), 400

    existing_user = users_collection.find_one({"email_1": email})
    if existing_user:
        return jsonify({"message": "User already exists"}), 400

    hashed_password = generate_password_hash(password)

    # Create new user record
    new_user = {
        "email_1": email,  # Matching with your structure
        "instagram_id_1": instagram_id,  # Matching with your structure
        "password_text": hashed_password,
    }

    try:
        result = users_collection.insert_one(new_user)
        print(result)
    except Exception as e:
        return jsonify({"message": f"Error saving user: {e}"}), 500

    return jsonify({"message": "User registered successfully"}), 201

@app.route("/signin", methods=["POST"])
def signin():
    data = request.get_json()

    # Extract values from request
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    # Fetch user from database
    try:
        user = users_collection.find_one({"email_1": email})
    except Exception as e:
        return jsonify({"message": f"Error accessing user data: {e}"}), 500

    if not user:
        return jsonify({"message": "User not found"}), 404

    # Verify password
    if not check_password_hash(user["password_text"], password):
        return jsonify({"message": "Invalid email or password"}), 401

    return jsonify({"message": "Sign-in successful"}), 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
