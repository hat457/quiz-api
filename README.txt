# AI Coding Quiz (Terminal Version)

This is a terminal-based quiz app that uses AI to generate multiple-choice programming questions in real-time.

## Features
- Uses OpenRouter.ai to generate new quiz questions
- User answers interactively in the terminal
- Score is shown at the end

## Setup

1. Install the required library:
```
pip install openai
```

2. Get a free API key from [https://openrouter.ai/account/keys](https://openrouter.ai/account/keys)

3. Open `quiz.py` and replace:
```
openai.api_key = "sk-or-REPLACE_WITH_YOUR_KEY"
```
with your real key.

## Run the Quiz
```
python quiz.py
```

Have fun testing your coding knowledge!
