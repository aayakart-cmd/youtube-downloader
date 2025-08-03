from flask import Flask, render_template, request
import yt_dlp
import os
import uuid

app = Flask(__name__)
DOWNLOAD_FOLDER = 'static/downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
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

if __name__ == '__main__':
    app.run(debug=True)
