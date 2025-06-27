# Only the changes relevant to the spinning wheel and crash fix are modified.
# Full updated code:

import tkinter as tk 
from tkinter import messagebox
from tkinter import PhotoImage
import math
import random
import json
import os
import webbrowser
from PIL import Image, ImageTk

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
    def __init__(self, master, categories, icons, command, **kwargs):
        super().__init__(master, width=300, height=300, bg="white", highlightthickness=0, **kwargs)
        self.categories = categories
        self.command = command
        self.icons = icons
        self.angle = 0
        self.is_spinning = False
        self.segments = len(categories)
        self.segment_colors = ["#ff9999", "#99ccff", "#99ff99", "#ffcc99", "#ccccff", "#ffff99"]
        self.bind("<Button-1>", self.spin)
        self.draw_wheel_rotated(0)
        self.spin_job = None  # NEW: Track after() ID

    def spin(self, event=None):
        if self.is_spinning:
            return
        self.is_spinning = True
        self.spin_velocity = random.uniform(20, 30)
        self.friction = 0.97
        self.min_velocity = 0.3
        self.spin_job = self.after(20, self.animate_spin)

    def animate_spin(self):
        if not self.winfo_exists():
            return

        if self.spin_velocity > self.min_velocity:
            self.angle += self.spin_velocity
            self.angle %= 360
            self.draw_wheel_rotated(self.angle)
            self.spin_velocity *= self.friction
            self.spin_job = self.after(20, self.animate_spin)
        else:
            self.is_spinning = False
            final_angle = self.angle % 360
            pointer_angle = (final_angle + 30) % 360  # FIXED: no offset
            segment_angle = 360 / self.segments
            selected_index = int(pointer_angle // segment_angle) % self.segments

            selected_category = self.categories[selected_index]
            selected_icon = self.icons[selected_index]
            self.show_selected_category_flip(selected_category, selected_icon)

    def draw_wheel_rotated(self, angle_offset):
        self.delete("all")
        center_x, center_y = 150, 150

        if not hasattr(self, 'wheel_base_img'):
            self.wheel_base_img = Image.open("wheel_3d.png").resize((280, 280))

        rotated = self.wheel_base_img.rotate(angle_offset, resample=Image.BICUBIC)  # FIXED: use +angle
        self.tk_rotated = ImageTk.PhotoImage(rotated)
        self.create_image(center_x, center_y, image=self.tk_rotated)

        self.create_polygon([145, 10, 155, 10, 150, 30], fill="red")
        self.create_polygon([150, 5, 160, 35, 150, 30, 140, 35], fill="#333", outline="#111")
        self.create_line(150, 5, 150, 30, fill="#777", width=1)

    def show_selected_category_flip(self, category, icon):
        self.icon = icon
        self.flip_reveal(category, icon)

    def flip_reveal(self, category, icon, step=0):
        self.delete("all")
        self.create_text(150, 60, text="You got:", font=("Helvetica", 16, "bold"), fill="#333")

        scale_x = max(0.1, abs(math.cos(math.radians(step * 10))))
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

        if step == 9:
            self.after(800, lambda: self.command(category))
            return

        self.after(50, lambda: self.flip_reveal(category, icon, step + 1))




    def draw_wheel_rotated(self, angle_offset):
        self.delete("all")
        center_x, center_y = 150, 150

        # Rotate the image (requires PIL)
        from PIL import Image, ImageTk

        if not hasattr(self, 'wheel_base_img'):
            # Load original image only once
            self.wheel_base_img = Image.open("wheel_3d.png").resize((280, 280))  # Slightly smaller than canvas

        rotated = self.wheel_base_img.rotate(angle_offset, resample=Image.BICUBIC)
        self.tk_rotated = ImageTk.PhotoImage(rotated)
        self.create_image(center_x, center_y, image=self.tk_rotated)

        # Draw arrow on top
        #self.create_polygon([145, 10, 155, 10, 150, 30], fill="black")


            # 3D-looking arrow (shaded sides)
        # Arrow at top pointing down
        #self.create_polygon([140, 30, 160, 30, 150, 10], fill="red")
        self.create_polygon([150, 35, 160, 15, 150, 10, 140, 15], fill="#333", outline="#111")
        self.create_line(150, 35, 150, 10, fill="#777", width=1)


class CategorySelectApp:
    def __init__(self, master):
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

        tk.Label(master, text="Spin the wheel to choose a category:", font=("Helvetica", 14), bg="#f0f4f8", fg="#333").pack(pady=10)

        self.categories = ["Python", "JavaScript", "HTML", "C++", "Java", "SQL"]

        def load_icon(path):
            return PhotoImage(file=path).subsample(16, 16)

        self.icons = [
            load_icon("category_icon_python.png"),
            load_icon("category_icon_js.png"),
            load_icon("category_icon_html.png"),
            load_icon("category_icon_java.png"),
            load_icon("category_icon_cpp.png"),            
            load_icon("category_icon_sql.png"),
        ]

        self.wheel = SpinningWheel(master, self.categories, self.icons, self.start_quiz)
        self.wheel.pack(pady=10)

    def start_quiz(self, category):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Missing Info", "Please enter your name.")
            return

        with open("user.json", "w") as f:
            json.dump({"username": name}, f)

        fade_out(self.master, lambda: self.launch_quiz(name, category))

    def launch_quiz(self, name, category):
        self.master.destroy()
        root = tk.Tk()
        root.attributes('-alpha', 0.0)
        TriviaQuizApp(root, username=name, category=category)
        fade_in(root)
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

        with open("questions.json", "r") as f:
            all_questions = json.load(f)
        self.questions = [q for q in all_questions if q['topic'].lower() == category.lower()]

        if not self.questions:
            messagebox.showerror("No Questions", f"No questions found for category '{category}'")
            self.master.destroy()
            return

        random.shuffle(self.questions)
        self.q_index = 0
        self.score = 0

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

        self.display_question()

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
        if selected == self.correct_answer:
            self.score += 1
            self.next_question()
        else:
            self.handle_incorrect()

    def next_question(self):
        self.q_index += 1
        if self.q_index >= len(self.questions):
            self.save_score()
            messagebox.showinfo("Quiz Complete", f"{self.username}, you scored {self.score}/{len(self.questions)}.")
            self.master.destroy()
        else:
            self.display_question()

    def handle_incorrect(self):
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
