from http.server import BaseHTTPRequestHandler
import json
import requests
import re
import urllib.parse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse the path and query parameters
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)
        
        # Get the 'link' parameter
        link = query_params.get('link', [None])[0]
        
        if not link:
            self.send_error_response(400, "Missing link parameter")
            return
        
        try:
            result = self.process_youtube_link(link)
            self.send_success_response(result)
        except Exception as e:
            self.send_error_response(500, str(e))
    
    def process_youtube_link(self, link):
        """Process YouTube link and return download info"""
        
        # Shorten URL function
        def shorten_url(url):
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
        
        # Prepare request to vidssave
        payload = {
            "url": "/media/parse",
            "data": {
                "origin": "source",
                "link": link
            },
            "token": ""
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-A505F) AppleWebKit/537.36",
            "Accept": "*/*",
            "Content-Type": "application/json",
            "Origin": "https://vidssave.com",
            "Referer": "https://vidssave.com/yt",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive"
        }
        
        # Make the request
        session = requests.Session()
        session.get("https://vidssave.com/yt", headers=headers, timeout=10)
        
        response = session.post(
            "https://vidssave.com/api/proxy",
            headers=headers,
            json=payload,
            timeout=20
        )
        
        data = response.json()
        
        if data.get("status") != 1:
            raise Exception("Invalid response from source")
        
        info = data["data"]
        
        # Process response
        thumbnail = shorten_url(info.get("thumbnail", ""))
        
        downloads = []
        for resource in info.get("resources", []):
            if resource.get("download_mode") == "check_download":
                downloads.append({
                    "quality": resource.get("quality", ""),
                    "format": resource.get("format", ""),
                    "size": resource.get("size", ""),
                    "download": shorten_url(resource.get("download_url", ""))
                })
        
        return {
            "title": info.get("title", ""),
            "duration": info.get("duration", ""),
            "thumbnail": thumbnail,
            "data": downloads
        }
    
    def send_success_response(self, data):
        """Send successful response"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        response = json.dumps({
            "status": 1,
            "response": data
        })
        self.wfile.write(response.encode())
    
    def send_error_response(self, code, message):
        """Send error response"""
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = json.dumps({
            "status": 0,
            "error": message
        })
        self.wfile.write(response.encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
