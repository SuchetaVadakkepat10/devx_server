from flask import Flask, request, jsonify
from flask_cors import CORS
try:
    from pymongo import MongoClient
    from werkzeug.security import generate_password_hash, check_password_hash
except ImportError:
    raise ImportError("Required modules not found. Ensure 'pymongo' and 'werkzeug' are installed.")

from dotenv import load_dotenv
import os
load_dotenv()

app = Flask(__name__)
CORS(app)  

try:
    client = MongoClient("mongodb+srv://suchetavadakkepat:6EHrFpVzLxvGzgbe@cluster0.kmlv7.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    db = client["loyalty_program"]
    users_collection = db["users"]
except Exception as e:
    raise ConnectionError(f"Failed to connect to the database: {e}")

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
