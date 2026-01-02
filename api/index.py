from http.server import BaseHTTPRequestHandler
import json
import requests
import re

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse query parameters
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        
        link = query_params.get('link', [None])[0]
        
        if not link:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({
                "status": 0,
                "error": "Missing link parameter"
            })
            self.wfile.write(response.encode())
            return

        # URL shortening function
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

        # Main API logic
        try:
            aotpypayload = {
                "url": "/media/parse",
                "data": {
                    "origin": "source",
                    "link": link
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
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = json.dumps({
                    "status": 0,
                    "error": "Invalid response from source"
                })
                self.wfile.write(response.encode())
                return

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

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({
                "status": 1,
                "response": {
                    "title": aotpyinfo.get("title"),
                    "duration": aotpyinfo.get("duration"),
                    "thumbnail": aotpythumb,
                    "data": aotpyout
                }
            })
            self.wfile.write(response.encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({
                "status": 0,
                "error": str(e)
            })
            self.wfile.write(response.encode())
