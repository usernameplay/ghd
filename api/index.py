from flask import Flask, render_template, request, jsonify
import requests
import html
import base64
from Crypto.Cipher import DES
from Crypto.Util.Padding import unpad

app = Flask(__name__, template_folder='../templates')

# Decryption for JioSaavn
def decrypt_url(url):
    try:
        key = b'38346591'
        cipher = DES.new(key, DES.MODE_ECB)
        enc_url = base64.b64decode(url.strip())
        dec_url = unpad(cipher.decrypt(enc_url), 8).decode('utf-8')
        return dec_url.replace("_96.mp4", "_320.mp3").replace("_96.mp3", "_320.mp3")
    except:
        return ""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/home')
def get_home():
    langs = ['malayalam', 'tamil', 'hindi']
    results = {}
    for lang in langs:
        try:
            url = f"https://www.jiosaavn.com/api.php?__call=content.getHomepageData&_format=json&cc=in&_marker=0&ctx=web6dot0"
            res = requests.get(url, cookies={"L": lang}).json()
            results[lang] = [{
                "id": a["id"],
                "title": html.unescape(a["text"]),
                "image": a["image"].replace("150x150", "500x500"),
                "artist": a.get("subtitle", "")
            } for a in res.get("new_albums", [])[:10]]
        except:
            results[lang] = []
    return jsonify(results)

@app.route('/api/album/<id>')
def get_album(id):
    url = f"https://www.jiosaavn.com/api.php?__call=content.getAlbumDetails&albumid={id}&_format=json"
    data = requests.get(url).json()
    songs = [{
        "id": s["id"],
        "title": html.unescape(s["song"]),
        "image": s["image"].replace("150x150", "500x500"),
        "artist": s["singers"],
        "url": decrypt_url(s["encrypted_media_url"])
    } for s in data.get("songs", [])]
    return jsonify({"title": data["title"], "songs": songs})

@app.route('/api/search')
def search():
    query = request.args.get('q')
    url = f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&q={query}&n=20"
    res = requests.get(url).json().get("results", [])
    results = [{
        "id": s["id"],
        "title": html.unescape(s["title"]),
        "image": s["image"].replace("150x150", "500x500"),
        "artist": s["subtitle"],
        "url": decrypt_url(s["encrypted_media_url"]) if "encrypted_media_url" in s else ""
    } for s in res]
    return jsonify(results)
