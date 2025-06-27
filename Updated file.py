# MAIN CHANGES INCLUDED:
# - Cached AI questions to JSON file
# - Removed duplicate load_questions_async definitions
# - Reorganized display_question call to avoid redundancy
# - OpenAI API key now loads from environment variable or .env file

import tkinter as tk
from tkinter import messagebox, PhotoImage
import math, random, json, os, webbrowser, threading
from PIL import Image, ImageTk, ImageOps
from dotenv import load_dotenv
import openai
import pygame
import os
import requests
pygame.mixer.init()

# Load environment variables from .env if available
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USE_AI_QUESTIONS = True
CHARACTER_CATEGORIES = ["JavaScript", "HTML", "Java", "C++", "SQL", "Python"]
PROGRESS_FILE = "user_progress.json"
MEDAL_ICONS = ["medal_gold.png", "medal_silver.png", "medal_bronze.png"]
angle = 0


import requests
import os

def get_ai_questions(category, num_questions=5):
    cache_file = f"ai_cache_{category.lower()}.json"
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            return json.load(f)

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    if not OPENROUTER_API_KEY:
        print("❌ Missing OpenRouter API key. Set OPENROUTER_API_KEY in your .env file.")
        return []

    prompt = f"""
    Generate {num_questions} multiple-choice trivia questions about {category}.
    Each question should include:
    - 'question' (string)
    - 'options' (list of 4 strings)
    - 'correct' (one of the options)

    Respond in JSON list format:
    [
      {{
        "question": "...",
        "options": ["A", "B", "C", "D"],
        "correct": "B"
      }},
      ...
    ]
    """

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "http://localhost",  # Required even for local dev
                "Content-Type": "application/json"
            },
            json={
                "model": "mistralai/mistral-7b-instruct",  # or another free model
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
        )

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)

        with open(cache_file, "w") as f:
            json.dump(parsed, f, indent=2)

        return parsed

    except Exception as e:
        print("❌ Error fetching AI questions:", e)
        return []


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}  # Return empty if file is invalid
    return {}

def save_progress(data):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_user_progress(username):
    data = load_progress()
    return data.get(username, {"correct_count": 0, "total_correct": 0, "characters": []})

def update_user_progress(username, correct=False, reset=False):
    data = load_progress()
    user = data.get(username, {"correct_count": 0, "characters": [], "total_correct": 0})

    # Ensure all fields exist
    user.setdefault("correct_count", 0)
    user.setdefault("characters", [])
    user.setdefault("total_correct", 0)

    if reset:
        user["correct_count"] = 0
    elif correct:
        user["correct_count"] += 1
        user["total_correct"] += 1  # Track all-time correct answers

    data[username] = user
    save_progress(data)
    return user

def award_character(username, category):
    data = load_progress()
    user = data.get(username, {"correct_count": 0, "characters": [], "total_correct": 0})

    # Ensure fields are initialized
    user.setdefault("correct_count", 0)
    user.setdefault("characters", [])
    user.setdefault("total_correct", 0)

    if category not in user["characters"]:
        user["characters"].append(category)
        user["correct_count"] = 0  # Reset progress bar
        user["total_correct"] = 0  # Reset total score after earning a character

    data[username] = user
    save_progress(data)

def has_all_characters(username):
    progress = get_user_progress(username)
    return all(cat in progress["characters"] for cat in CHARACTER_CATEGORIES)


def fade_out(window, callback=None, step=0.05):
    alpha = window.attributes('-alpha')
    if alpha > 0:
        window.attributes('-alpha', alpha - step)
        window.after(10, lambda: fade_out(window, callback, step))
    else:
        if callback:
            callback()

def fade_in(window, step=0.05):
    alpha = window.attributes('-alpha')
    if alpha < 1:
        window.attributes('-alpha', alpha + step)
        window.after(10, lambda: fade_in(window, step))


class SpinningWheel(tk.Canvas):
    def __init__(self, master, categories, icons, command, initial_angle=0, **kwargs):
        self.angle = initial_angle  # Set the angle before drawing
        # Remove 'initial_angle' from kwargs if it somehow got in (defensive)
        if 'initial_angle' in kwargs:
            del kwargs['initial_angle']
        super().__init__(master, width=300, height=300, bg="white", highlightthickness=0, **kwargs)

        self.categories = categories
        self.command = command
        self.icons = icons        
        self.is_spinning = False
        self.segments = len(categories)
        self.segment_colors = ["#ff9999", "#99ccff", "#99ff99", "#ffcc99", "#ccccff", "#ffff99"]
        self.bind("<Button-1>", self.spin)
        self.spin_job = None
        self.tick_sound = pygame.mixer.Sound("tick.wav")
        self.ding_sound = pygame.mixer.Sound("ding.wav")
        self.timer_job = None

        self.draw_wheel_rotated(self.angle)



        
    def spin(self, event=None):
        if self.is_spinning:
            return
        self.is_spinning = True
        self.spin_velocity = random.uniform(25, 35)
        self.friction = 0.935
        self.min_velocity = 0.1

        self.tick_sound.play()  # Only once
        self.spin_job = self.after(20, self.animate_spin)

    def animate_spin(self):
        if not self.winfo_exists():
            return

        if self.spin_velocity > self.min_velocity:
            self.angle += self.spin_velocity
            self.angle %= 360
            self.draw_wheel_rotated(self.angle)
            self.spin_velocity *= self.friction

            self.spin_job = self.after(60, self.animate_spin)
        else:
            self.is_spinning = False
            global angle
            angle = self.angle            
            final_angle = self.angle % 360
            adjusted_angle = (final_angle + 90) % 360
            segment_angle = 360 / self.segments
            selected_index = int(adjusted_angle // segment_angle) % self.segments
            selected_category = self.categories[selected_index]
            selected_icon = self.icons[selected_index]

            self.ding_sound.play()
            self.show_selected_category_flip(selected_category, selected_icon)

    def cancel_spin_animation(self):
        if self.spin_job:
            try:
                self.after_cancel(self.spin_job)
            except:
                pass
            self.spin_job = None


    def draw_wheel_rotated(self, angle_offset):
        self.delete("all")
        center_x, center_y = 150, 150

        # Load and draw the static wheel image (once)
        if not hasattr(self, 'wheel_base_img'):
            self.wheel_base_img = Image.open("wheel_3d.png").resize((280, 280))  # Slightly smaller than canvas

        self.tk_rotated = ImageTk.PhotoImage(self.wheel_base_img)
        self.create_image(center_x, center_y, image=self.tk_rotated)

 
        # Rotating arrow (shorter and thicker version)
        # Total arrow length (shaft + head)
        total_length = 60
        head_length = 16
        shaft_length = total_length - head_length  # Shaft stops where the arrowhead starts

        # Calculate main direction
        angle_rad = math.radians(angle_offset)

        # End of shaft (start of arrowhead)
        shaft_end_x = center_x + shaft_length * math.cos(angle_rad)
        shaft_end_y = center_y + shaft_length * math.sin(angle_rad)

        # Tip of arrowhead
        tip_x = center_x + total_length * math.cos(angle_rad)
        tip_y = center_y + total_length * math.sin(angle_rad)

        # Draw shaft
        self.create_line(center_x, center_y, shaft_end_x, shaft_end_y, width=8, fill="red")

        # Arrowhead base corners
        head_width = 14
        head_angle = math.atan2(head_width / 2, head_length)

        left_x = tip_x - head_length * math.cos(angle_rad - head_angle)
        left_y = tip_y - head_length * math.sin(angle_rad - head_angle)
        right_x = tip_x - head_length * math.cos(angle_rad + head_angle)
        right_y = tip_y - head_length * math.sin(angle_rad + head_angle)

        # Draw arrowhead
        self.create_polygon(
            tip_x, tip_y,
            left_x, left_y,
            right_x, right_y,
            fill="crimson", outline="black"
        )
        # Base cap (anchor at the center)
        base_radius = 6
        self.create_oval(
            center_x - base_radius, center_y - base_radius,
            center_x + base_radius, center_y + base_radius,
            fill="darkred", outline="black"
        )

    def show_selected_category_flip(self, category, icon):
        self.icon = icon
        self.flip_reveal(category, icon)

    def flip_reveal(self, category, icon, step=0):
        if not self.winfo_exists():
            return

        self.delete("all")
        self.create_text(150, 60, text="You got:", font=("Helvetica", 16, "bold"), fill="#333")

        # Bounce scale from 0.6 to 1.2 and settle
        bounce_factor = 1.0 + 0.2 * math.sin(step * math.pi / 6)
        scale_x = max(0.1, bounce_factor)
        width = int(icon.width() * scale_x)
        if width < 1:
            width = 1

        try:
            ratio = max(1, icon.width() // width)
            self.resized_icon = icon.subsample(ratio, 1)
        except Exception:
            self.resized_icon = icon

        self.icon_id = self.create_image(150, 150, image=self.resized_icon)
        self.create_text(150, 240, text=category, font=("Helvetica", 18, "bold"), fill="#111")

        if step == 12:
            self.after(800, lambda: self.command(category))
            return

        self.after(40, lambda: self.flip_reveal(category, icon, step + 1))
  

class CategorySelectApp:
    def __init__(self, master, character_challenge=False, username=None):
        self.master = master
        self.master.title("Coding Quiz")
        self.master.configure(bg="#f0f4f8")
        self.master.geometry("360x640")

        self.top_bar = tk.Frame(master, bg="#ddd", height=30)
        self.top_bar.pack(fill="x")
        tk.Label(self.top_bar, text="📶", bg="#ddd", font=("Helvetica", 12)).pack(side="right")
        tk.Label(self.top_bar, text="🔋", bg="#ddd", font=("Helvetica", 12)).pack(side="right", padx=10)

        tk.Label(master, text="Welcome to the Coding Quiz!", font=("Helvetica", 18, "bold"), bg="#f0f4f8", fg="#333").pack(pady=10)
        tk.Label(master, text="Enter your name:", font=("Helvetica", 12), bg="#f0f4f8", fg="#333").pack()
        self.name_entry = tk.Entry(master, font=("Helvetica", 12))
        self.name_entry.pack(pady=5)
        

        if os.path.exists("user.json"):
            with open("user.json", "r") as f:
                data = json.load(f)
                self.name_entry.insert(0, data.get("username", ""))
                
        # Load and show user's total score if name exists
        # self.score_label = tk.Label(master, text="", font=("Helvetica", 12), bg="#f0f4f8", fg="#333")
        # self.score_label.pack(pady=2)

        # def update_score_display():
        #     name = self.name_entry.get().strip()
        #     if name:
        #         progress = get_user_progress(name)
        #         self.score_label.config(text=f"Total Correct Answers: {progress.get('total_correct', 0)}")

        # self.name_entry.bind("<FocusOut>", lambda e: update_score_display())
        # self.name_entry.bind("<KeyRelease>", lambda e: update_score_display())

        # update_score_display()

        
                
        # Progress Bar Display
        self.bar_frame = tk.Frame(master, bg="#f0f4f8")
        self.bar_frame.pack(pady=5)

        self.bars = []
        for i in range(3):
            bar = tk.Canvas(self.bar_frame, width=40, height=10, bg="#ccc", highlightthickness=0)
            bar.pack(side="left", padx=5)
            self.bars.append(bar)
            
        
            
        def refresh_bars(self):
            update_progress_bars()

        def update_progress_bars():
            if os.path.exists("user.json"):
                with open("user.json", "r") as f:
                    data = json.load(f)
                    name = data.get("username", "").strip()
            else:
                name = self.name_entry.get().strip()

            if name:
                progress = get_user_progress(name)
                correct = progress.get("correct_count", 0)
                for i, bar in enumerate(self.bars):
                    if i < correct:
                        bar.config(bg="#4CAF50")  # filled bar
                    else:
                        bar.config(bg="#ccc")     # empty bar
            else:
                for bar in self.bars:
                    bar.config(bg="#ccc")  # clear if no name
        


        self.name_entry.bind("<FocusOut>", lambda e: update_progress_bars())
        self.name_entry.bind("<KeyRelease>", lambda e: update_progress_bars())

        # Immediately show bars if name is loaded
        update_progress_bars()
        
        # Character Collection Display with Icons
        tk.Label(master, text="Collected Characters:", font=("Helvetica", 12), bg="#f0f4f8", fg="#333").pack(pady=5)

        self.character_frame = tk.Frame(master, bg="#f0f4f8")
        self.character_frame.pack(pady=5)

        self.character_icons = {}
        self.character_labels = {}

        self.character_icons = {}
        self.character_labels = {}

        for cat in CHARACTER_CATEGORIES:
            icon_path = f"character_icon_{cat.lower()}.png"

            try:
                original_img = Image.open(icon_path).convert("RGBA").resize((40, 40), Image.Resampling.LANCZOS
)

                # Create color version
                icon = ImageTk.PhotoImage(original_img)

                # Convert to grayscale, then back to RGBA
                grayscale = ImageOps.grayscale(original_img.convert("RGB"))
                grayscale_img = Image.merge("RGBA", (grayscale, grayscale, grayscale, original_img.getchannel("A")))
                dark_icon = ImageTk.PhotoImage(grayscale_img)

            except Exception as e:
                print(f"Failed to load icon for {cat}: {e}")
                icon = None
                dark_icon = None

            label = tk.Label(self.character_frame, image=dark_icon, bg="#ddd", bd=2, relief="ridge", width=40, height=40)
            label.image_normal = icon
            label.image_dark = dark_icon
            label.config(image=dark_icon)
            label.pack(side="left", padx=4)
            self.character_labels[cat] = label           
        
        def flash_character_border(label, flashes=4, current=0):
            colors = ["#4CAF50", "#FFD700"]  # green & gold alternation
            if current >= flashes:
                label.config(bg="#f0f4f8")  # back to normal background
                return
            label.config(bg=colors[current % len(colors)])
            label.after(200, lambda: flash_character_border(label, flashes, current + 1))
            
        def bounce_icon(label, steps=4, scale_up=True):
            size = 40
            scale = 1.2 if scale_up else 1.0
            label.config(width=int(size * scale), height=int(size * scale))
            if steps == 0:
                label.config(width=size, height=size)
            else:
                label.after(100, lambda: bounce_icon(label, steps - 1, not scale_up))                
                
        def update_characters():
            name = self.name_entry.get().strip()
            if not name:
                return

            progress = get_user_progress(name)
            unlocked = progress.get("characters", [])

            for cat, label in self.character_labels.items():
                if cat in unlocked:
                    label.config(image=label.image_normal)
                else:
                    label.config(image=label.image_dark)
                    
            # Inside update_characters()
            if cat in unlocked:
                label.config(image=label.image_normal)
                flash_character_border(label)
                
            if cat in unlocked:
                label.config(image=label.image_normal)
                bounce_icon(label)



                        
        update_characters()
        
        self.name_entry.bind("<FocusOut>", lambda e: update_characters())
        self.name_entry.bind("<KeyRelease>", lambda e: update_characters())
                   
        
        tk.Label(master, text="Spin the wheel to choose a category:", font=("Helvetica", 14), bg="#f0f4f8", fg="#333").pack(pady=10)

        self.categories = ["JavaScript", "HTML", "Java", "C++", "SQL", "Python"]


        def load_icon(path):
            return PhotoImage(file=path).subsample(16, 16)

        self.icons = [
            load_icon("category_icon_js.png"),         # JavaScript
            load_icon("category_icon_html.png"),       # HTML
            load_icon("category_icon_java.png"),       # Java
            load_icon("category_icon_cpp.png"),        # C++
            load_icon("category_icon_sql.png"),        # SQL
            load_icon("category_icon_python.png"),     # Python
        ]

        if character_challenge and username:
            self.wheel = None
            tk.Label(master, text="Choose a category for your character!", font=("Helvetica", 12), bg="#f0f4f8", fg="#222").pack(pady=10)
            for i, category in enumerate(self.categories):
                tk.Button(master, text=category, font=("Helvetica", 12), width=20,
                        command=lambda c=category: self.start_character_quiz(c, username)).pack(pady=5)
        else:
            global angle
            self.wheel = SpinningWheel(master, self.categories, self.icons, self.start_quiz, initial_angle=angle)

            self.wheel.pack(pady=10)

        if self.wheel:
            self.wheel.pack(pady=1)

        self.leaderboard_button = tk.Button(master, text="📊 View Leaderboard", font=("Helvetica", 12),
                                    bg="#4CAF50", fg="white", command=self.show_leaderboard)
        self.leaderboard_button.pack(pady=10)
        
    def show_leaderboard(self):
        if not os.path.exists("scores.json"):
            messagebox.showinfo("Leaderboard", "No scores recorded yet.")
            return

        with open("scores.json", "r") as f:
            raw_scores = json.load(f)

        # Aggregate scores by username
        aggregated = {}
        for entry in raw_scores:
            user = entry["username"]
            aggregated[user] = aggregated.get(user, 0) + entry["score"]  # 1 point per correct answer

        # Load progress to show character badges
        all_progress = load_progress()

        leaderboard = sorted(aggregated.items(), key=lambda x: x[1], reverse=True)

        leaderboard_win = tk.Toplevel(self.master)
        leaderboard_win.title("\U0001F3C6 Leaderboard")
        leaderboard_win.geometry("400x500")
        leaderboard_win.configure(bg="#f0f4f8")

        tk.Label(leaderboard_win, text="Top Players", font=("Helvetica", 16, "bold"), bg="#f0f4f8").pack(pady=10)

        frame = tk.Frame(leaderboard_win, bg="#f0f4f8")
        frame.pack(pady=5, fill="both", expand=True)

        canvas = tk.Canvas(frame, bg="#f0f4f8", highlightthickness=0)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f0f4f8")

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for i, (user, total_score) in enumerate(leaderboard):
            progress = all_progress.get(user, {})
            characters = progress.get("characters", [])

            row = tk.Frame(scrollable_frame, bg="#f0f4f8")
            row.pack(anchor="w", padx=10, pady=4, fill="x")

            if i < 3 and os.path.exists(MEDAL_ICONS[i]):
                try:
                    medal_img = Image.open(MEDAL_ICONS[i]).resize((20, 20), Image.Resampling.LANCZOS)
                    medal_icon = ImageTk.PhotoImage(medal_img)
                    medal_label = tk.Label(row, image=medal_icon, bg="#f0f4f8")
                    medal_label.image = medal_icon
                    medal_label.pack(side="left", padx=(0, 5))
                except Exception as e:
                    print(f"Error loading medal icon: {e}")

            name_label = tk.Label(row, text=f"{user}: {total_score} pts", font=("Helvetica", 11), bg="#f0f4f8", anchor="w")
            name_label.pack(side="left")

            icon_frame = tk.Frame(row, bg="#f0f4f8")
            icon_frame.pack(side="right")

            for char in characters:
                icon_path = f"character_icon_{char.lower()}.png"
                if os.path.exists(icon_path):
                    try:
                        img = Image.open(icon_path).resize((20, 20), Image.Resampling.LANCZOS)
                        icon = ImageTk.PhotoImage(img)
                        lbl = tk.Label(icon_frame, image=icon, bg="#f0f4f8")
                        lbl.image = icon  # prevent garbage collection
                        lbl.pack(side="left", padx=1)
                    except Exception as e:
                        print(f"Error loading icon for {char}: {e}")

    def start_character_quiz(self, category, username):
        fade_out(self.master, lambda: self.launch_character_quiz(username, category))

    def launch_character_quiz(self, username, category):
        self.master.destroy()
        root = tk.Tk()
        root.attributes('-alpha', 0.0)
        CharacterChallengeQuiz(root, username=username, category=category)
        fade_in(root)
        root.mainloop()


    def start_quiz(self, category):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Missing Info", "Please enter your name.")
            return

        with open("user.json", "w") as f:
            json.dump({"username": name}, f)
        
        self.wheel.cancel_spin_animation()

        fade_out(self.master, lambda: self.launch_quiz(name, category))

    def launch_quiz(self, name, category):
        self.master.destroy()
        root = tk.Tk()
        root.attributes('-alpha', 0.0)
        TriviaQuizApp(root, username=name, category=category)
        fade_in(root)
        root.mainloop()
        
    #def show_leaderboard(self):
     #   if not os.path.exists("scores.json"):
      #      messagebox.showinfo("Leaderboard", "No scores recorded yet.")
       #     return

        #with open("scores.json", "r") as f:
         #   scores = json.load(f)

        #leaderboard = sorted(scores, key=lambda x: x["score"], reverse=True)[:20]
        #message = "\n".join([f"{s['username']} - {s['category']}: {s['score']}/{s['total']}" for s in leaderboard])
        #messagebox.showinfo("Top Scores", message or "No scores yet!")

class SelectNextCategoryScreen:
    def __init__(self, master, username, original_category, questions, q_index, score):
        self.master = master
        self.username = username
        self.questions = questions
        self.q_index = q_index
        self.score = score
        self.master.title("Spin Again!")
        self.master.configure(bg="#f0f4f8")
        self.master.geometry("360x640")

        tk.Label(master, text="🎉 Spin again for the next question!", font=("Helvetica", 16, "bold"),
                 bg="#f0f4f8", fg="#333").pack(pady=20)

        categories = ["JavaScript", "HTML", "Java", "C++", "SQL", "Python"]

        def load_icon(path):
            return PhotoImage(file=path).subsample(16, 16)

        icons = [
            load_icon("category_icon_js.png"),
            load_icon("category_icon_html.png"),
            load_icon("category_icon_java.png"),
            load_icon("category_icon_cpp.png"),
            load_icon("category_icon_sql.png"),
            load_icon("category_icon_python.png"),
        ]

        global angle
        self.wheel = SpinningWheel(master, categories, icons, self.launch_next_question, initial_angle=angle)

        self.wheel.pack(pady=10)

    def launch_next_question(self, category):
        self.master.destroy()
        root = tk.Tk()
        app = TriviaQuizApp(root, self.username, category)
        app.questions = self.questions
        app.q_index = self.q_index
        app.score = self.score
        app.display_question()
        root.mainloop()


class TriviaQuizApp:
    def __init__(self, master, username, category):
        self.master = master
        self.username = username
        self.category = category
        self.master.title("Trivia Quiz")
        self.master.geometry("360x640")
        self.master.configure(bg="#f0f4f8")
        self.master.resizable(False, False)

        # Set up UI elements FIRST
        self.header = tk.Label(master, text=f"🎯 {category.capitalize()} Trivia",
                            font=("Helvetica", 16, "bold"), bg="#f0f4f8", fg="#333", wraplength=320, justify="center")
        self.header.pack(pady=10)

        self.status = tk.Label(master, text="", font=("Helvetica", 10),
                            bg="#f0f4f8", fg="#666")
        self.status.pack(pady=5)

        self.question_label = tk.Label(master, text="", font=("Helvetica", 14),
                                    wraplength=320, bg="#f0f4f8", fg="#222", justify="center")
        self.question_label.pack(pady=10)

        self.buttons_frame = tk.Frame(master, bg="#f0f4f8")
        self.buttons_frame.pack(pady=10)

        self.answer_buttons = []
        for i in range(4):
            btn = tk.Button(self.buttons_frame, text="", font=("Helvetica", 12),
                            bg="#ffffff", fg="#333", width=30, wraplength=280, justify="left", anchor="w",
                            command=lambda b=i: self.submit_answer(b))
            btn.pack(pady=5)
            self.answer_buttons.append(btn)

        self.time_remaining = 20
        self.timer_label = tk.Label(self.master, text=f"⏰ Time left: {self.time_remaining}s", font=("Helvetica", 10),
                                    bg="#f0f4f8", fg="#d32f2f")
        self.timer_label.pack(pady=2)
        self.update_timer()
        
        if USE_AI_QUESTIONS:
            self.questions = []
            self.header.config(text=f"Loading {category} questions!")

            def load_questions_async():
                questions = get_ai_questions(category)
                if not questions:
                    messagebox.showerror("Error", "Failed to load questions from AI.")
                    self.master.destroy()
                    return
                self.questions = questions
                self.q_index = 0
                self.score = 0
                self.master.after(0, self.display_question)  # Use .after() to run in main thread

            threading.Thread(target=load_questions_async).start()
            return
        else:
            with open("questions.json", "r") as f:
                all_questions = json.load(f)
            self.questions = [q for q in all_questions if q['topic'].lower() == category.lower()]
            random.shuffle(self.questions)
            self.q_index = 0
            self.score = 0
            self.display_question()


    def update_timer(self):
        if self.time_remaining > 0:
            self.time_remaining -= 1
            self.timer_label.config(text=f"⏰ Time left: {self.time_remaining}s")
            self.timer_job = self.master.after(1000, self.update_timer)
        else:
            self.timer_label.config(text="⏰ Time's up!")
            self.handle_incorrect()

    def display_question(self):
        self.current_question = self.questions[self.q_index]
        self.question_label.config(text=f"❓ {self.current_question['question']}")
        self.status.config(text=f"{self.username} | Q{self.q_index + 1}/{len(self.questions)} | Score: {self.score}")

        options = self.current_question["options"].copy()
        random.shuffle(options)
        self.correct_answer = self.current_question["correct"].strip().lower()

        for i, opt in enumerate(options):
            self.answer_buttons[i].config(text=opt, state="normal", bg="#ffffff")

    def submit_answer(self, index):
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None

        selected = self.answer_buttons[index].cget("text").strip().lower()
        if selected == self.correct_answer:
            self.score += 1
            update_user_progress(self.username, correct=True)  # Track progress

            progress = get_user_progress(self.username)
            if progress["correct_count"] >= 3:
                self.start_character_challenge()
            else:
                messagebox.showinfo("Correct!", "✅ Nice job! Spin again to continue.")
                self.master.destroy()
                # Re-launch spin screen but keep question index & score
                root = tk.Tk()
                app = CategorySelectApp(root)
                root.mainloop()

                root.mainloop()

        else:
            self.handle_incorrect()
        
    def start_character_challenge(self):
        update_user_progress(self.username, reset=True)
        messagebox.showinfo("Character Challenge!", "You earned a special challenge! Choose your category.")

        # Go to the wheel but allow custom category selection for character challenge
        self.master.destroy()
        new_root = tk.Tk()
        app = CategorySelectApp(new_root, character_challenge=True, username=self.username)
        new_root.mainloop()


    def next_question(self):
        self.q_index += 1
        if self.q_index >= len(self.questions):
            self.save_score()
            if self.timer_job:
                self.master.after_cancel(self.timer_job)
                self.timer_job = None
            messagebox.showinfo("Quiz Complete", f"{self.username}, you scored {self.score}/{len(self.questions)}.")
            self.master.destroy()
        else:
            self.display_question()

    def handle_incorrect(self):
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None
        for btn in self.answer_buttons:
            btn.config(state="disabled")
        retry = messagebox.askyesno("Wrong Answer!", "Oops! That's incorrect.\nWatch an ad to continue?")
        if retry:
            self.show_video_ad()
        else:
            self.save_score()
            messagebox.showinfo("Thanks for playing!", f"Your final score: {self.score}")
            self.master.destroy()
            new_root = tk.Tk()
            app = CategorySelectApp(new_root)
            new_root.mainloop()

    def show_video_ad(self):
        for widget in self.master.winfo_children():
            widget.destroy()

        self.header = tk.Label(self.master, text="📺 Watch This Ad to Continue",
                            font=("Helvetica", 16, "bold"), bg="#f0f4f8", fg="#333")
        self.header.pack(pady=10)

        info = tk.Label(self.master, text="The ad will open in your browser.",
                        font=("Helvetica", 12), bg="#f0f4f8", fg="#555")
        info.pack(pady=5)

        self.countdown_label = tk.Label(self.master, text="⏳ You can skip in 5 seconds",
                                        font=("Helvetica", 10), bg="#f0f4f8", fg="#777")
        self.countdown_label.pack(pady=5)

        webbrowser.open("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        self.button_frame = tk.Frame(self.master, bg="#f0f4f8")
        self.button_frame.pack(pady=20)

        self.skip_btn = tk.Button(self.button_frame, text="⏩ Skip Ad",
                                font=("Helvetica", 12), bg="#f44336", fg="white",
                                command=self.rebuild_quiz_ui)
        self.skip_btn.pack_forget()

        self.countdown_seconds = 5
        self.update_countdown()

    def update_countdown(self):
        if self.countdown_seconds > 0:
            self.countdown_label.config(
                text=f"⏳ You can skip in {self.countdown_seconds} second{'s' if self.countdown_seconds > 1 else ''}")
            self.countdown_seconds -= 1
            self.master.after(1000, self.update_countdown)
        else:
            self.countdown_label.config(text="✅ You can now skip the ad.")
            self.skip_btn.pack(pady=10)

    def rebuild_quiz_ui(self):
        for widget in self.master.winfo_children():
            widget.destroy()

        self.__init__(self.master, self.username, self.category)

    def save_score(self):
        score_data = {
            "username": self.username,
            "category": self.category,
            "score": self.score,
            "total": len(self.questions)
        }

        scores_file = "scores.json"
        if os.path.exists(scores_file):
            try:
                with open(scores_file, "r") as f:
                    all_scores = json.load(f)
                if not isinstance(all_scores, list):
                    all_scores = []
            except json.JSONDecodeError:
                all_scores = []
        else:
            all_scores = []

        all_scores.append(score_data)

        with open(scores_file, "w") as f:
            json.dump(all_scores, f, indent=2)
            
class CharacterChallengeQuiz:
    def __init__(self, master, username, category):
        self.master = master
        self.username = username
        self.category = category
        self.master.title("Character Challenge")
        self.master.geometry("360x640")
        self.master.configure(bg="#f0f4f8")
        self.master.resizable(False, False)

        self.header = tk.Label(master, text=f"🎯 {category} Character Challenge!",
                               font=("Helvetica", 16, "bold"), bg="#f0f4f8", fg="#333", wraplength=320, justify="center")
        self.header.pack(pady=10)

        self.question_label = tk.Label(master, text="", font=("Helvetica", 14),
                                       wraplength=320, bg="#f0f4f8", fg="#222", justify="center")
        self.question_label.pack(pady=10)

        self.buttons_frame = tk.Frame(master, bg="#f0f4f8")
        self.buttons_frame.pack(pady=10)

        self.answer_buttons = []
        for i in range(4):
            btn = tk.Button(self.buttons_frame, text="", font=("Helvetica", 12),
                            bg="#ffffff", fg="#333", width=30, wraplength=280, justify="left", anchor="w",
                            command=lambda b=i: self.submit_answer(b))
            btn.pack(pady=5)
            self.answer_buttons.append(btn)

        self.time_remaining = 20
        self.timer_label = tk.Label(master, text=f"⏰ Time left: {self.time_remaining}s", font=("Helvetica", 10),
                                    bg="#f0f4f8", fg="#d32f2f")
        self.timer_label.pack(pady=2)
        
        self.timer_running = False  # Prevent timer from starting early
        self.correct_answer = None  # Initialize to avoid attribute error

        if USE_AI_QUESTIONS:
            self.questions = []
            self.header.config(text=f"Loading {category} challenge question!")

            def load_questions_async():
                questions = get_ai_questions(category, num_questions=1)
                if not questions:
                    messagebox.showerror("Error", "Failed to load challenge question from AI.")
                    self.master.destroy()
                    return
                self.questions = questions
                self.q_index = 0
                self.score = 0
                self.master.after(0, self.display_question)  # Safe UI call

            threading.Thread(target=load_questions_async).start()
            return
        else:
            with open("questions.json", "r") as f:
                all_questions = json.load(f)
            self.questions = [q for q in all_questions if q['topic'].lower() == category.lower()]
            self.q_index = 0
            self.score = 0
            self.display_question()

        self.update_timer()

    def display_question(self):
        self.current_question = self.questions[self.q_index]
        self.question_label.config(text=f"❓ {self.current_question['question']}")

        options = self.current_question['options']
        random.shuffle(options)

        for i, option in enumerate(options):
            self.answer_buttons[i].config(text=option)

        self.correct_answer = self.current_question['correct'].strip().lower()
        self.time_remaining = 20
        self.timer_label.config(text=f"⏰ Time left: {self.time_remaining}s")

        if not self.timer_running:
            self.timer_running = True
            self.countdown()

    def countdown(self):
        if self.time_remaining > 0:
            self.timer_label.config(text=f"⏰ Time left: {self.time_remaining}s")
            self.time_remaining -= 1
            self.master.after(1000, self.countdown)
        else:
            messagebox.showinfo("Time's up!", "You ran out of time. Try again later.")
            self.master.destroy()
            root = tk.Tk()
            app = CategorySelectApp(root)
            root.mainloop()

    
    def update_timer(self):
        if self.time_remaining > 0:
            self.time_remaining -= 1
            self.timer_label.config(text=f"⏰ Time left: {self.time_remaining}s")
            self.timer_job = self.master.after(1000, self.update_timer)
        else:
            self.timer_label.config(text="⏰ Time's up!")
            self.handle_incorrect()



    def display_question(self):
        self.current_question = self.questions[self.q_index]
        self.question_label.config(text=f"❓ {self.current_question['question']}")
        self.status.config(text=f"{self.username} | Q{self.q_index + 1}/{len(self.questions)} | Score: {self.score}")

        options = self.current_question["options"].copy()
        random.shuffle(options)
        self.correct_answer = self.current_question["correct"].strip().lower()

        for i, opt in enumerate(options):
            self.answer_buttons[i].config(text=opt, state="normal", bg="#ffffff")

    def submit_answer(self, index):
        selected = self.answer_buttons[index].cget("text").strip().lower()
        correct = selected == self.correct_answer

        if correct:
            award_character(self.username, self.category)
            if has_all_characters(self.username):
                messagebox.showinfo("🏆 Victory!", "You've collected all 6 characters! You win!")
            else:
                messagebox.showinfo("🎉 Character Earned!", f"You earned the {self.category} character!")
        else:
            messagebox.showinfo("Wrong!", "You missed the character challenge. Try again later.")

        # Regardless of result, return to main screen
        self.master.destroy()
        root = tk.Tk()
        app = CategorySelectApp(root)
        root.mainloop()


        
    def start_character_challenge(self):
        update_user_progress(self.username, reset=True)
        messagebox.showinfo("Character Challenge!", "You earned a special challenge! Choose your category.")

        # Go to the wheel but allow custom category selection for character challenge
        self.master.destroy()
        new_root = tk.Tk()
        app = CategorySelectApp(new_root, character_challenge=True, username=self.username)
        new_root.mainloop()


    def next_question(self):
        self.q_index += 1
        if self.q_index >= len(self.questions):
            self.save_score()
            if self.timer_job:
                self.master.after_cancel(self.timer_job)
                self.timer_job = None
            messagebox.showinfo("Quiz Complete", f"{self.username}, you scored {self.score}/{len(self.questions)}.")
            self.master.destroy()
        else:
            self.display_question()

    def handle_incorrect(self):
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None
        for btn in self.answer_buttons:
            btn.config(state="disabled")
        retry = messagebox.askyesno("Wrong Answer!", "Oops! That's incorrect.\nWatch an ad to continue?")
        if retry:
            self.show_video_ad()
        else:
            self.save_score()
            messagebox.showinfo("Thanks for playing!", f"Your final score: {self.score}")
            self.master.destroy()
            new_root = tk.Tk()
            app = CategorySelectApp(new_root)
            new_root.mainloop()

    def show_video_ad(self):
        for widget in self.master.winfo_children():
            widget.destroy()

        self.header = tk.Label(self.master, text="📺 Watch This Ad to Continue",
                            font=("Helvetica", 16, "bold"), bg="#f0f4f8", fg="#333")
        self.header.pack(pady=10)

        info = tk.Label(self.master, text="The ad will open in your browser.",
                        font=("Helvetica", 12), bg="#f0f4f8", fg="#555")
        info.pack(pady=5)

        self.countdown_label = tk.Label(self.master, text="⏳ You can skip in 5 seconds",
                                        font=("Helvetica", 10), bg="#f0f4f8", fg="#777")
        self.countdown_label.pack(pady=5)

        webbrowser.open("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        self.button_frame = tk.Frame(self.master, bg="#f0f4f8")
        self.button_frame.pack(pady=20)

        self.skip_btn = tk.Button(self.button_frame, text="⏩ Skip Ad",
                                font=("Helvetica", 12), bg="#f44336", fg="white",
                                command=self.rebuild_quiz_ui)
        self.skip_btn.pack_forget()

        self.countdown_seconds = 5
        self.update_countdown()

    def update_countdown(self):
        if self.countdown_seconds > 0:
            self.countdown_label.config(
                text=f"⏳ You can skip in {self.countdown_seconds} second{'s' if self.countdown_seconds > 1 else ''}")
            self.countdown_seconds -= 1
            self.master.after(1000, self.update_countdown)
        else:
            self.countdown_label.config(text="✅ You can now skip the ad.")
            self.skip_btn.pack(pady=10)

    def rebuild_quiz_ui(self):
        for widget in self.master.winfo_children():
            widget.destroy()

        self.__init__(self.master, self.username, self.category)

    def save_score(self):
        score_data = {
            "username": self.username,
            "category": self.category,
            "score": self.score,
            "total": len(self.questions)
        }

        scores_file = "scores.json"
        if os.path.exists(scores_file):
            try:
                with open(scores_file, "r") as f:
                    all_scores = json.load(f)
                if not isinstance(all_scores, list):
                    all_scores = []
            except json.JSONDecodeError:
                all_scores = []
        else:
            all_scores = []

        all_scores.append(score_data)

        with open(scores_file, "w") as f:
            json.dump(all_scores, f, indent=2)


if __name__ == "__main__":
    root = tk.Tk()    
    root.resizable(False, False)
    app = CategorySelectApp(root)
    root.mainloop()
