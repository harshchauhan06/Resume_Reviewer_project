from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import os
import traceback
import re
import sys # Import sys for controlled exit

# --- Configuration & Initialization ---

# Tell Flask where to find templates (HTML) and static files (CSS/JS/images)
app = Flask(__name__, static_folder="static", template_folder="template")
CORS(app)

# Load Groq API key once globally
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    # This message will only appear in the Render logs if the key is missing
    print("=====================================================================")
    print("⚠️ CRITICAL ERROR: GROQ_API_KEY not set!")
    print("Please set the environment variable in Render dashboard.")
    print("=====================================================================")


# ----------------------------
# Serve frontend
# ----------------------------
@app.route("/")
def index():
    # Renders template/index.html
    return render_template("index.html")


# ----------------------------
# Backend API
# ----------------------------
@app.route("/feedback", methods=["POST"])
def feedback():
    # The GROQ_API_KEY is accessible here from the global scope (defined above)

    # 1. Check for API Key upfront. This handles the case where the key is truly missing.
    if not GROQ_API_KEY:
        error_msg = "Server Configuration Error: LLM API Key is not configured."
        print(f"ERROR: {error_msg}")
        # Return a service unavailable status since the backend dependency is missing
        return jsonify({"error": error_msg}), 503 

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON payload provided"}), 400

        job_role = data.get("job_role", "").strip()
        resume_text = data.get("resume_text", "").strip()
        job_desc = data.get("job_desc", "").strip()

        if not resume_text or not job_role:
            return jsonify({"error": "Resume text and job role are required"}), 400

        # Clean text and truncate to fit context window
        resume_text_clean = re.sub(r"\s+", " ", resume_text)[:6000] 
        job_desc_clean = re.sub(r"\s+", " ", job_desc)[:2000]       

        prompt = f"""
You are a career coach AI assistant. Review the following resume text and provide detailed feedback tailored for the job role: {job_role}.

Resume: {resume_text_clean}

Job Description: {job_desc_clean}

Analyze for:
- Missing skills relevant to the role
- Suggestions to improve formatting, clarity, and tone
- Highlight vague or redundant language
- Recommendations to tailor experience & achievements
- Provide section-wise feedback (Education, Experience, Skills, etc.)
"""

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            # Key is used here. If it's incorrect, Groq returns a 401.
            "Authorization": f"Bearer {GROQ_API_KEY}", 
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.1-8b-instant", 
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024, 
            "temperature": 0.7
        }

        # Use a timeout for the API call
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"Groq API call successful. Status: {response.status_code}")

        if response.status_code != 200:
            # This handles the BAD KEY (401) or other Groq errors
            return jsonify({
                "error": f"Groq API error {response.status_code}",
                "details": response.text
            }), 500

        result = response.json()
        if "choices" in result and result["choices"]:
            feedback_text = result["choices"][0]["message"]["content"]
        else:
            return jsonify({"error": "No choices returned from Groq", "details": result}), 500

        return jsonify({"feedback": feedback_text})

    except requests.exceptions.Timeout:
        return jsonify({"error": "Groq API request timed out."}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Could not connect to Groq API endpoint."}), 503
    except Exception as e:
        print("Exception occurred:", str(e))
        traceback.print_exc()
        # This generic error should now appear in Render logs for debugging
        return jsonify({"error": str(e)}), 500


@app.route("/ping")
def ping():
    return "pong"


# --- Application Runner ---

if __name__ == "__main__":
    # Ensure all required packages are installed (for self-diagnosis)
    try:
        import flask
        import requests
        import gunicorn # Added gunicorn check since it's required for Render start command
    except ImportError:
        print("=====================================================================")
        print("FATAL ERROR: Missing required Python packages.")
        print("Please run: pip install Flask flask-cors requests gunicorn")
        print("=====================================================================")
        sys.exit(1)

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)