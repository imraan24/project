from youtube_transcript_api import YouTubeTranscriptApi

video_id = "dQw4w9WgXcQ"  # Replace this with a video ID that you are testing

try:
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    print("Transcript Found:\n", transcript[:5])  # Print first 5 lines
except Exception as e:
    print("Error:", str(e))
