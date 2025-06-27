# MAIN CHANGES INCLUDED:
# - Cached AI questions to JSON file
# - Removed duplicate load_questions_async definitions
# - Reorganized display_question call to avoid redundancy
# - OpenAI API key now loads from environment variable or .env file

import tkinter as tk
from tkinter import messagebox, PhotoImage
import math, random, json, os, webbrowser, threading
from PIL import Image, ImageTk, ImageOps, ImageEnhance
from dotenv import load_dotenv
import openai
import pygame
import os
import requests
pygame.mixer.init()

# Load environment variables from .env if available
load_dotenv()

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
USE_AI_QUESTIONS = True
CHARACTER_CATEGORIES = ["JavaScript", "HTML", "Java", "C++", "SQL", "Python"]
PROGRESS_FILE = "user_progress.json"
MEDAL_ICONS = ["medal_gold.png", "medal_silver.png", "medal_bronze.png"]
angle = 0
AI_MEMORY_FILE = "ai_question_memory.json"
ICON_CACHE = {}
use_image_arrow = True

CATEGORY_ICONS = {
    "Python": "icons/category_icon_python.png",
    "JavaScript": "icons/category_icon_js.png",
    "HTML": "icons/category_icon_html.png",
    "Java": "icons/category_icon_java.png",
    "C++": "icons/category_icon_cpp.png",
    "SQL": "icons/category_icon_sql.png"
}



def handle_quiz_finished(self, score):
    messagebox.showinfo("Quiz Finished", f"Great job!\nYour score was: {score}")
    self.master.destroy()  # or transition to next screen


def show_animated_banner(root, message):
    banner = tk.Label(root, text=message, bg="#4CAF50", fg="white", font=("Helvetica", 14, "bold"), padx=10, pady=5)
    banner.place(x=0, y=-50, relwidth=1)

    def slide_in(y=-50):
        if y < 0:
            y += 5
            banner.place(y=y)
            root.after(10, lambda: slide_in(y))
        else:
            banner.place(y=0)
            root.after(2000, slide_out)

    def slide_out(y=0):
        if y > -50:
            y -= 5
            banner.place(y=y)
            root.after(10, lambda: slide_out(y))
        else:
            banner.destroy()

    slide_in()



def load_ai_memory():
    if os.path.exists(AI_MEMORY_FILE):
        try:
            with open(AI_MEMORY_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_ai_memory(memory):
    with open(AI_MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

def load_questions_async(self):
        if USE_AI_QUESTIONS:
            self.questions = []

            def update_header():
                self.header.config(text=f"Loading {self.category} challenge question from AI...")

            self.master.after(0, update_header)

            ai_question_memory = load_ai_memory()
            print("[DEBUG] Loading questions from AI...")
            attempts = 0
            max_attempts = 5
            new_questions = []
            recent = ai_question_memory.get(self.category, [])

            while attempts < max_attempts:
                questions = get_ai_questions(self.category, num_questions=1)
                print("[DEBUG] AI returned:", questions)
                if questions:
                    q_text = questions[0].get("question", "").strip()
                    if q_text and q_text not in recent:
                        recent.append(q_text)
                        if len(recent) > 5:
                            recent.pop(0)
                        ai_question_memory[self.category] = recent
                        save_ai_memory(ai_question_memory)
                        new_questions = questions
                        break
                attempts += 1

            def on_success():
                print("[DEBUG] on_success triggered")
                if not new_questions:
                    print("[ERROR] No questions returned")
                else:
                    print("[DEBUG] First question:", new_questions[0])
                self.questions = new_questions
                self.q_index = 0
                self.score = 0
                self.master.after(0, self.display_question)



            def fallback_to_local():
                print("[DEBUG] Falling back to local questions...")
                try:
                    with open("questions.json", "r") as f:
                        all_questions = json.load(f)
                    print(f"[DEBUG] Loaded {len(all_questions)} questions from file")
                    self.questions = [q for q in all_questions if q['topic'].lower() == self.category.lower()]
                    print(f"[DEBUG] Filtered down to {len(self.questions)} for category: {self.category}")
                    if not self.questions:
                        raise ValueError(f"No local questions found for category: {self.category}")
                    random.shuffle(self.questions)
                    self.q_index = 0
                    self.score = 0
                    self.master.after(0, self.display_question)
                except Exception as e:
                    print(f"[ERROR] Failed to load local questions: {e}")
                    def show_error():
                        messagebox.showerror("Error", f"AI and local question loading failed:\n{e}")
                        self.master.destroy()
                    self.master.after(0, show_error)



            if new_questions:
                try:
                    self.master.after(0, on_success)
                except Exception as e:
                    print("[WARN] Could not trigger on_success in main thread:", e)

            else:
                print("[WARN] Could not get unique AI question. Falling back to local.")
                self.master.after(0, fallback_to_local)    


def get_ai_questions(category, num_questions=5):
    cache_file = f"ai_cache_{category.lower()}.json"
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            return json.load(f)

    if not TOGETHER_API_KEY:
        print("❌ Missing Together API key. Set TOGETHER_API_KEY in your .env file.")
        return fallback_questions(category, num_questions)

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
            "https://api.together.xyz/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {TOGETHER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
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
        return fallback_questions(category, num_questions)


def fallback_questions(category, num_questions=5):
    try:
        with open("questions.json", "r") as f:
            all_questions = json.load(f)
        filtered = [q for q in all_questions if q['topic'].lower() == category.lower()]
        random.shuffle(filtered)
        return filtered[:num_questions]
    except Exception as e:
        print("❌ Error loading fallback questions:", e)
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

def award_character(username, category, root=None):
    data = load_progress()
    user = data.get(username, {"correct_count": 0, "characters": [], "total_correct": 0})

    user.setdefault("correct_count", 0)
    user.setdefault("characters", [])
    user.setdefault("total_correct", 0)

    if category not in user["characters"]:
        user["characters"].append(category)
        user["correct_count"] = 0
        user["total_correct"] = 0

        # Win check
        if all(cat in user["characters"] for cat in CHARACTER_CATEGORIES):
            print("🏆 All characters unlocked!")
            if root and root.winfo_exists():
                show_animated_banner(root, f"🏆 {username}, you won the game!")
            # Let the main app handle the next steps (reset or not)

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
        arrow_img = Image.open("arrow.png").resize((40, 40))
        self.arrow_tk = ImageTk.PhotoImage(arrow_img)
        self.use_image_arrow = True

        # Load arrow image once (ideally when initializing canvas class)
        #self.arrow_img = Image.open("arrow.png")
        #self.arrow_img = self.arrow_img.resize((40, 40), Image.ANTIALIAS)  # adjust size as needed
        #self.arrow_tk = ImageTk.PhotoImage(self.arrow_img)

        # Add to canvas (on top of wheel)
        #self.arrow_image_obj = self.create_image(150, 10, image=self.arrow_tk)  # adjust (x, y)

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
            IMAGE_OFFSET = 45  # 🡐 You might need to fine-tune this visually
            adjusted_angle = (final_angle + IMAGE_OFFSET) % 360

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

        # Load and persist base wheel image (once)
        if not hasattr(self, 'wheel_base_img'):
            self.wheel_base_img = Image.open("wheel_3d.png").resize((280, 280))
        if not hasattr(self, 'tk_rotated') or angle_offset == 0:
            self.tk_rotated = ImageTk.PhotoImage(self.wheel_base_img)

        self.create_image(center_x, center_y, image=self.tk_rotated)

        # Load arrow image (once)
        if not hasattr(self, 'arrow_original_img'):
            self.arrow_original_img = Image.open("arrow.png").resize((80, 80))

        # Rotate and persist arrow image
        rotated_arrow = self.arrow_original_img.rotate(-angle_offset, resample=Image.BICUBIC, expand=True)
        self.arrow_tk = ImageTk.PhotoImage(rotated_arrow)

        # Draw arrow as part of wheel
        self.create_image(center_x, center_y, image=self.arrow_tk)



        # Optional: central cap for aesthetic
        #base_radius = 6
        #self.create_oval(
        #    center_x - base_radius, center_y - base_radius,
        #    center_x + base_radius, center_y + base_radius,
        #    fill="darkred", outline="black"
        #)



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
        ICON_CACHE.clear()  # Ensure images aren't reused from previous window

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
        print("Building CategorySelectApp UI")

        

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
        
        def load_icons_for_category(cat):
            icon_path = f"character_icon_{cat.lower()}.png"
            if cat in ICON_CACHE:
                return ICON_CACHE[cat]

            try:
                original_img = Image.open(icon_path).convert("RGBA").resize((40, 40), Image.Resampling.LANCZOS)
                icon = ImageTk.PhotoImage(original_img)

                # Create grayscale + brightened version
                grayscale = ImageOps.grayscale(original_img.convert("RGB"))
                brightened = ImageEnhance.Brightness(grayscale).enhance(1.4)
                grayscale_img = Image.merge("RGBA", (brightened, brightened, brightened, original_img.getchannel("A")))
                dark_icon = ImageTk.PhotoImage(grayscale_img)

                ICON_CACHE[cat] = {"normal": icon, "dark": dark_icon}
                return icon, dark_icon
            except Exception as e:
                print(f"Error loading icon for {cat}: {e}")
                return None, None


        ICON_CACHE.clear()  # Ensure we reload fresh images for new window

        for cat in CHARACTER_CATEGORIES:
            try:
                icon_path = f"character_icon_{cat.lower()}.png"
                original_img = Image.open(icon_path).convert("RGBA").resize((40, 40), Image.Resampling.LANCZOS)

                # Normal color icon
                icon = ImageTk.PhotoImage(original_img)

                # Grayscale version
                grayscale = ImageOps.grayscale(original_img.convert("RGB"))
                grayscale_img = Image.merge("RGBA", (grayscale, grayscale, grayscale, original_img.getchannel("A")))
                dark_icon = ImageTk.PhotoImage(grayscale_img)

                ICON_CACHE[cat] = {"normal": icon, "dark": dark_icon}

                label = tk.Label(self.character_frame, bg="#ddd", bd=2, relief="ridge", width=40, height=40)
                label.config(image=dark_icon)
                label.image = dark_icon
                label.image_normal = icon
                label.image_dark = dark_icon
                label.pack(side="left", padx=4)
                self.character_labels[cat] = label

            except Exception as e:
                print(f"Error loading icon for {cat}: {e}")

                icon = None
                dark_icon = None          
                       
                         
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
                    flash_character_border(label)
                    bounce_icon(label) 
                else:
                    label.config(image=label.image_dark)
                    
            # Inside update_characters()
                        
                                    
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

            # Show the collected characters section just like homepage
            tk.Label(master, text="Choose a category for your character!", font=("Helvetica", 14), bg="#f0f4f8", fg="#333").pack(pady=10)

            progress = get_user_progress(username)
            unlocked = progress.get("characters", [])

            for category in CHARACTER_CATEGORIES:
                btn = tk.Button(
                    master,
                    text=category,
                    font=("Helvetica", 12),
                    width=20,
                    state="disabled" if category in unlocked else "normal",
                    command=(lambda c=category: self.start_character_quiz(c, username)) if category not in unlocked else None
                )
                btn.pack(pady=5)

            return  # ✅ Exit early to avoid showing wheel


        else:
            global angle
            self.wheel = SpinningWheel(master, self.categories, self.icons, self.start_quiz, initial_angle=angle)

            self.wheel.pack(pady=10)

        #if self.wheel:
           # self.wheel.pack(pady=1)

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

    def launch_character_quiz(self, name, category):
        self.master.withdraw()  # Hides it safely

        new_window = tk.Toplevel()
        new_window.attributes('-alpha', 0.0)
        CharacterChallengeQuiz(new_window, username=name, category=category)
        fade_in(new_window)



    def start_quiz(self, category):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Missing Info", "Please enter your name.")
            return

        with open("user.json", "w") as f:
            json.dump({"username": name}, f)

        self.wheel.cancel_spin_animation()

        # 🧠 Load icon
        icon_path = CATEGORY_ICONS.get(category, "icons/default.png")
        icon_image = Image.open(icon_path).resize((48, 48))
        icon_tk = ImageTk.PhotoImage(icon_image)

        # ✅ Load questions
        try:
            with open("questions.json", "r") as f:
                all_questions = json.load(f)
            questions = [q for q in all_questions if q["topic"].lower() == category.lower()]
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load questions: {e}")
            return

        if not questions:
            messagebox.showwarning("No Questions", f"No questions found for {category}.")
            return

        # 🎬 Launch quiz
        fade_out(
            self.master,
            lambda: self.launch_quiz(name, questions, icon_tk, self.handle_quiz_finished, category)
        )
        
    def launch_quiz(self, username, questions, icon, on_finish, category):
        self.master.withdraw()  # Hide current window

        def return_to_home(score=None):
            self.master.destroy()
            new_root = tk.Tk()
            new_root.resizable(False, False)

            # ✅ Load progress and check streak
            progress = load_progress()
            user = progress.get(username, {})
            correct_streak = user.get("correct_count", 0)
            print(f"[DEBUG] User '{username}' correct streak: {correct_streak}")

            if correct_streak >= 3:
                update_user_progress(username, reset=True)
                CategorySelectApp(new_root, character_challenge=True, username=username)
            else:
                CategorySelectApp(new_root, character_challenge=False, username=username)


        new_window = tk.Toplevel()
        new_window.attributes('-alpha', 0.0)
        TriviaQuestionScreen(
            new_window, questions, category, icon, username,
            lambda score: return_to_home(score)
        )

        fade_in(new_window)


    
            
    def handle_quiz_finished(self, final_score):
        messagebox.showinfo("Quiz Complete", f"You scored {final_score} points!")
        self.master.deiconify()  # Bring back the main window after quiz

class SelectNextCategoryScreen:
    def __init__(self, master, username, original_category, questions, q_index, score):
        self.master = master
        self.username = username.strip().lower()
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
        
    def return_to_wheel(self, score=None):
        self.master.destroy()
        CategorySelectApp(tk.Toplevel(), username=self.username)


    def launch_next_question(self, selected_category, questions, selected_icon):
        self.master.withdraw()  # Hides it safely

        new_window = tk.Toplevel()
        quiz = TriviaQuestionScreen(
            new_window,
            questions,
            selected_category,
            selected_icon,
            self.username,
            lambda score: self.return_to_wheel(score)
        )
        quiz.questions = self.questions
        quiz.q_index = self.q_index
        quiz.score = self.score
        quiz.display_question()      

class TriviaQuestionScreen:
    recent_questions_memory = {}
    
    def __init__(self, master, questions, category, icon, username, on_finish):
        self.master = master
        self.questions = questions
        self.category = category
        self.icon = icon
        self.username = username.strip().lower()
        self.on_finish = on_finish
        self.q_index = 0
        self.score = 0
        self.timer_seconds = 15
        self.timer_job = None

        self.frame = tk.Frame(master, bg="#f2f6fa")
        self.frame.pack(fill="both", expand=True)

        # Category Icon at Top
        self.category_icon_tk = icon
        self.category_icon_label = tk.Label(self.frame, image=self.category_icon_tk, bg="#f2f6fa")
        self.category_icon_label.pack(pady=(10, 5))

        # Header (Username + Score)
        self.header = tk.Label(self.frame, text=f"{self.username} | Q1/{len(self.questions)} | Score: 0", font=("Helvetica", 14), bg="#f2f6fa")
        self.header.pack(pady=5)

        # Question Label (larger)
        self.question_label = tk.Label(self.frame, text="", font=("Helvetica", 16, "bold"), bg="#f2f6fa", wraplength=400, justify="center")
        self.question_label.pack(pady=(10, 20))

        # Answer Buttons
        self.answer_buttons = []
        for i in range(4):
            btn = tk.Button(self.frame, text="", font=("Helvetica", 14), width=40, command=lambda b=i: self.submit_answer(b))
            btn.pack(pady=6, padx=30, fill="x")
            self.answer_buttons.append(btn)

        # Timer
        self.timer_label = tk.Label(self.frame, text="", font=("Helvetica", 14), fg="red", bg="#f2f6fa")
        self.timer_label.pack(pady=10)

        # Banner Ad Placeholder at Bottom
        self.banner_ad = tk.Label(self.frame, text="🔸 Banner Ad Placeholder 🔸", font=("Helvetica", 12), bg="#ddd")
        self.banner_ad.pack(side="bottom", fill="x", pady=5)

        self.display_question()

    def display_question(self):
        question = self.questions[self.q_index]
        self.question_label.config(text=question['question'])

        choices = question.get('options', [])[:]
        random.shuffle(choices)

        for i, btn in enumerate(self.answer_buttons):
            btn.config(text=choices[i], state="normal")

        self.update_header()
        self.start_timer()

    def update_header(self):
        self.header.config(text=f"{self.username} | Q{self.q_index+1}/{len(self.questions)} | Score: {self.score}")

    def start_timer(self):
        self.timer_seconds = 20
        self.update_timer()   
        
    def launch_character_challenge(self, category, popup_window):
        popup_window.destroy()
        self.master.destroy()
        new_window = tk.Toplevel()
        CharacterChallengeQuiz(new_window, username=self.username, category=category)
        # Start loading questions from AI safely
        

    
    
    def update_timer(self):
        self.timer_label.config(text=f"⏰ Time left: {self.timer_seconds}s")
        if self.timer_seconds > 0:
            self.timer_seconds -= 1
            self.timer_job = self.master.after(1000, self.update_timer)
        else:
            self.submit_answer(None)  # Treat as timeout

    def submit_answer(self, selected_index):
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None

        question = self.questions[self.q_index]
        selected_text = self.answer_buttons[selected_index].cget("text") if selected_index is not None else None
        correct_text = question.get('correct') or question.get('answer')

        for btn in self.answer_buttons:
            btn.config(state="disabled")

        if selected_text == correct_text:
            self.score += 1
            self.question_label.config(text="✅ Correct!")
            user_progress = update_user_progress(self.username, correct=True)
            
            print(f"[DEBUG] User '{self.username}' correct streak: {user_progress['correct_count']}")

            # ✅ Trigger only when correct streak becomes exactly 3
            if user_progress.get("correct_count", 0) == 3:
                update_user_progress(self.username, reset=True)
                earned = load_progress().get(self.username, {}).get("characters", [])
                
                def open_character_selection():
                    popup = tk.Toplevel(self.master)
                    popup.title("Select a Character to Earn")
                    popup.geometry("320x400")
                    popup.configure(bg="#f0f4f8")

                    tk.Label(popup, text="🎯 Choose a character category:", font=("Helvetica", 14, "bold"), bg="#f0f4f8").pack(pady=10)

                    for cat in CHARACTER_CATEGORIES:
                        is_unlocked = cat in earned
                        btn = tk.Button(
                            popup,
                            text=f"{'✅ ' if is_unlocked else ''}{cat}",
                            font=("Helvetica", 12),
                            width=25,
                            state="disabled" if is_unlocked else "normal",
                            command=(lambda c=cat: self.launch_character_challenge(c, popup)) if not is_unlocked else None
                        )
                        btn.pack(pady=6)

                self.master.after(1000, open_character_selection)
                return

            self.master.after(1500, self.end_quiz)

        else:
            self.question_label.config(text=f"❌ Incorrect!\nCorrect answer: {correct_text}")
            update_user_progress(self.username, correct=False)  # 👈 Reset streak
            self.master.after(1500, self.end_quiz)


    def end_quiz(self):
        self.master.destroy()
        self.on_finish(self.score)  # Will re-show the homepage


    def next_question(self):
        self.q_index += 1
        if self.q_index >= len(self.questions):
            self.end_quiz()
        else:
            self.display_question()

            
class CharacterChallengeQuiz:
    recent_questions_memory = {}

    def __init__(self, master, username, category):
        self.master = master
        self.username = username.strip().lower()
        self.category = category.strip().lower()
        self.master.title("Character Challenge")
        self.master.geometry("360x640")
        self.master.configure(bg="#f0f4f8")
        self.master.resizable(False, False)
        self.master.after(100, lambda: self.master.after(0, self.start_question_thread))

        title_case = self.category.capitalize()       

        self.header = tk.Label(master, text=f"🎯 {category} Character Challenge!",
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
        self.question_label.config(text=f"Loading {self.category} challenge question from AI...")

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

        self.timer_running = False
        self.correct_answer = None
        self.timer_job = None       
        
    def load_questions_async(self):
        if USE_AI_QUESTIONS:
            self.questions = []

            def update_header_safe():
                try:
                    self.header.config(text=f"Loading {self.category} challenge question from AI...")
                except Exception as e:
                    print("[WARN] Could not update header label:", e)

            self.master.after(0, update_header_safe)


            ai_question_memory = load_ai_memory()
            print("[DEBUG] Loading questions from AI...")
            attempts = 0
            max_attempts = 5
            new_questions = []
            recent = ai_question_memory.get(self.category, [])

            while attempts < max_attempts:
                questions = get_ai_questions(self.category, num_questions=1)
                print("[DEBUG] AI returned:", questions)
                if questions:
                    q_text = questions[0].get("question", "").strip()
                    if q_text and q_text not in recent:
                        recent.append(q_text)
                        if len(recent) > 5:
                            recent.pop(0)
                        ai_question_memory[self.category] = recent
                        save_ai_memory(ai_question_memory)
                        new_questions = questions
                        break
                attempts += 1

            def on_success():
                print("[DEBUG] on_success triggered")
                if not new_questions:
                    print("[ERROR] No questions returned")
                else:
                    print("[DEBUG] First question:", new_questions[0])
                self.questions = new_questions
                self.q_index = 0
                self.score = 0
                self.master.after(0, self.display_question)



            def fallback_to_local():
                print("[DEBUG] Falling back to local questions...")
                try:
                    with open("questions.json", "r") as f:
                        all_questions = json.load(f)
                    print(f"[DEBUG] Loaded {len(all_questions)} questions from file")
                    self.questions = [q for q in all_questions if q['topic'].lower() == self.category.lower()]
                    print(f"[DEBUG] Filtered down to {len(self.questions)} for category: {self.category}")
                    if not self.questions:
                        raise ValueError(f"No local questions found for category: {self.category}")
                    random.shuffle(self.questions)
                    self.q_index = 0
                    self.score = 0
                    self.master.after(0, self.display_question)
                except Exception as e:
                    print(f"[ERROR] Failed to load local questions: {e}")
                    def show_error():
                        messagebox.showerror("Error", f"AI and local question loading failed:\n{e}")
                        self.master.destroy()
                    self.master.after(0, show_error)



            if new_questions:
                self.master.after(0, on_success)
            else:
                print("[WARN] Could not get unique AI question. Falling back to local.")
                try:
                    self.master.after(0, fallback_to_local)
                except Exception as e:
                    print("[WARN] Could not trigger fallback_to_local:", e)
 

    def start_question_thread(self):
        threading.Thread(target=self.load_questions_async, daemon=True).start()         

    def display_question(self):
        self.current_question = self.questions[self.q_index]
        print("[DEBUG] Displaying question:", self.current_question)
        self.question_label.config(text=f"❓ {self.current_question['question']}")

        options = self.current_question['options']
        random.shuffle(options)

        for i, option in enumerate(options):
            self.answer_buttons[i].config(text=option)

        self.correct_answer = self.current_question['correct'].strip().lower()
        self.time_remaining = 20
        self.timer_label.config(text=f"⏰ Time left: {self.time_remaining}s")
        self.status.config(text=f"{self.username} | Q{self.q_index + 1}/{len(self.questions)} | Score: {self.score}")

        self.timer_running = True
        self.update_timer()

    def update_timer(self):
        if self.time_remaining > 0:
            self.time_remaining -= 1
            self.timer_label.config(text=f"⏰ Time left: {self.time_remaining}s")
            self.timer_job = self.master.after(1000, self.update_timer)
        else:
            self.timer_label.config(text="⏰ Time's up!")
            self.master.after_cancel(self.timer_job)
            self.timer_job = None
            self.handle_incorrect()

    def submit_answer(self, selected_index):
        selected = self.answer_buttons[selected_index].cget("text").strip().lower()
        print("[DEBUG] Submitted:", selected)
        print("[DEBUG] Expected:", self.correct_answer)

        # Stop the timer if it's running
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None

        if selected == self.correct_answer:
            # Award character
            award_character(self.username, self.category, root=self.master)

            # Check progress
            progress = get_user_progress(self.username)
            earned = progress.get("characters", [])

            if all(cat in earned for cat in CHARACTER_CATEGORIES):
                # 🎉 User won the game
                self.master.after(500, lambda: self.go_to_home(win=True))
                return  # 🛑 Don't continue below
            else:
                messagebox.showwarning("Congratulation!","You WON a character!")
                show_animated_banner(self.master, f"🎉 You unlocked the {self.category} character!")
        else:
            print("[DEBUG] Answer is incorrect.")
            messagebox.showwarning("Incorrect", "Sorry, that's the wrong answer.")

        # Only return to main screen if they didn't win the game
        self.master.after(0, self.master.destroy)
        new_window = tk.Toplevel()
        CategorySelectApp(new_window)
    
        
    def go_to_home(self, win=False):
        self.master.destroy()
        home = tk.Toplevel()

        if win:
            # ✅ Ask after delay so window has time to build
            def prompt_restart():
                restart = messagebox.askyesno("You Won!", "You collected all 6 characters! Start a new game?")
                if restart:
                    # Reset progress
                    data = load_progress()
                    user = data.get(self.username, {})
                    user["characters"] = []
                    user["correct_count"] = 0
                    user["total_correct"] = 0
                    data[self.username] = user
                    save_progress(data)
                else:
                    home.destroy()

            home.after(500, prompt_restart)

        CategorySelectApp(home, username=self.username)
        
    def start_character_challenge(self):
        update_user_progress(self.username, reset=True)
        messagebox.showinfo("Character Challenge!", "You earned a special challenge! Choose your category.")

        # Go to the wheel but allow custom category selection for character challenge
        self.master.withdraw()  # Hides it safely
        
        new_root = tk.Toplevel(self.master)
        app = CategorySelectApp(new_root, character_challenge=True, username=self.username)

    def next_question(self):
        self.q_index += 1
        if self.q_index >= len(self.questions):
            self.save_score()
            if self.timer_job:
                self.master.after_cancel(self.timer_job)
                self.timer_job = None
            messagebox.showinfo("Quiz Complete", f"{self.username}, you scored {self.score}/{len(self.questions)}.")
            self.master.withdraw()  # Hides it safely

        else:
            self.display_question()
            print("[DEBUG] Questions to display:", self.questions)


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
            
            self.master.withdraw()  # ✅ DO NOT destroy, just hide
            new_root = tk.Toplevel(self.master)  # ✅ Create new window in same context
            app = CategorySelectApp(new_root)
            # ✅ DO NOT call new_root.mainloop()!

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
