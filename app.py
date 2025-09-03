import os
import requests
from flask import Flask, render_template, request, jsonify

# Initialize the Flask application
app = Flask(__name__)

# --- AI Model Configuration ---
# IMPORTANT: You need to get your own API key for the AI model.
# Replace 'YOUR_GEMINI_API_KEY' with your actual key.
# For deployment, it's best practice to set this as an environment variable.
API_KEY = os.environ.get('GEMINI_API_KEY', 'YOUR_GEMINI_API_KEY')
GEMINI_API_URL = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={API_KEY}'

# Route for the main chat page
@app.route('/')
def index():
    """
    Renders the main chat interface page.
    """
    # The HTML file should be in a folder named 'templates'
    return render_template('index.html')

# API endpoint to handle user questions
@app.route('/ask', methods=['POST'])
def ask():
    """
    Receives a user's question, sends it to the Gemini API,
    and returns the AI's response.
    """
    # Get the user's message from the incoming JSON request
    user_message = request.json.get('message')

    if not user_message:
        return jsonify({'error': 'No message provided.'}), 400
        
    if API_KEY == 'YOUR_GEMINI_API_KEY':
        # Provide a helpful message if the API key is not set
        return jsonify({
            'response': "Hello! It looks like the AI API key isn't set up yet. Please ask the developer to configure it on the backend."
        }), 200

    # --- Prepare the request for the Gemini API ---
    headers = {
        'Content-Type': 'application/json',
    }
    
    # The payload contains the user's message
    payload = {
        "contents": [{
            "parts": [{
                "text": user_message
            }]
        }]
    }

    try:
        # --- Send the request to the Gemini API ---
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        # --- Process the AI's response ---
        response_data = response.json()
        
        # Extract the generated text from the response
        # The structure can be complex, so we safely navigate it
        candidate = response_data.get('candidates', [{}])[0]
        content_part = candidate.get('content', {}).get('parts', [{}])[0]
        ai_response_text = content_part.get('text', 'Sorry, I could not get a response.')

        # Send the AI's response back to the frontend
        return jsonify({'response': ai_response_text})

    except requests.exceptions.RequestException as e:
        # Handle network errors or bad responses from the API
        print(f"Error calling Gemini API: {e}")
        return jsonify({'error': 'Failed to communicate with the AI service.'}), 500
    except (KeyError, IndexError) as e:
        # Handle unexpected response structure from the API
        print(f"Error parsing Gemini API response: {e}")
        return jsonify({'error': 'Received an invalid response from the AI service.'}), 500


if __name__ == '__main__':
    # This allows you to run the app locally for testing
    # For deployment, a WSGI server like Gunicorn will be used (see Procfile)
    app.run(debug=True, port=5001)

