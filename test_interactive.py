import urllib.request
import urllib.error
import json
import uuid
import mimetypes

BASE_URL = "http://localhost:8000"

def encode_multipart_formdata(fields, files):
    boundary = uuid.uuid4().hex
    body = []
    for key, value in fields.items():
        body.extend([
            f'--{boundary}'.encode('utf-8'),
            f'Content-Disposition: form-data; name="{key}"'.encode('utf-8'),
            b'',
            value.encode('utf-8')
        ])
    for key, filepath in files.items():
        try:
            with open(filepath, 'rb') as f:
                file_content = f.read()
            filename = filepath.split('/')[-1].split('\\')[-1]
            mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            body.extend([
                f'--{boundary}'.encode('utf-8'),
                f'Content-Disposition: form-data; name="{key}"; filename="{filename}"'.encode('utf-8'),
                f'Content-Type: {mime_type}'.encode('utf-8'),
                b'',
                file_content
            ])
        except Exception as e:
            print(f"Error reading file {filepath}: {e}")
            return None, None
            
    body.append(f'--{boundary}--'.encode('utf-8'))
    body.append(b'')
    content_type = f'multipart/form-data; boundary={boundary}'
    return b'\r\n'.join(body), content_type

def analyze_text(transcript):
    url = f"{BASE_URL}/api/v1/analyze/text"
    data = json.dumps({
        "client_id": "test_client",
        "transcript": transcript
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, method="POST", headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode('utf-8'))

def analyze_audio(filepath):
    url = f"{BASE_URL}/api/v1/analyze/audio"
    body, content_type = encode_multipart_formdata({"client_id": "test_client"}, {"audio_file": filepath})
    
    if not body:
        return {"error": "Failed to load file"}
        
    req = urllib.request.Request(url, data=body, method="POST", headers={'Content-Type': content_type})
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode('utf-8'))


if __name__ == "__main__":
    print("=" * 50)
    print(" VAJRA PHASE 1 - INTERACTIVE TESTER ")
    print("=" * 50)
    
    while True:
        print("\nWhat would you like to test?")
        print("1. Text Transcript File Upload")
        print("2. Audio File Upload")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1/2/3): ").strip()
        
        if choice == '1':
            print("\n" + "-"*40)
            print("Enter the path to your text transcript file (e.g. transcript.txt)")
            filepath = input("> ").strip()
            
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception as e:
                print(f"⚠️  Error reading file: {e}")
                continue
                
            if len(text.strip()) < 10:
                print("⚠️  Error: Transcript in file must be at least 10 characters!")
                continue
                
            print(f"\nSending '{filepath}' to API...")
            result = analyze_text(text)
            
            print("\n" + "="*40)
            print("API RESPONSE:")
            print(json.dumps(result, indent=2))
            if result.get("language_detected"):
                print(f"\n💡 Detected Language Hint: '{result.get('language_detected')}'")
            print("="*40)
            
        elif choice == '2':
            print("\n" + "-"*40)
            print("Enter the path to your audio file (e.g. sample_call.mp3)")
            filepath = input("> ")
            
            print("\nSending to API...")
            result = analyze_audio(filepath)
            
            print("\n" + "="*40)
            print("API RESPONSE:")
            print(json.dumps(result, indent=2))
            print("="*40)
            
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Try again.")
