#!/usr/bin/env python3
"""
Local server for Viser AI to proxy AI requests and serve the standalone UI.
"""

import json
import os
import time
import random
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.error
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Basic config - loads from environment variables
CONFIG = {
    "owner_name": os.getenv("OWNER_NAME", "Vishnu"),
    "USE_OPENAI": os.getenv("USE_OPENAI", "False").lower() == "true",
    "USE_FALLBACK": os.getenv("USE_FALLBACK", "False").lower() == "true",
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
    "GROQ_API_KEY": os.getenv("GROQ_API_KEY", ""),
    "GROQ_MODEL": os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
}


class ViserAIHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def _json(self, status: int, data: dict):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_OPTIONS(self):
        self._json(200, {"ok": True})

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            return self._serve_file('viser-ai-modern.html', 'text/html')
        if self.path.endswith('.html'):
            return self._serve_file(self.path.lstrip('/'), 'text/html')
        if self.path.endswith('.js'):
            return self._serve_file(self.path.lstrip('/'), 'application/javascript')
        if self.path.endswith('.css'):
            return self._serve_file(self.path.lstrip('/'), 'text/css')
        self.send_error(404)

    def _serve_file(self, path: str, content_type: str):
        try:
            with open(path, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404)

    def do_POST(self):
        print(f"🌐 POST request received: {self.path}")
        print(f"📊 Headers: {dict(self.headers)}")
        
        length = int(self.headers.get('Content-Length', '0'))
        print(f"📏 Content-Length: {length}")
        
        if length > 0:
            print(f"📖 Reading {length} bytes...")
            post_data = self.rfile.read(length)
            print(f"✅ Read {len(post_data)} bytes successfully")
        else:
            post_data = b''
            print("📭 No POST data to read")

        if self.path == "/api/chat":
            try:
                print(f"📨 Received chat request")
                data = json.loads(post_data.decode("utf-8"))
                user_message = data.get("message", "")
                print(f"💬 User message: {user_message[:100]}...")

                if not user_message:
                    print("❌ No message provided")
                    self._set_headers(400)
                    self.wfile.write(json.dumps({"error": "No message provided"}).encode("utf-8"))
                    return

                # Check if using fallback mode
                if CONFIG.get('USE_FALLBACK', False):
                    ai_response = self._fallback(user_message)
                    self._set_headers()
                    self.wfile.write(json.dumps({"response": ai_response}).encode("utf-8"))
                    return

                # --- API call for chat (OpenAI or Groq based on config) ---
                if CONFIG.get('USE_OPENAI', False):
                    headers = {
                        "Authorization": f"Bearer {CONFIG['OPENAI_API_KEY']}",
                        "Content-Type": "application/json"
                    }
                    api_url = "https://api.openai.com/v1/chat/completions"
                    model = "gpt-3.5-turbo"
                else:
                    headers = {
                        "Authorization": f"Bearer {CONFIG['GROQ_API_KEY']}",
                        "Content-Type": "application/json"
                    }
                    api_url = "https://api.groq.com/openai/v1/chat/completions"
                    model = CONFIG.get("GROQ_MODEL", "llama-3.1-8b-instant")

                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are Viser AI, an intelligent AI assistant specialized in document analysis, project management, and deliverable generation. You help users with business requirements documents, timelines, budgets, and other project-related tasks."},
                        {"role": "user", "content": user_message}
                    ],
                    "temperature": 0.6,
                    "max_tokens": 800
                }

                print(f"🔄 Making API call to {api_url}...")
                print(f"🔑 Using API key: {headers['Authorization'][:20]}...")
                print(f"📦 Payload: {json.dumps(payload, indent=2)}")
                
                try:
                    response = requests.post(api_url, headers=headers, json=payload, timeout=15)  # Reduced timeout
                    print(f"📊 API Response Status: {response.status_code}")
                except requests.exceptions.Timeout:
                    print("⏰ API request timed out")
                    raise
                except requests.exceptions.RequestException as e:
                    print(f"🚫 API request failed: {e}")
                    raise
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result["choices"][0]["message"]["content"]
                    print(f"✅ AI Response generated: {len(ai_response)} characters")
                    self._set_headers()
                    self.wfile.write(json.dumps({"response": ai_response}).encode("utf-8"))
                else:
                    # API call failed, provide detailed error
                    error_msg = f"API Error {response.status_code}: {response.text}"
                    print(f"❌ API Error: {error_msg}")
                    self._set_headers(500)
                    self.wfile.write(json.dumps({
                        "error": error_msg,
                        "status_code": response.status_code
                    }).encode("utf-8"))

            except requests.exceptions.RequestException as e:
                # Network/API errors
                error_msg = f"API request failed: {str(e)}"
                self._set_headers(500)
                self.wfile.write(json.dumps({
                    "error": error_msg,
                    "type": "network_error"
                }).encode("utf-8"))
            except Exception as e:
                # Other unexpected errors
                self._set_headers(500)
                self.wfile.write(json.dumps({
                    "error": f"Unexpected error: {str(e)}",
                    "trace": traceback.format_exc()
                }).encode("utf-8"))

        elif self.path == "/api/upload":
            try:
                print("📤 Received upload request")
                
                content_length = int(self.headers.get('Content-Length', 0))
                content_type = self.headers.get('Content-Type', '')
                
                print(f"📊 Content-Length: {content_length}")
                print(f"📊 Content-Type: {content_type}")
                
                if content_length == 0:
                    print("❌ No file content provided")
                    self._set_headers(400)
                    self.wfile.write(json.dumps({"error": "No file content provided"}).encode("utf-8"))
                    return

                # Read the raw POST data
                print("📖 Reading POST data...")
                post_data = self.rfile.read(content_length)
                print(f"📊 Read {len(post_data)} bytes")
                
                # Use a much simpler multipart parsing approach
                if 'multipart/form-data' in content_type:
                    print("🔍 Parsing multipart data...")
                    
                    # Extract boundary
                    boundary = content_type.split('boundary=')[1].strip()
                    print(f"🔍 Boundary: {boundary}")
                    
                    # Simple approach: find the file content between boundaries
                    file_data = None
                    filename = "uploaded_file.txt"
                    
                    # Convert to string for easier processing
                    data_str = post_data.decode('utf-8', errors='ignore')
                    
                    # Look for filename in Content-Disposition
                    if 'filename=' in data_str:
                        try:
                            filename_start = data_str.find('filename="') + 10
                            filename_end = data_str.find('"', filename_start)
                            if filename_end > filename_start:
                                filename = data_str[filename_start:filename_end]
                                print(f"📄 Found filename: {filename}")
                        except:
                            print("📄 Using default filename")
                    
                    # Find the actual file content (after double newline)
                    # Look for the pattern that separates headers from content
                    content_start = post_data.find(b'\r\n\r\n')
                    if content_start == -1:
                        content_start = post_data.find(b'\n\n')
                    
                    if content_start != -1:
                        # Start after the double newline
                        content_start += 4 if b'\r\n\r\n' in post_data else 2
                        
                        # Find the end boundary
                        boundary_bytes = f'--{boundary}'.encode()
                        content_end = post_data.find(boundary_bytes, content_start)
                        
                        if content_end != -1:
                            file_data = post_data[content_start:content_end]
                            # Remove trailing newlines
                            file_data = file_data.rstrip(b'\r\n')
                            print(f"📊 Extracted {len(file_data)} bytes of file data")
                        else:
                            print("❌ Could not find end boundary")
                    else:
                        print("❌ Could not find content separator")
                        
                    if not file_data:
                        print("❌ No file data extracted")
                        self._set_headers(400)
                        self.wfile.write(json.dumps({"error": "Could not extract file data"}).encode("utf-8"))
                        return
                        
                else:
                    # Not multipart, treat as raw file
                    file_data = post_data
                    filename = f"uploaded_file_{int(time.time())}.txt"
                    print(f"📄 Using raw data, filename: {filename}")
                
                # Validate file data
                if not file_data or len(file_data) == 0:
                    print("❌ Empty file data")
                    self._set_headers(400)
                    self.wfile.write(json.dumps({"error": "Empty file data"}).encode("utf-8"))
                    return
                
                print("💾 Saving file...")
                
                # Create uploads directory if it doesn't exist
                upload_dir = "uploads"
                os.makedirs(upload_dir, exist_ok=True)
                
                # Generate unique filename
                import uuid
                file_id = str(uuid.uuid4())
                file_extension = os.path.splitext(filename)[1] if '.' in filename else '.txt'
                unique_filename = f"{file_id}{file_extension}"
                file_path = os.path.join(upload_dir, unique_filename)
                
                # Save the file
                with open(file_path, 'wb') as f:
                    f.write(file_data)
                
                print(f"✅ Upload successful: {filename} -> {unique_filename} ({len(file_data)} bytes)")
                
                # Send success response
                self._set_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "message": f"File uploaded successfully: {filename}",
                    "fileId": file_id,
                    "filename": filename,
                    "size": len(file_data),
                    "path": file_path
                }).encode("utf-8"))
                
            except Exception as e:
                print(f"❌ Upload error: {str(e)}")
                import traceback
                traceback.print_exc()
                self._set_headers(500)
                self.wfile.write(json.dumps({
                    "error": f"Upload failed: {str(e)}"
                }).encode("utf-8"))

        elif self.path == "/api/analyze":
            try:
                data = json.loads(post_data.decode("utf-8"))
                filename = data.get("filename")
                file_path = data.get("file_path")  # Add file path support

                # If file_path is provided, read the actual file content
                if file_path and os.path.exists(file_path):
                    try:
                        # Handle different file types
                        if filename.endswith('.docx'):
                            content = self._extract_docx_content(file_path)
                        elif filename.endswith('.txt'):
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                        elif filename.endswith('.pdf'):
                            content = self._extract_pdf_content(file_path)
                        else:
                            # For other file types, try to read as text
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                    except Exception as e:
                        content = f"Error reading file content: {str(e)}"
                else:
                    # Fallback to provided content
                    content = data.get("content", "")
                    if not content:
                        self._set_headers(400)
                        self.wfile.write(json.dumps({"error": "No file content or file path provided"}).encode("utf-8"))
                        return

                # Check if using fallback mode
                if CONFIG.get('USE_FALLBACK', False):
                    # Create mock file data for fallback
                    mock_files = [{"name": filename, "size": len(content), "type": "text/plain"}]
                    ai_response = self._fallback_analysis(mock_files)
                    self._set_headers()
                    self.wfile.write(json.dumps({"filename": filename, "analysis": ai_response}).encode("utf-8"))
                    return

                # Build optimized analysis prompt
                # Limit content length to prevent timeouts
                max_content_length = 8000  # Reduced from unlimited
                if len(content) > max_content_length:
                    content = content[:max_content_length] + "\n\n[Content truncated for analysis - document is very large]"
                
                prompt = f"""
You are Viser AI, an expert document analyst. Analyze this document thoroughly but concisely.

Filename: {filename}

Document Content:
{content}

Provide a comprehensive analysis covering:

## 1. DOCUMENT OVERVIEW
- Primary purpose and target audience
- Document type and main topics

## 2. KEY CONTENT & CONCEPTS
- Major topics and concepts covered
- Important methodologies or frameworks
- Tools and technologies mentioned

## 3. TECHNICAL DETAILS
- Requirements and dependencies
- Configuration options
- Code examples or snippets

## 4. PRACTICAL INFORMATION
- Step-by-step processes
- Best practices and recommendations
- Troubleshooting guidance

## 5. SUMMARY & NEXT STEPS
- Key takeaways
- Actionable recommendations
- Important considerations

Be thorough but concise. Focus on the most important and useful information.
"""

                # --- API call for analysis (OpenAI or Groq based on config) ---
                if CONFIG.get('USE_OPENAI', False):
                    headers = {
                        "Authorization": f"Bearer {CONFIG['OPENAI_API_KEY']}",
                        "Content-Type": "application/json"
                    }
                    api_url = "https://api.openai.com/v1/chat/completions"
                    model = "gpt-3.5-turbo"
                else:
                    headers = {
                        "Authorization": f"Bearer {CONFIG['GROQ_API_KEY']}",
                        "Content-Type": "application/json"
                    }
                    api_url = "https://api.groq.com/openai/v1/chat/completions"
                    model = CONFIG.get("GROQ_MODEL", "llama-3.1-8b-instant")

                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are Viser AI, an expert document analyst. Provide clear, comprehensive analysis."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000   # Reduced for faster response
                }

                print(f"🔄 Making analysis API call to {api_url}...")
                print(f"🔑 Using API key: {headers['Authorization'][:20]}...")
                print(f"📦 Analysis payload size: {len(str(payload))} characters")
                
                try:
                    response = requests.post(api_url, headers=headers, json=payload, timeout=15)  # Reduced timeout
                    print(f"📊 Analysis API Response Status: {response.status_code}")
                except requests.exceptions.Timeout:
                    print("⏰ Analysis API request timed out")
                    raise
                except requests.exceptions.RequestException as e:
                    print(f"🚫 Analysis API request failed: {e}")
                    raise
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result["choices"][0]["message"]["content"]
                    self._set_headers()
                    self.wfile.write(json.dumps({
                        "filename": filename,
                        "analysis": ai_response
                    }).encode("utf-8"))
                else:
                    # API call failed, provide detailed error
                    error_msg = f"Analysis API Error {response.status_code}: {response.text}"
                    self._set_headers(500)
                    self.wfile.write(json.dumps({
                        "error": error_msg,
                        "status_code": response.status_code
                    }).encode("utf-8"))

            except requests.exceptions.RequestException as e:
                # Network/API errors
                error_msg = f"Analysis API request failed: {str(e)}"
                self._set_headers(500)
                self.wfile.write(json.dumps({
                    "error": error_msg,
                    "type": "network_error"
                }).encode("utf-8"))
            except Exception as e:
                # Other unexpected errors
                self._set_headers(500)
                self.wfile.write(json.dumps({
                    "error": f"Analysis error: {str(e)}",
                    "trace": traceback.format_exc()
                }).encode("utf-8"))

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode("utf-8"))


    def _call_openai(self, message: str) -> str:
        # Basic throttle
        if not hasattr(self.server, 'last_openai'): self.server.last_openai = 0.0
        gap = 5.0 - (time.time() - self.server.last_openai)
        if gap > 0: time.sleep(gap)

        url = 'https://api.openai.com/v1/chat/completions'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {CONFIG["OPENAI_API_KEY"]}'
        }
        payload = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {'role': 'system', 'content': 'You are Viser AI, an e-commerce BI assistant.'},
                {'role': 'user', 'content': message}
            ],
            'max_tokens': 300,
            'temperature': 0.7
        }
        body = json.dumps(payload).encode('utf-8')

        backoff = 2.0
        for attempt in range(5):
            try:
                req = urllib.request.Request(url, data=body, headers=headers)
                with urllib.request.urlopen(req, timeout=30) as resp:
                    self.server.last_openai = time.time()
                    data = json.loads(resp.read().decode('utf-8'))
                    return data['choices'][0]['message']['content']
            except urllib.error.HTTPError as e:
                text = ''
                try: text = e.read().decode('utf-8', 'ignore')
                except Exception: pass
                if e.code == 429:
                    if 'quota' in text.lower():
                        return 'OpenAI quota exceeded for this key. Provide another key or try later.'
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                return f'OpenAI error ({e.code}). Please try again.'
            except Exception as e:
                return f'OpenAI error: {e}'
        return 'OpenAI is rate limiting now. Try again shortly.'



    def _fallback(self, message: str) -> str:
        return "Viser AI fallback: Please provide your data files or a specific BI question."

    def _fallback_analysis(self, files) -> str:
        names = ", ".join([f.get('name', 'file') for f in files])
        return (
            f"Analysis for: {names}\n"
            "- Pricing conflicts: 3\n- Inventory discrepancies: 2\n- KPIs to monitor: AOV, CTR, Sell-through\n"
            "Actions: standardize descriptions, adjust prices, restock fast movers."
        )

    def _extract_docx_content(self, file_path):
        """Extract text content from .docx files"""
        try:
            from docx import Document
            doc = Document(file_path)
            content = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    content.append(paragraph.text.strip())
            return '\n'.join(content)
        except ImportError:
            return "Error: python-docx library not installed. Cannot read .docx files."
        except Exception as e:
            return f"Error reading .docx file: {str(e)}"

    def _extract_pdf_content(self, file_path):
        """Extract text content from PDF files"""
        try:
            import PyPDF2
            content = []
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    content.append(page.extract_text())
            return '\n'.join(content)
        except ImportError:
            return "Error: PyPDF2 library not installed. Cannot read PDF files."
        except Exception as e:
            return f"Error reading PDF file: {str(e)}"


def run(port=8000):
    server = HTTPServer(('', port), ViserAIHandler)
    print(f"Viser AI Server running at http://localhost:{port}")
    provider = 'OpenAI' if CONFIG.get('USE_OPENAI') else 'GROQ' if not CONFIG.get('USE_FALLBACK') else 'Fallback'
    print(f"AI Provider: {provider}")
    if not CONFIG.get('USE_OPENAI') and not CONFIG.get('USE_FALLBACK'):
        print("ℹ️  Using Groq API (OpenAI quota exceeded)")
    print("Press Ctrl+C to stop the server")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
        server.server_close()


if __name__ == '__main__':
    run()


