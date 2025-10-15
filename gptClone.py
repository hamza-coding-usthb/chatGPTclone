# gptClone.py
import os
from flask import Flask
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv() # take environment variables from .env.

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)
app = Flask(__name__)

@app.route("/")
def index():
    return "Hello, World!"

if __name__ == "__main__":
    app.run()
