from flask import Flask, render_template, request, jsonify
import requests, json, html, base64
from pyDes import *

app = Flask(__name__)
des_cipher = des(b"38346591", ECB, b"\0\0\0\0\0\0\0\0", pad=None, padmode=PAD_PKCS5)

def decrypt_url(url):
    try:
        enc_url = base64.b64decode(url.strip())
        dec_url = des_cipher.decrypt(enc_url, padmode=PAD_PKCS5).decode("utf-8")
        return dec_url.replace("_96.mp4", "_320.mp3").replace("_96_p.mp4", "_320.mp4")
    except: return ""

def fetch_albums(lang):
    try:
        cookies = {"L": lang}
        url = "https://www.jiosaavn.com/api.php?__call=content.getHomepageData&_format=json"
        res = requests.get(url, cookies=cookies).json()
        data = res["new_albums"]
        return [{"name": html.unescape(i["text"]), "image": i["image"].replace("150x150", "500x500"), "id": i["albumid"]} for i in data]
    except: return []

@app.route("/")
def index():
    # Home Page Data
    data = {
        "malayalam": fetch_albums("malayalam"),
        "tamil": fetch_albums("tamil"),
        "hindi": fetch_albums("hindi")
    }
    return render_template("index.html", data=data)

@app.route("/api/album/<id>")
def album_details(id):
    url = f"https://www.jiosaavn.com/api.php?__call=content.getAlbumDetails&albumid={id}&_format=json"
    data = requests.get(url).json()
    return jsonify(data)

@app.route("/api/song/<id>")
def song_details(id):
    url = f"https://www.jiosaavn.com/api.php?__call=song.getDetails&pids={id}&_format=json"
    res = requests.get(url).json()
    song_data = res[id]
    song_data["download_url"] = decrypt_url(song_data["encrypted_media_url"])
    return jsonify(song_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
        
