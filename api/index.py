import base64
import requests
import json
import re
from flask import Flask, render_template, request, jsonify
from pyDes import *
from traceback import print_exc

app = Flask(__name__, template_folder='../templates')

# --- JioSaavn Endpoints ---
search_base_url = "https://www.jiosaavn.com/api.php?__call=autocomplete.get&_format=json&_marker=0&cc=in&includeMetaTags=1&query="
song_details_base_url = "https://www.jiosaavn.com/api.php?__call=song.getDetails&cc=in&_marker=0%3F_marker%3D0&_format=json&pids="

# --- Helper Functions ---
def decrypt_url(url):
    try:
        des_cipher = des(b"38346591", ECB, b"\0\0\0\0\0\0\0\0", pad=None, padmode=PAD_PKCS5)
        enc_url = base64.b64decode(url.strip())
        dec_url = des_cipher.decrypt(enc_url, padmode=PAD_PKCS5).decode('utf-8')
        dec_url = dec_url.replace("_96.mp4", "_320.mp4")
        return dec_url
    except:
        return None

def format_string(string):
    if not string: return ""
    return string.encode().decode().replace("&quot;", "'").replace("&amp;", "&").replace("&#039;", "'")

def format_song(data):
    try:
        if 'encrypted_media_url' in data:
            data['media_url'] = decrypt_url(data['encrypted_media_url'])
        
        if data.get('320kbps') != "true" and 'media_url' in data:
            data['media_url'] = data['media_url'].replace("_320.mp4", "_160.mp4")
            
        data['image'] = data['image'].replace("150x150", "500x500")
        data['song'] = format_string(data.get('song', 'Unknown'))
        data['album'] = format_string(data.get('album', 'Unknown'))
        data['singers'] = format_string(data.get('singers', 'Unknown'))
    except Exception as e:
        print(f"Error: {e}")
    return data

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    query = request.args.get('query')
    if not query:
        return jsonify([])
    
    try:
        res = requests.get(search_base_url + query).text.encode().decode('unicode-escape')
        pattern = r'\(From "([^"]+)"\)'
        clean_res = json.loads(re.sub(pattern, r"(From '\1')", res))
        
        songs_list = clean_res.get('songs', {}).get('data', [])
        results = []
        
        for song in songs_list:
            song_id = song['id']
            # Detailed fetch to get media URL
            d_res = requests.get(song_details_base_url + song_id).text.encode().decode('unicode-escape')
            d_json = json.loads(d_res)
            results.append(format_song(d_json[song_id]))
            
        return jsonify(results)
    except:
        print_exc()
        return jsonify([])

# Vercel handler
app = app
      
