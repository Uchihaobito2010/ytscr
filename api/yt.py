import json
import requests
import re

def handler(event, context):
    # Parse query parameters
    query = event.get('queryStringParameters', {})
    link = query.get('link', '') if query else ''
    
    if not link:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 0,
                'error': 'Missing link parameter. Use: /api/yt?link=YOUTUBE_URL'
            })
        }
    
    try:
        # URL shortener function
        def shorten_url(url):
            if not url or not isinstance(url, str):
                return url
            try:
                response = requests.post(
                    "https://freelyshrink.com/shorten.php",
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    data={"long_url": url},
                    timeout=5
                )
                
                if response.status_code == 200:
                    if "code=" in response.url:
                        code = response.url.split("code=")[1].split("&")[0]
                        return f"https://hosturl.link/{code}"
                    
                    match = re.search(r'code=([a-zA-Z0-9]+)', response.text)
                    if match:
                        return f"https://hosturl.link/{match.group(1)}"
            except Exception as e:
                print(f"Shorten error: {e}")
            return url
        
        # Prepare request to vidssave
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Origin": "https://vidssave.com",
            "Referer": "https://vidssave.com/yt",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive"
        }
        
        payload = {
            "url": "/media/parse",
            "data": {
                "origin": "source",
                "link": link
            },
            "token": ""
        }
        
        # Make API request
        session = requests.Session()
        session.headers.update(headers)
        
        # Get initial cookies
        session.get("https://vidssave.com/yt", timeout=5)
        
        # Make main request
        response = session.post(
            "https://vidssave.com/api/proxy",
            json=payload,
            timeout=10
        )
        
        # Parse response
        if response.status_code != 200:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'status': 0,
                    'error': f'API returned status {response.status_code}'
                })
            }
        
        data = response.json()
        
        if data.get('status') != 1:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'status': 0,
                    'error': 'Invalid response from video source'
                })
            }
        
        info = data.get('data', {})
        
        # Prepare result
        downloads = []
        thumbnail = shorten_url(info.get('thumbnail', ''))
        
        for resource in info.get('resources', []):
            if resource.get('download_mode') == 'check_download':
                download_url = resource.get('download_url', '')
                if download_url:
                    downloads.append({
                        'quality': resource.get('quality', 'Unknown'),
                        'format': resource.get('format', 'mp4'),
                        'size': resource.get('size', 'N/A'),
                        'download': shorten_url(download_url)
                    })
        
        result = {
            'status': 1,
            'response': {
                'title': info.get('title', ''),
                'duration': info.get('duration', ''),
                'thumbnail': thumbnail,
                'data': downloads
            }
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result, indent=2)
        }
        
    except requests.exceptions.Timeout:
        return {
            'statusCode': 504,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 0,
                'error': 'Request timeout. Please try again.'
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 0,
                'error': f'Server error: {str(e)}'
            })
        }
