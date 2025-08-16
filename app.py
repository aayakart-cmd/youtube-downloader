from flask import Flask, render_template, request, jsonify, url_for
from flask_cors import CORS
import yt_dlp
import os
import uuid
import logging

# Basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

DOWNLOAD_FOLDER = 'static/downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


def try_download_with_opts(url, ydl_opts):
    """Try to download with given ydl_opts. Returns local filepath on success."""
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename  # full path


@app.route('/api/download', methods=['POST'])
def api_download():
    """
    Expects JSON: { "url": "<youtube url>" }
    Returns JSON: { status: "success", download_url: "<public-url>" } or error.
    """
    data = request.get_json() or {}
    url = data.get("url")
    if not url:
        return jsonify({"status": "error", "message": "URL is required"}), 400

    # unique id so multiple downloads don't collide
    video_id = str(uuid.uuid4())
    out_template = os.path.join(DOWNLOAD_FOLDER, f"{video_id}.%(ext)s")

    # common http headers to mimic normal browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36",
        "Referer": "https://www.youtube.com/"
    }

    # A list of option-sets to try (primary -> fallbacks)
    opts_list = [
        # Primary: download best video+audio, merge if necessary
        {
            "outtmpl": out_template,
            "format": "bestvideo+bestaudio/best",
            "noplaylist": True,
            "http_headers": headers,
            "geo_bypass": True,
            "socket_timeout": 30,
            "no_warnings": True,
            "quiet": True,
        },
        # Fallback 1: simple best single-file
        {
            "outtmpl": out_template,
            "format": "best",
            "noplaylist": True,
            "http_headers": headers,
            "geo_bypass": True,
            "socket_timeout": 30,
            "no_warnings": True,
            "quiet": True,
        },
        # Fallback 2: try only audio stream (sometimes works when video blocked)
        {
            "outtmpl": out_template,
            "format": "bestaudio/best",
            "noplaylist": True,
            "http_headers": headers,
            "geo_bypass": True,
            "socket_timeout": 30,
            "no_warnings": True,
            "quiet": True,
            # do not force postprocessing (avoid requiring ffmpeg)
        },
        # Fallback 3: force generic extractor (last resort)
        {
            "outtmpl": out_template,
            "format": "best",
            "noplaylist": True,
            "force_generic_extractor": True,
            "http_headers": headers,
            "geo_bypass": True,
            "socket_timeout": 30,
            "no_warnings": True,
            "quiet": True,
        }
    ]

    last_error = None
    for idx, opts in enumerate(opts_list, start=1):
        try:
            logger.info("Attempt %d: trying download with options: %s", idx, {k: v for k, v in opts.items() if k != "http_headers"})
            filename = try_download_with_opts(url, opts)
            # ensure file exists
            if not os.path.isfile(filename):
                raise Exception("Download completed but file not found: " + str(filename))

            # create external URL for the static file
            file_basename = os.path.basename(filename)
            download_url = url_for('static', filename=f"downloads/{file_basename}", _external=True)
            return jsonify({"status": "success", "download_url": download_url}), 200

        except Exception as e:
            logger.warning("Attempt %d failed: %s", idx, str(e))
            last_error = str(e)
            # continue to next fallback

    # All attempts failed
    return jsonify({"status": "error", "message": "All download attempts failed", "details": last_error}), 500


# Keep the old web form route (optional)
@app.route('/download', methods=['POST'])
def download_form():
    url = request.form.get('url')
    if not url:
        return "Error: URL is required", 400

    # For form route, reuse the API logic via internal request simulation
    response = app.test_client().post('/api/download', json={"url": url})
    return response.get_data(as_text=True), response.status_code, {'Content-Type': 'application/json'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
