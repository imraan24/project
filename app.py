from flask import Flask, request, jsonify
import os
import uuid
import whisper
import yt_dlp
from transformers import pipeline
from deep_translator import GoogleTranslator

app = Flask(__name__)

# Load models
whisper_model = whisper.load_model("base")
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# Download and transcribe YouTube audio
def transcribe_audio(youtube_url):
    try:
        unique_id = str(uuid.uuid4())
        output_template = unique_id + ".%(ext)s"
        output_filename = unique_id + ".mp3"
        ffmpeg_path = os.path.join(os.getcwd(), "ffmpeg.exe")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'quiet': True,
            'ffmpeg_location': ffmpeg_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        print(f"[INFO] Transcribing file: {output_filename}")
        result = whisper_model.transcribe(output_filename)
        os.remove(output_filename)
        return result["text"]

    except Exception as e:
        return f"Error transcribing audio: {str(e)}"

# Translate text
def translate_text(text, target_lang):
    try:
        return GoogleTranslator(source="auto", target=target_lang).translate(text)
    except Exception as e:
        return f"Translation Error: {str(e)}"

# Break long text into chunks (for summarization)
def chunk_text(text, max_tokens=700):
    words = text.split()
    return [' '.join(words[i:i + max_tokens]) for i in range(0, len(words), max_tokens)]

# Summarize long text safely
def summarize_text(text, target_lang):
    try:
        if len(text.split()) < 50:
            return f"Transcript too short to summarize:\n{text}"

        # Translate to English for summarization
        english_text = translate_text(text, "en") if target_lang != "en" else text
        chunks = chunk_text(english_text)

        full_summary = ""
        for chunk in chunks:
            summary = summarizer(chunk, max_length=200, min_length=50, do_sample=False)[0]['summary_text']
            full_summary += summary + " "

        # Translate back to target language if needed
        return translate_text(full_summary.strip(), target_lang) if target_lang != "en" else full_summary.strip()

    except Exception as e:
        return f"Error summarizing: {str(e)}"

# Flask API route
@app.route('/summarize', methods=['POST'])
def summarize():
    data = request.json
    video_url = data.get("video_url")
    language = data.get("language", "en")

    if not video_url:
        return jsonify({"error": "No video URL provided"}), 400

    print(f"[INFO] Downloading and processing: {video_url}")
    transcript = transcribe_audio(video_url)

    if transcript.startswith("Error"):
        return jsonify({"error": transcript}), 500

    print(f"[INFO] Summarizing and translating to {language}")
    summary = summarize_text(transcript, language)

    return jsonify({
        "video_url": video_url,
        "language": language,
        "summary": summary
    })

if __name__ == '__main__':
    app.run(debug=True)
