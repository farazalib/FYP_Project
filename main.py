
"""# app.py (Flask backend)

from flask import Flask, render_template, request, redirect, url_for, session
import requests
import os
import csv
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # For sessions

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Function to save user data in CSV
def save_user_data(name, email, mood, recommended_songs, searched_songs, weather_songs, favorites):
    file_path = "user_data.csv"
    file_exists = os.path.isfile(file_path)

    with open(file_path, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow([
                "Name", "Email", "Mood", "Recommended Songs", "Searched Songs", "Weather Songs", "Favorite Songs"
            ])
        writer.writerow([
            name,
            email,
            mood,
            ", ".join(recommended_songs),
            ", ".join(searched_songs),
            ", ".join(weather_songs),
            ", ".join(favorites)
        ])

@app.route("/")
def welcome():
    return render_template("welcome.html")

@app.route("/main", methods=["GET", "POST"])
def main_page():
    if request.method == "POST":
        name = request.form.get("name", "User")
        email = request.form.get("email", "")
        session["name"] = name
        session["email"] = email
        session["favorites"] = []
        session["searched"] = []
        return render_template("main.html", name=name)
    else:
        return render_template("main.html", name=session.get("name", "User"))

@app.route("/detect_mood", methods=["POST"])
def detect_mood():
    if 'image' not in request.files:
        return render_template("main.html", name=session.get("name", "User"), error="No image file provided.")

    image = request.files['image']
    if image.filename == '':
        return render_template("main.html", name=session.get("name", "User"), error="No selected file.")

    filename = secure_filename(image.filename)
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image.save(image_path)
    session['last_image'] = image_path

    try:
        files = {'file': open(image_path, 'rb')}
        response = requests.post("https://ai-song-recommendation-production.up.railway.app/recommend", files=files)
        if response.status_code == 200:
            data = response.json()
            mood = data.get("emotion") or data.get("mood", "Unknown")
            song_titles = data.get("songs", [])

            songs = [{
                "name": title,
                "artist": "Unknown",
                "url": f"https://open.spotify.com/search/{title.replace(' ', '%20')}"
            } for title in song_titles]

            session["mood"] = mood
            session["recommended"] = [song["name"] for song in songs]

            # Save data to CSV
            save_user_data(
                name=session.get("name", "User"),
                email=session.get("email", ""),
                mood=mood,
                recommended_songs=[song["name"] for song in songs],
                searched_songs=session.get("searched", []),
                weather_songs=session.get("weather", []),
                favorites=session.get("favorites", [])
            )

            return render_template("main.html", name=session.get("name", "User"), mood=mood, songs=songs, image_path=image_path)
        else:
            return render_template("main.html", name=session.get("name", "User"), error="API Error", image_path=image_path)
    except Exception as e:
        return render_template("main.html", name=session.get("name", "User"), error=f"Server Error: {e}", image_path=image_path)

@app.route("/add_to_favorites", methods=["POST"])
def add_to_favorites():
    name = request.form.get("name")
    artist = request.form.get("artist")
    url = request.form.get("url")

    fav = f"{name} - {artist}"
    if "favorites" not in session:
        session["favorites"] = []
    if fav not in session["favorites"]:
        session["favorites"].append(fav)

    return redirect(request.referrer or url_for('main_page'))

@app.route("/search", methods=["POST"])
def search():
    query = request.form.get("search", "")
    if query:
        if "searched" not in session:
            session["searched"] = []
        session["searched"].append(query)
        return redirect(f"https://www.google.com/search?q={query}+site:open.spotify.com")
    return redirect(url_for('main_page'))

@app.route("/suggestions", methods=["GET", "POST"])
def suggestions():
    songs = []
    desc = "N/A"
    temp = "N/A"
    error = None

    if request.method == "POST":
        lat = request.form.get("lat")
        lon = request.form.get("lon")

        if not lat or not lon:
            error = "Location not available."
        else:
            try:
                response = requests.post("https://ai-song-recommendation-production.up.railway.app/weather_songs", json={"latitude": lat, "longitude": lon})
                if response.status_code == 200:
                    data = response.json()
                    desc = data.get("weather", "N/A").capitalize()
                    temp = data.get("temperature", "N/A")
                    song_titles = data.get("songs", [])
                    songs = [{
                        "name": title,
                        "artist": "Unknown",
                        "url": f"https://open.spotify.com/search/{title.replace(' ', '%20')}"
                    } for title in song_titles]
                    session["weather"] = [song["name"] for song in songs]
                else:
                    error = f"API Error {response.status_code}: {response.text}"
            except Exception as e:
                error = str(e)

    return render_template("suggestion.html", desc=desc, temp=temp, songs=songs, error=error)

if __name__ == "__main__":
    app.run(debug=True)"""

from flask import Flask, render_template, request, redirect, url_for, session
import requests
import os
import csv
import base64
from PIL import Image
from io import BytesIO
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Save user data in CSV
def save_user_data(name, email, mood, recommended_songs, searched_songs, weather_songs, favorites):
    file_path = "user_data.csv"
    file_exists = os.path.isfile(file_path)

    with open(file_path, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow([
                "Name", "Email", "Mood", "Recommended Songs", "Searched Songs", "Weather Songs", "Favorite Songs"
            ])
        writer.writerow([
            name,
            email,
            mood,
            ", ".join(recommended_songs),
            ", ".join(searched_songs),
            ", ".join(weather_songs),
            ", ".join(favorites)
        ])

@app.route("/")
def welcome():
    return render_template("welcome.html")

@app.route("/main", methods=["GET", "POST"])
def main_page():
    if request.method == "POST":
        name = request.form.get("name", "User")
        email = request.form.get("email", "")
        session["name"] = name
        session["email"] = email
        session["favorites"] = []
        session["searched"] = []
        return render_template("main.html", name=name)
    else:
        return render_template("main.html", name=session.get("name", "User"))

@app.route("/detect_mood", methods=["POST"])
def detect_mood():
    webcam_image_data = request.form.get("webcam_image")
    image = request.files.get("image")

    if image and image.filename != '':
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)
    elif webcam_image_data:
        try:
            header, encoded = webcam_image_data.split(",", 1)
            decoded = base64.b64decode(encoded)
            image = Image.open(BytesIO(decoded))
            filename = "webcam_capture.png"
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
        except Exception as e:
            return render_template("main.html", name=session.get("name", "User"), error=f"Webcam Error: {e}")
    else:
        return render_template("main.html", name=session.get("name", "User"), error="No image provided.")

    # Send image to external mood detection API
    try:
        files = {'file': open(image_path, 'rb')}
        response = requests.post("https://ai-song-recommendation-production.up.railway.app/recommend", files=files)
        if response.status_code == 200:
            data = response.json()
            mood = data.get("emotion") or data.get("mood", "Unknown")
            song_titles = data.get("songs", [])

            songs = [{
                "name": title,
                "artist": "Unknown",
                "url": f"https://open.spotify.com/search/{title.replace(' ', '%20')}"
            } for title in song_titles]

            session["mood"] = mood
            session["recommended"] = [song["name"] for song in songs]

            save_user_data(
                name=session.get("name", "User"),
                email=session.get("email", ""),
                mood=mood,
                recommended_songs=[song["name"] for song in songs],
                searched_songs=session.get("searched", []),
                weather_songs=session.get("weather", []),
                favorites=session.get("favorites", [])
            )

            return render_template("main.html", name=session.get("name", "User"), mood=mood, songs=songs, image_path=image_path)
        else:
            return render_template("main.html", name=session.get("name", "User"), error="API Error", image_path=image_path)
    except Exception as e:
        return render_template("main.html", name=session.get("name", "User"), error=f"Server Error: {e}", image_path=image_path)

@app.route("/add_to_favorites", methods=["POST"])
def add_to_favorites():
    name = request.form.get("name")
    artist = request.form.get("artist")
    url = request.form.get("url")

    fav = f"{name} - {artist}"
    if "favorites" not in session:
        session["favorites"] = []
    if fav not in session["favorites"]:
        session["favorites"].append(fav)

    return redirect(request.referrer or url_for('main_page'))

@app.route("/search", methods=["POST"])
def search():
    query = request.form.get("search", "")
    if query:
        if "searched" not in session:
            session["searched"] = []
        session["searched"].append(query)
        return redirect(f"https://open.spotify.com/search/{query.replace(' ', '%20')}")
    return redirect(url_for('main_page'))

@app.route("/suggestions", methods=["GET", "POST"])
def suggestions():
    songs = []
    desc = "N/A"
    temp = "N/A"
    error = None

    if request.method == "POST":
        lat = request.form.get("lat")
        lon = request.form.get("lon")

        if not lat or not lon:
            error = "Location not available."
        else:
            try:
                response = requests.post("https://ai-song-recommendation-production.up.railway.app/weather_songs", json={"latitude": lat, "longitude": lon})
                if response.status_code == 200:
                    data = response.json()
                    desc = data.get("weather", "N/A").capitalize()
                    temp = data.get("temperature", "N/A")
                    song_titles = data.get("songs", [])
                    songs = [{
                        "name": title,
                        "artist": "Unknown",
                        "url": f"https://open.spotify.com/search/{title.replace(' ', '%20')}"
                    } for title in song_titles]
                    session["weather"] = [song["name"] for song in songs]
                else:
                    error = f"API Error {response.status_code}: {response.text}"
            except Exception as e:
                error = str(e)

    return render_template("suggestion.html", desc=desc, temp=temp, songs=songs, error=error)

if __name__ == "__main__":
    app.run(debug=True)

