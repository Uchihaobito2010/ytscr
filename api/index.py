from flask import Flask, request
from flask_cors import CORS
import requests
import re

app = Flask(__name__)
CORS(app)

def aotpy_shorten_url(aotpyurl):
    if not aotpyurl:
        return aotpyurl
    try:
        aotpyres = requests.post(
            "https://freelyshrink.com/shorten.php",
            headers={
                "User-Agent": "Mozilla/5.0",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={"long_url": aotpyurl},
            timeout=15
        )

        if "code=" in aotpyres.url:
            aotpycode = aotpyres.url.split("code=")[1].split("&")[0]
            return f"https://hosturl.link/{aotpycode}"

        aotpymatch = re.search(r'code=([a-zA-Z0-9]+)', aotpyres.text)
        if aotpymatch:
            return f"https://hosturl.link/{aotpymatch.group(1)}"

    except:
        pass

    return aotpyurl


@app.route("/api/yt", methods=["GET"])
def aotpy_api():
    aotpylink = request.args.get("link")

    if not aotpylink:
        return {
            "status": 0,
            "error": "Missing link parameter"
        }, 400

    aotpypayload = {
        "url": "/media/parse",
        "data": {
            "origin": "source",
            "link": aotpylink
        },
        "token": ""
    }

    aotpyheaders = {
        "User-Agent": "Mozilla/5.0 (Linux; Android)",
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Origin": "https://vidssave.com",
        "Referer": "https://vidssave.com/yt"
    }

    try:
        aotpysession = requests.Session()
        aotpysession.get("https://vidssave.com/yt", headers=aotpyheaders)
        aotpyres = aotpysession.post(
            "https://vidssave.com/api/proxy",
            headers=aotpyheaders,
            json=aotpypayload,
            timeout=20
        )

        aotpydata = aotpyres.json()

        if aotpydata.get("status") != 1:
            return {
                "status": 0,
                "error": "Invalid response from source"
            }, 500

        aotpyinfo = aotpydata["data"]
        aotpyout = []

        aotpythumb = aotpyinfo.get("thumbnail")
        aotpythumb = aotpy_shorten_url(aotpythumb)

        for aotpyrsc in aotpyinfo.get("resources", []):
            if aotpyrsc.get("download_mode") == "check_download":
                aotpyout.append({
                    "quality": aotpyrsc.get("quality"),
                    "format": aotpyrsc.get("format"),
                    "size": aotpyrsc.get("size"),
                    "download": aotpy_shorten_url(aotpyrsc.get("download_url"))
                })

        return {
            "status": 1,
            "response": {
                "title": aotpyinfo.get("title"),
                "duration": aotpyinfo.get("duration"),
                "thumbnail": aotpythumb,
                "data": aotpyout
            }
        }

    except Exception as aotpye:
        return {
            "status": 0,
            "error": str(aotpye)
        }, 500


# Vercel के लिए handler function
def handler(event, context):
    from flask import Flask
    import app as flask_app
    
    return flask_app.app(event, context)

if __name__ == "__main__":
    app.run()
