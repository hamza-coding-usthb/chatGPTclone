import os
import logging # Import the logging module
from flask import Flask, request, render_template
from dotenv import load_dotenv
import requests

# Configure logging to see detailed output in the console
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv() # Load environment variables from .env.

# --- DeepSeek/OpenRouter Configuration ---
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEEPSEEK_MODEL = "tngtech/deepseek-r1t2-chimera:free"
# ----------------------------------------

if not OPENROUTER_API_KEY:
    logging.warning("OPENROUTER_API_KEY environment variable is not set. API calls will fail.")

app = Flask(__name__)
conversation_history = []
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get")
def get_bot_response():
    userText = request.args.get('msg')
    conversation_history.append({"role": "user", "content": userText})
    logging.info(f"Received user query: {userText}")

    if not OPENROUTER_API_KEY:
        return "ERROR: OpenRouter API Key is missing. Please set the OPENROUTER_API_KEY environment variable in your .env file."

    headers = {
        'Authorization': f'Bearer {OPENROUTER_API_KEY}',
        'Content-Type': 'application/json'
    }

    data = {
        "model": DEEPSEEK_MODEL,
        "messages": conversation_history,
        "temperature": 0.5 
    }
    
    # Log the URL and the model being used
    logging.debug(f"Attempting API request to URL: {API_URL}")
    logging.debug(f"Payload model: {DEEPSEEK_MODEL}")

    try:
        # We ensure to pass data as 'json' to let requests handle the Content-Type header correctly
        response = requests.post(API_URL, json=data, headers=headers)
        
        # Check for non-200 status codes
        response.raise_for_status() 

        # Log successful status
        logging.info("API request successful (Status 200)")

        # Parse the response JSON
        result_json = response.json()
        ai_message = result_json['choices'][0]['message']['content']
        conversation_history.append({"role": "assistant", "content": ai_message})
        return ai_message

    except requests.exceptions.RequestException as e:
        # Log the full error and response text for debugging the 404
        logging.error(f"API Request failed for URL: {API_URL}")
        logging.error(f"Error details: {e}")
        
        if response.status_code == 404:
            # Check for common 404 causes on OpenRouter
            try:
                error_content = response.json()
                error_message = error_content.get('error', {}).get('message', 'Model might be unavailable.')
                return f"Error 404 (Not Found): The API endpoint is correct, but the model '{DEEPSEEK_MODEL}' might be temporarily unavailable on OpenRouter, or there's an issue with your network. Details: {error_message}"
            except:
                 return f"Error 404: The URL {API_URL} was not found. Please verify your connection."

        elif response.status_code == 429:
            return "The DeepSeek/OpenRouter free tier rate limit has been exceeded (429 Too Many Requests). Please wait and try again."
        elif response.status_code in [401, 403]:
            return "Authentication Error: Please check your OPENROUTER_API_KEY and key permissions."
        else:
            return f"An API request error occurred (Status {response.status_code}): {e}"

    except Exception as e:
        logging.critical(f"An unexpected error occurred: {e}", exc_info=True)
        return f"An unexpected error occurred: {e}"

if __name__ == "__main__":
    app.run(debug=True)
