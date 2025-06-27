class TriviaQuestionScreen:
    def __init__(self, master, questions, category, icon, username, on_finish):
        self.master = master
        self.questions = questions
        self.category = category
        self.icon = icon
        self.username = username
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

        choices = question['choices'][:]
        random.shuffle(choices)

        for i, btn in enumerate(self.answer_buttons):
            btn.config(text=choices[i], state="normal")

        self.update_header()
        self.start_timer()

    def update_header(self):
        self.header.config(text=f"{self.username} | Q{self.q_index+1}/{len(self.questions)} | Score: {self.score}")

    def start_timer(self):
        self.timer_seconds = 15
        self.update_timer()

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
        correct_text = question['answer']

        if selected_text == correct_text:
            self.score += 1

        for btn in self.answer_buttons:
            btn.config(state="disabled")

        self.master.after(1000, self.next_question)

    def next_question(self):
        self.q_index += 1
        if self.q_index >= len(self.questions):
            self.frame.destroy()
            self.on_finish(self.score)
        else:
            self.display_question()
