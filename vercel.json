from flask import Flask, request
import requests
import re
import json

app = Flask(__name__)

# Vercel serverless compatibility
def app_handler(request):
    return app(request)

def aotpy_shorten_url(url):
    if not url:
        return url
    try:
        response = requests.post(
            "https://freelyshrink.com/shorten.php",
            headers={
                "User-Agent": "Mozilla/5.0",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={"long_url": url},
            timeout=15
        )

        if "code=" in response.url:
            code = response.url.split("code=")[1].split("&")[0]
            return f"https://hosturl.link/{code}"

        match = re.search(r'code=([a-zA-Z0-9]+)', response.text)
        if match:
            return f"https://hosturl.link/{match.group(1)}"

    except:
        pass
    return url

@app.route('/api/yt')
def yt_downloader():
    link = request.args.get('link')
    
    if not link:
        return json.dumps({
            "status": 0,
            "error": "Missing link parameter"
        }), 400, {'Content-Type': 'application/json'}

    payload = {
        "url": "/media/parse",
        "data": {"origin": "source", "link": link},
        "token": ""
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android)",
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Origin": "https://vidssave.com",
        "Referer": "https://vidssave.com/yt"
    }

    try:
        session = requests.Session()
        session.get("https://vidssave.com/yt", headers=headers)
        response = session.post(
            "https://vidssave.com/api/proxy",
            headers=headers,
            json=payload,
            timeout=20
        )

        data = response.json()

        if data.get("status") != 1:
            return json.dumps({
                "status": 0,
                "error": "Invalid response from source"
            }), 500, {'Content-Type': 'application/json'}

        info = data["data"]
        output = []

        thumb = aotpy_shorten_url(info.get("thumbnail"))

        for resource in info.get("resources", []):
            if resource.get("download_mode") == "check_download":
                output.append({
                    "quality": resource.get("quality"),
                    "format": resource.get("format"),
                    "size": resource.get("size"),
                    "download": aotpy_shorten_url(resource.get("download_url"))
                })

        return json.dumps({
            "status": 1,
            "response": {
                "title": info.get("title"),
                "duration": info.get("duration"),
                "thumbnail": thumb,
                "data": output
            }
        }), 200, {'Content-Type': 'application/json'}

    except Exception as e:
        return json.dumps({
            "status": 0,
            "error": str(e)
        }), 500, {'Content-Type': 'application/json'}
