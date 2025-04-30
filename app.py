from flask import Flask, render_template, request, send_file
import requests
import os
import time
from elevenlabs import generate, set_api_key, save
from moviepy.editor import ImageSequenceClip
import shutil

app = Flask(__name__)

LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY", "temp")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "temp")

VIDEOS_FOLDER = "generated"
os.makedirs(VIDEOS_FOLDER, exist_ok=True)

def skapa_manus(prompt):
    return [
        f"{prompt} - Scen 1: Start",
        f"{prompt} - Scen 2: Mellanakt",
        f"{prompt} - Scen 3: Slutsats"
    ]

def generera_bilder(prompts):
    image_files = []
    for i, prompt in enumerate(prompts):
        url = "https://cloud.leonardo.ai/api/rest/v1/generations"
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {LEONARDO_API_KEY}",
            "content-type": "application/json"
        }
        data = {
            "height": 576,
            "width": 1024,
            "prompt": prompt,
            "num_images": 1
        }

        response = requests.post(url, headers=headers, json=data)
        generation_id = response.json()['sdGenerationJob']['generationId']

        while True:
            res = requests.get(f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}", headers=headers)
            data = res.json()
            if data['status'] == 'COMPLETE':
                image_url = data['generated_media'][0]['url']
                break
            time.sleep(2)

        img_data = requests.get(image_url).content
        filename = os.path.join(VIDEOS_FOLDER, f"frame_{i}.png")
        with open(filename, 'wb') as handler:
            handler.write(img_data)
        image_files.append(filename)
    return image_files

def skapa_video(image_files, duration=60):
    clip = ImageSequenceClip(image_files, fps=24)
    final_clip = clip.loop(duration=duration)
    output_path = os.path.join(VIDEOS_FOLDER, "animation.mp4")
    final_clip.write_videofile(output_path, codec="libx264")
    return output_path

@app.route("/", methods=["GET", "POST"])
def home():
    video_url = None
    error = None

    if request.method == "POST":
        user_prompt = request.form["prompt"]

        try:
            scenes = skapa_manus(user_prompt)
            image_files = generera_bilder(scenes)
            video_path = skapa_video(image_files)
            video_url = "/download/animation.mp4"
        except Exception as e:
            error = f"Fel: {str(e)}"

    return render_template("index.html", video_url=video_url, error=error)

@app.route("/download/<path:filename>")
def download_file(filename):
    return send_file(os.path.join(VIDEOS_FOLDER, filename), as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
