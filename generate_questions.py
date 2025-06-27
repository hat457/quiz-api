import openai
import json
import random
import time

# Setup for OpenRouter.ai
openai.api_base = "https://openrouter.ai/api/v1"
openai.api_key = "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"  # Replace with your real OpenRouter API key

def generate_question(topic):
    prompt = f"""
Create a multiple-choice programming quiz question about "{topic}".
Respond in JSON format like this:
{{
  "question": "Which keyword defines a function in Python?",
  "correct": "def",
  "wrong": ["func", "define", "function"],
  "topic": "{topic}"
}}
Only return the JSON. Do not include any explanation or extra text.
"""

    try:
        response = openai.ChatCompletion.create(
            model="mistralai/mistral-7b-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        content = response['choices'][0]['message']['content']
        raw_q = json.loads(content)

        # Prepare options and shuffle
        options = raw_q["wrong"] + [raw_q["correct"]]
        random.shuffle(options)

        return {
            "question": raw_q["question"],
            "options": options,
            "correct": raw_q["correct"],
            "topic": raw_q["topic"]
        }

    except Exception as e:
        print("❌ Error generating question:", e)
        return None

def run_quiz(topic, num_questions):
    score = 0
    for i in range(num_questions):
        print(f"\n🎯 Question {i + 1}")
        q = generate_question(topic)
        if not q:
            print("Skipping this question due to error.")
            continue

        print(q['question'])
        for idx, option in enumerate(q['options']):
            print(f"{idx + 1}. {option}")

        # Get user's answer
        while True:
            try:
                choice = int(input("Your answer (1-4): "))
                if 1 <= choice <= 4:
                    break
                else:
                    print("Please enter a number between 1 and 4.")
            except ValueError:
                print("Please enter a valid number.")

        selected_answer = q['options'][choice - 1]
        if selected_answer == q['correct']:
            print("✅ Correct!")
            score += 1
        else:
            print(f"❌ Wrong! The correct answer was: {q['correct']}")

        time.sleep(1)  # Optional: pace the quiz

    print("\n📊 Quiz Complete!")
    print(f"👉 You got {score} out of {num_questions} correct.")

# Run it
if __name__ == "__main__":
    topic = input("Enter a programming topic (e.g., Python, JavaScript): ").strip()
    num = int(input("How many questions do you want? "))
    run_quiz(topic, num)
