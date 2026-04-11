import base64
import requests
import json
import re
from flask import Flask, render_template, request, jsonify
from pyDes import *
from traceback import print_exc

app = Flask(__name__)

# --- Configuration & Endpoints ---
search_base_url = "https://www.jiosaavn.com/api.php?__call=autocomplete.get&_format=json&_marker=0&cc=in&includeMetaTags=1&query="
song_details_base_url = "https://www.jiosaavn.com/api.php?__call=song.getDetails&cc=in&_marker=0%3F_marker%3D0&_format=json&pids="
lyrics_base_url = "https://www.jiosaavn.com/api.php?__call=lyrics.getLyrics&ctx=web6dot0&api_version=4&_format=json&_marker=0%3F_marker%3D0&lyrics_id="

# --- Helper Functions (Ningal thannathu) ---

def decrypt_url(url):
    des_cipher = des(b"38346591", ECB, b"\0\0\0\0\0\0\0\0", pad=None, padmode=PAD_PKCS5)
    enc_url = base64.b64decode(url.strip())
    dec_url = des_cipher.decrypt(enc_url, padmode=PAD_PKCS5).decode('utf-8')
    dec_url = dec_url.replace("_96.mp4", "_320.mp4")
    return dec_url

def format_string(string):
    return string.encode().decode().replace("&quot;", "'").replace("&amp;", "&").replace("&#039;", "'")

def format_song(data):
    try:
        if 'encrypted_media_url' in data:
            data['media_url'] = decrypt_url(data['encrypted_media_url'])
        
        # Audio URL quality handling
        if data.get('320kbps') != "true":
            data['media_url'] = data['media_url'].replace("_320.mp4", "_160.mp4")
            
        data['image'] = data['image'].replace("150x150", "500x500")
        data['song'] = format_string(data['song'])
        data['album'] = format_string(data['album'])
        data['singers'] = format_string(data['singers'])
    except Exception as e:
        print(f"Error formatting: {e}")
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
        response = requests.get(search_base_url + query).text.encode().decode('unicode-escape')
        # Clean pattern
        pattern = r'\(From "([^"]+)"\)'
        response = json.loads(re.sub(pattern, r"(From '\1')", response))
        
        songs_list = response['songs']['data']
        results = []
        
        for song in songs_list:
            # Fetching details for each song to get the encrypted URL
            song_id = song['id']
            details_res = requests.get(song_details_base_url + song_id).text.encode().decode('unicode-escape')
            details_json = json.loads(details_res)
            formatted = format_song(details_json[song_id])
            results.append(formatted)
            
        return jsonify(results)
    except Exception as e:
        print_exc()
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
    
