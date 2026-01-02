from http.server import BaseHTTPRequestHandler
import json
import requests
import re
import urllib.parse
import time

def shorten_url(url):
    """URL shortening function"""
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
            timeout=10
        )
        
        if "code=" in response.url:
            code = response.url.split("code=")[1].split("&")[0]
            return f"https://hosturl.link/{code}"
        
        match = re.search(r'code=([a-zA-Z0-9]+)', response.text)
        if match:
            return f"https://hosturl.link/{match.group(1)}"
            
    except Exception as e:
        print(f"URL shortening error: {e}")
    
    return url

def get_youtube_data(link):
    """Fetch YouTube video data"""
    payload = {
        "url": "/media/parse",
        "data": {
            "origin": "source",
            "link": link
        },
        "token": ""
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-A505F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "Origin": "https://vidssave.com",
        "Referer": "https://vidssave.com/yt",
        "Connection": "keep-alive"
    }
    
    session = requests.Session()
    
    # First request to get cookies
    try:
        session.get("https://vidssave.com/yt", headers=headers, timeout=10)
        time.sleep(1)  # Small delay
        
        # Main request
        response = session.post(
            "https://vidssave.com/api/proxy",
            headers=headers,
            json=payload,
            timeout=15
        )
        
        return response.json()
        
    except requests.exceptions.Timeout:
        return {"status": 0, "error": "Request timeout"}
    except Exception as e:
        return {"status": 0, "error": str(e)}

def handler(event, context):
    """Main handler function for Vercel"""
    try:
        # Parse query parameters
        query_params = event.get('queryStringParameters', {})
        link = query_params.get('link')
        
        if not link:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                },
                'body': json.dumps({
                    "status": 0,
                    "error": "Missing link parameter"
                })
            }
        
        # Get YouTube data
        data = get_youtube_data(link)
        
        if data.get("status") != 1:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    "status": 0,
                    "error": data.get("error", "Invalid response from source")
                })
            }
        
        info = data.get("data", {})
        downloads = []
        
        # Shorten thumbnail URL
        thumbnail = shorten_url(info.get("thumbnail", ""))
        
        # Process download links
        for resource in info.get("resources", []):
            if resource.get("download_mode") == "check_download":
                download_url = shorten_url(resource.get("download_url", ""))
                if download_url:
                    downloads.append({
                        "quality": resource.get("quality", "N/A"),
                        "format": resource.get("format", "mp4"),
                        "size": resource.get("size", "N/A"),
                        "download": download_url
                    })
        
        # Prepare response
        response_data = {
            "status": 1,
            "response": {
                "title": info.get("title", ""),
                "duration": info.get("duration", ""),
                "thumbnail": thumbnail,
                "data": downloads
            }
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps(response_data, indent=2)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                "status": 0,
                "error": f"Server error: {str(e)}"
            })
        }

# For local testing
if __name__ == "__main__":
    # Test the function locally
    test_event = {
        'queryStringParameters': {
            'link': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        }
    }
    result = handler(test_event, None)
    print(json.dumps(result, indent=2))
