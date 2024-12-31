from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(app)  

client = MongoClient("mongodb+srv://suchetavadakkepat:6EHrFpVzLxvGzgbe@cluster0.kmlv7.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

db = client["loyalty_program"]
users_collection = db["users"]

@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    
    # Extract values from request
    email = data.get("email")
    instagram_id = data.get("instagram_id")  
    password = data.get("password")

    if not email or not instagram_id or not password:
        return jsonify({"message": "All fields are required"}), 400

    existing_user = users_collection.find_one({"email_1": email})  # Checking based on email_1
    if existing_user:
        return jsonify({"message": "User already exists"}), 400

    hashed_password = generate_password_hash(password)

    # Create new user record
    new_user = {
        "email_1": email,  # Matching with your structure
        "instagram_id_1": instagram_id,  # Matching with your structure
        "password_text": hashed_password,
    }

    result = users_collection.insert_one(new_user)
    print(result)

    return jsonify({"message": "User registered successfully"}), 201

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
