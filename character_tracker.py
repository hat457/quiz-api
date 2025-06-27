# --- Add this to the top of your script ---
import json
import os

# --- Utility to load progress ---
def load_user_progress(username):
    path = "user_progress.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
    else:
        data = {}

    if username not in data:
        data[username] = {
            "earned_characters": [],
            "correct_since_last": 0
        }

    return data

# --- Utility to save progress ---
def save_user_progress(username, progress):
    path = "user_progress.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
    else:
        data = {}

    data[username] = progress

    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# --- Called after every correct answer ---
def update_progress_on_correct(username):
    data = load_user_progress(username)
    data[username]["correct_since_last"] += 1
    save_user_progress(username, data[username])

    if data[username]["correct_since_last"] >= 3:
        return True  # Time for character challenge
    return False

# --- Called when character challenge is won ---
def award_character(username, category):
    data = load_user_progress(username)
    if category not in data[username]["earned_characters"]:
        data[username]["earned_characters"].append(category)
        data[username]["correct_since_last"] = 0
        save_user_progress(username, data[username])

# --- Optional: Check if user has won ---
def check_all_characters_earned(username, total_categories):
    data = load_user_progress(username)
    return len(data[username]["earned_characters"]) == total_categories
