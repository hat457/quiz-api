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


class CharacterChallengeQuiz:
    recent_questions_memory = {}

    def __init__(self, master, username, category):
        self.master = master
        self.username = username.strip().lower()
        self.category = category
        self.master.title("Character Challenge")
        self.master.geometry("360x640")
        self.master.configure(bg="#f0f4f8")
        self.master.resizable(False, False)

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

        if USE_AI_QUESTIONS:
            self.questions = []
            self.header.config(text=f"Loading {category} challenge question from AI...")
            # Load memory once at app start
            ai_question_memory = load_ai_memory()


            def load_questions_async():
                print("[DEBUG] Loading questions from AI...")
                attempts = 0
                max_attempts = 5
                new_questions = questions
                recent = ai_question_memory.get(category, [])
                

                while attempts < max_attempts:
                    questions = get_ai_questions(category, num_questions=1)
                    print("[DEBUG] AI returned:", questions)
                    if questions:
                        q_text = questions[0].get("question", "").strip()
                        if q_text and q_text not in recent:
                            # Update memory
                            recent.append(q_text)
                            if len(recent) > 5:
                                recent.pop(0)
                            ai_question_memory[category] = recent
                            save_ai_memory(ai_question_memory)
                            break
                    attempts += 1

                if not new_questions:
                    print("[WARN] Could not get unique AI question. Falling back to local questions.json.")
                    try:
                        with open("questions.json", "r") as f:
                            all_questions = json.load(f)
                        self.questions = [q for q in all_questions if q['topic'].lower() == self.category.lower()]
                        random.shuffle(self.questions)
                        self.q_index = 0
                        self.score = 0
                        self.master.after(0, self.display_question)
                        return
                    except Exception as e:
                        messagebox.showerror("Error", f"AI and local question loading failed:\n{e}")
                        self.master.after(0, self.master.destroy)
                        return


                self.questions = new_questions
                self.q_index = 0
                self.score = 0
                self.master.after(0, self.display_question)

            threading.Thread(target=load_questions_async).start()
            return
        else:
            print("[DEBUG] Loading questions from JSON file")
            with open("questions.json", "r") as f:
                all_questions = json.load(f)
            self.questions = [q for q in all_questions if q['topic'].lower() == category.lower()]
            self.q_index = 0
            self.score = 0
            self.display_question()

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