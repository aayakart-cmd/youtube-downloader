from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import yt_dlp
import os
import uuid

app = Flask(__name__)
CORS(app)  # Allow requests from other domains (like your static HTML)

DOWNLOAD_FOLDER = 'static/downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Web UI route
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# Web form download route
@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    if not url:
        return "Error: URL is required"

    video_id = str(uuid.uuid4())
    output_path = f"{DOWNLOAD_FOLDER}/{video_id}.%(ext)s"

    ydl_opts = {
        'outtmpl': output_path,
        'format': 'best'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            file = os.path.basename(filename)
            return f'<a href="/static/downloads/{file}" download>Click to Download</a>'
    except Exception as e:
        return f"Error: {str(e)}"

# API route for static HTML
@app.route('/api/download', methods=['POST'])
def api_download():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "URL is required"}), 400

    video_id = str(uuid.uuid4())
    output_path = f"{DOWNLOAD_FOLDER}/{video_id}.%(ext)s"

    ydl_opts = {
        'outtmpl': output_path,
        'format': 'best'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            file = os.path.basename(filename)
            return jsonify({
                "status": "success",
                "download_link": f"/static/downloads/{file}"
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
