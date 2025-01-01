from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
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

# JWT Configuration
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "your_secret_key")  # Use a secure key, and preferably load it from env variables
jwt = JWTManager(app)

try:
    client = MongoClient("mongodb+srv://suchetavadakkepat:6EHrFpVzLxvGzgbe@cluster0.kmlv7.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    db = client["loyalty_program"]
    users_collection = db["users"]
    posts_collection = db["posts"]
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
        "instagram_id": instagram_id,  # Matching with your structure
        "password_text": hashed_password,
    }

    try:
        result = users_collection.insert_one(new_user)
        print(result)
    except Exception as e:
        return jsonify({"message": f"Error saving user: {e}"}), 500

     # Create JWT token
    access_token = create_access_token(identity=email)
    return jsonify({"message": "User registered successfully", "access_token": access_token}), 201

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

    # Create JWT token
    access_token = create_access_token(identity=email)
    return jsonify({"access_token": access_token}), 200

@app.route("/users", methods=["GET"])
@jwt_required()  # Ensure only authenticated users can access this route
def get_users():
    try:
        # Fetch the first 10 users (or fewer if there are less than 10)
        users = users_collection.find().limit(10)

        # Convert the cursor to a list
        users_list = list(users)

        # Clean the data (optional step to remove MongoDB-specific fields like _id)
        for user in users_list:
            user["_id"] = str(user["_id"])  # Convert ObjectId to string

        return jsonify(users_list), 200
    except Exception as e:
        return jsonify({"message": f"Error retrieving users: {e}"}), 500


@app.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    # Get the current user's email from the JWT token
    current_user = get_jwt_identity()
    return jsonify({"message": f"Welcome {current_user}!"}), 200

# Add a post (admin use or initialization)
@app.route("/add_post", methods=["POST"])
def add_post():
    data = request.get_json()
    title = data.get("title")
    if not title:
        return jsonify({"message": "Title is required"}), 400

    new_post = {"title": title, "like_score": 0, "liked_by": []}
    try:
        result = posts_collection.insert_one(new_post)
    except Exception as e:
        return jsonify({"message": f"Error adding post: {e}"}), 500

    return jsonify({"message": "Post added successfully", "post_id": str(result.inserted_id)}), 201

# Toggle like for a post
@app.route("/toggle_like", methods=["POST"])
def toggle_like():
    data = request.get_json()
    post_id = data.get("post_id")
    user_email = data.get("user_email")

    if not post_id or not user_email:
        return jsonify({"message": "Post ID and User Email are required"}), 400

    try:
        post = posts_collection.find_one({"_id": post_id})
        if not post:
            return jsonify({"message": "Post not found"}), 404

        liked_by = post.get("liked_by", [])
        if user_email in liked_by:
            # Unlike the post
            liked_by.remove(user_email)
        else:
            # Like the post
            liked_by.append(user_email)

        like_score = len(liked_by)

        # Update the post in the database
        posts_collection.update_one(
            {"_id": post_id},
            {"$set": {"liked_by": liked_by, "like_score": like_score}}
        )
    except Exception as e:
        return jsonify({"message": f"Error toggling like: {e}"}), 500

    return jsonify({"like_score": like_score}), 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
