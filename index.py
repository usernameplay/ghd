import requests
import json
from flask import Flask, render_template, request, redirect
import html
import base64
from pyDes import *

des_cipher = des(b"38346591", ECB, b"\0\0\0\0\0\0\0\0", pad=None, padmode=PAD_PKCS5)

def check_audio(url):
    try:
        r = requests.get(url, timeout=5)
        return r.status_code
    except:
        return 404

def fix_title(title):
    return html.unescape(title).replace("&quot;", "")

def decrypt_url(url):
    enc_url = base64.b64decode(url.strip())
    dec_url = des_cipher.decrypt(enc_url, padmode=PAD_PKCS5).decode("utf-8")
    dec_url = dec_url.replace("_96.mp4", "_320.mp3")
    return dec_url

def fix_media_url(url):
    return url.replace("preview", "h").replace("_96_p.mp4", "_320.mp4")

app = Flask(__name__)

def fetch_albums(lang):
    try:
        cookies = {"L": lang}
        url = "https://www.jiosaavn.com/api.php?__call=content.getHomepageData"
        res = requests.get(url, cookies=cookies).text
        data = json.loads("{" + res.split("{", 1)[1])["new_albums"]
        albums = []
        for i in range(len(data)):
            albums.append({
                "name": html.unescape(data[i]["text"]),
                "year": data[i]["year"],
                "image": data[i]["image"].replace("150x150", "500x500"),
                "id": data[i]["albumid"]
            })
        return albums
    except:
        return []

@app.route("/")
def index():
    return redirect("/home")

@app.route("/home")
def home():
    mal_data = fetch_albums("malayalam")
    tam_data = fetch_albums("tamil")
    hin_data = fetch_albums("hindi")
    kan_data = fetch_albums("kannada")
    eng_data = fetch_albums("english")
    return render_template("home.html", mal=mal_data, tam=tam_data, hin=hin_data)

@app.route("/get_album")
def get_album_details():
    albumID = request.args.get("albumID")
    url = f"https://www.jiosaavn.com/api.php?__call=content.getAlbumDetails&albumid={albumID}"
    result = requests.get(url).text
    data = json.loads("{" + result.split("{", 1)[1])
    songs = data["songs"]
    songIDs, songImages, songNames = [], [], []
    for s in songs:
        songIDs.append(s["id"])
        songImages.append(s["image"].replace("150x150", "500x500"))
        songNames.append(html.unescape(s["song"]))
    return render_template("Album_Details.html", title=html.unescape(data["title"]), songNames=songNames, 
                           album_image=data["image"].replace("150x150", "500x500"), song_IDs=songIDs, song_covers=songImages, zip=zip)

@app.route("/play_song")
def play():
    songID = request.args.get("songID")
    url = f"https://www.jiosaavn.com/api.php?cc=in&_marker=0&_format=json&model=Redmi_5A&__call=song.getDetails&pids={songID}"
    res = requests.get(url).text
    data = json.loads("{" + res.split("{", 1)[1])[songID]
    
    mp3_url = ""
    try:
        mp3_url = fix_media_url(data["media_preview_url"])
        if check_audio(mp3_url) != 200:
            mp3_url = decrypt_url(data["encrypted_media_url"]).replace("mp3", "mp4")
    except:
        mp3_url = decrypt_url(data["encrypted_media_url"])

    return render_template("Play.html", song_name=fix_title(data["song"]), singers=data["singers"], 
                           year=data["year"], image=data["image"].replace("150x150", "500x500"), 
                           mp3_url=mp3_url, album_name=html.unescape(data["album"]))

@app.route("/search")
def search():
    query = request.args.get("songName", "")
    if not query: return render_template("search_results.html", songs_titles=[], songName="")
    url = f"https://www.jiosaavn.com/api.php?p=1&q={query}&_format=json&_marker=0&api_version=4&ctx=web6dot0&n=50&__call=search.getResults"
    r = requests.get(url).json()["results"]
    ids, imgs, titles, years = [], [], [], []
    for i in r:
        ids.append(i["id"]); imgs.append(i["image"].replace("150x150", "500x500"))
        titles.append(i["title"]); years.append(i["year"])
    return render_template("search_results.html", songIDs=ids, images=imgs, songs_titles=titles, years=years, songName=query, zip=zip)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

