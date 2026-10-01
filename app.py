from flask import Flask, request, jsonify, send_file
from yt_dlp import YoutubeDL
import os
import tempfile

app = Flask(__name__)

QUALITIES = {
    "360p": 360,
    "720p": 720,
    "1080p": 1080,
    "1440p": 1440,
    "4K": 2160
}

@app.get("/api/health")
def health():
    return jsonify({
        "ok": True,
        "service": "ClipDropper backend"
    })

@app.post("/api/download")
def download():
    data = request.get_json(silent=True) or {}

    url = (data.get("url") or "").strip()
    quality = data.get("quality", "1080p")

    if not url:
        return jsonify({"error": "Please enter a YouTube URL."}), 400

    if quality not in QUALITIES:
        return jsonify({"error": "Invalid quality."}), 400

    height = QUALITIES[quality]

    folder = tempfile.mkdtemp(prefix="clipdropper-")
    output = os.path.join(
        folder,
        "%(title).100s-%(id)s.%(ext)s"
    )

    options = {
        "outtmpl": output,
        "noplaylist": True,
        "merge_output_format": "mp4",
        "format": (
            f"bestvideo[height<={height}]+bestaudio/"
            f"best[height<={height}]/best"
        ),
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        base, _ = os.path.splitext(filename)
        mp4_file = base + ".mp4"

        final_file = (
            mp4_file
            if os.path.exists(mp4_file)
            else filename
        )

        if not os.path.exists(final_file):
            return jsonify({
                "error": "The video file was not created."
            }), 500

        return send_file(
            final_file,
            as_attachment=True,
            download_name=os.path.basename(final_file),
            mimetype="video/mp4"
        )

    except Exception as exc:
        return jsonify({
            "error": "Download failed.",
            "details": str(exc)[:500]
        }), 422


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
