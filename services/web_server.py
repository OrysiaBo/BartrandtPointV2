#!/usr/bin/env python3
"""
Web Server für Remote-Präsentationen auf Tablet/Smartphone
Bertrandt Dynamic Messe Stand V4 - Remote Display Service
"""

import threading
import time
import json
import os
import base64
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs
from PIL import Image
from io import BytesIO

from core.logger import logger
from models.content import content_manager

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Multi-threaded HTTP Server"""
    daemon_threads = True
    allow_reuse_address = True

class PresentationRequestHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler für Präsentations-Streaming"""
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            query_params = parse_qs(parsed_path.query)
            
            if path == '/':
                self.serve_presentation_page()
            elif path == '/api/current_slide':
                self.serve_current_slide_data()
            elif path == '/api/slide':
                slide_id = int(query_params.get('id', [1])[0])
                self.serve_slide_data(slide_id)
            elif path == '/api/slides_list':
                self.serve_slides_list()
            elif path == '/static/style.css':
                self.serve_css()
            elif path == '/static/script.js':
                self.serve_javascript()
            elif path.startswith('/api/image/'):
                # Serve slide images
                image_path = path.replace('/api/image/', '')
                self.serve_image(image_path)
            elif path == '/api/control':
                # For receiving control commands from tablet
                self.handle_control_command(query_params)
            else:
                self.send_404()
                
        except Exception as e:
            logger.error(f"Error handling GET request: {e}")
            self.send_500()
    
    def do_POST(self):
        """Handle POST requests for slide control"""
        try:
            if self.path == '/api/control':
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length).decode('utf-8')
                command_data = json.loads(post_data)
                self.handle_control_command_post(command_data)
            else:
                self.send_404()
        except Exception as e:
            logger.error(f"Error handling POST request: {e}")
            self.send_500()
    
    def serve_presentation_page(self):
        """Serve the main presentation HTML page"""
        html_content = self.get_presentation_html()
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(html_content.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def serve_current_slide_data(self):
        """Serve current slide data as JSON"""
        try:
            current_slide_id = getattr(web_server, 'current_slide_id', 1)
            slide = content_manager.get_slide(current_slide_id)
            
            if slide:
                slide_data = {
                    'slide_id': current_slide_id,
                    'title': slide.title,
                    'content': slide.content,
                    'total_slides': content_manager.get_slide_count(),
                    'timestamp': datetime.now().isoformat()
                }
                
                # Add canvas elements if available
                if hasattr(slide, 'extra_data') and slide.extra_data:
                    canvas_elements = slide.extra_data.get('canvas_elements', [])
                    # Convert image paths to web-accessible URLs
                    for element in canvas_elements:
                        if element['type'] == 'image' and 'relative_path' in element:
                            element['web_url'] = f"/api/image/{element['relative_path']}"
                    
                    slide_data['canvas_elements'] = canvas_elements
                
                response = json.dumps(slide_data, ensure_ascii=False)
            else:
                response = json.dumps({'error': 'Slide not found'})
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response.encode('utf-8'))))
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error serving current slide data: {e}")
            self.send_500()
    
    def serve_slide_data(self, slide_id):
        """Serve specific slide data"""
        try:
            slide = content_manager.get_slide(slide_id)
            
            if slide:
                slide_data = {
                    'slide_id': slide_id,
                    'title': slide.title,
                    'content': slide.content,
                    'total_slides': content_manager.get_slide_count(),
                    'timestamp': datetime.now().isoformat()
                }
                
                # Add canvas elements if available
                if hasattr(slide, 'extra_data') and slide.extra_data:
                    canvas_elements = slide.extra_data.get('canvas_elements', [])
                    # Convert image paths to web-accessible URLs
                    for element in canvas_elements:
                        if element['type'] == 'image' and 'relative_path' in element:
                            element['web_url'] = f"/api/image/{element['relative_path']}"
                    
                    slide_data['canvas_elements'] = canvas_elements
                
                response = json.dumps(slide_data, ensure_ascii=False)
            else:
                response = json.dumps({'error': 'Slide not found'})
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error serving slide {slide_id}: {e}")
            self.send_500()
    
    def serve_slides_list(self):
        """Serve list of all slides"""
        try:
            slides = content_manager.get_all_slides()
            slides_list = []
            
            for slide_id, slide in slides.items():
                slides_list.append({
                    'slide_id': slide_id,
                    'title': slide.title,
                    'content': slide.content[:100] + "..." if len(slide.content) > 100 else slide.content
                })
            
            response = json.dumps({
                'slides': slides_list,
                'total': len(slides_list),
                'current': getattr(web_server, 'current_slide_id', 1)
            }, ensure_ascii=False)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error serving slides list: {e}")
            self.send_500()
    
    def serve_image(self, image_path):
        """Serve slide images"""
        try:
            full_path = os.path.join("data", "images", image_path)
            
            if os.path.exists(full_path):
                with open(full_path, 'rb') as f:
                    image_data = f.read()
                
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.send_header('Content-Length', str(len(image_data)))
                self.send_header('Cache-Control', 'max-age=3600')
                self.end_headers()
                self.wfile.write(image_data)
            else:
                self.send_404()
                
        except Exception as e:
            logger.error(f"Error serving image {image_path}: {e}")
            self.send_500()
    
    def handle_control_command(self, query_params):
        """Handle control commands from tablet via GET"""
        try:
            action = query_params.get('action', [''])[0]
            
            if action == 'next':
                web_server.next_slide()
            elif action == 'prev':
                web_server.previous_slide()
            elif action == 'goto':
                slide_id = int(query_params.get('slide', [1])[0])
                web_server.goto_slide(slide_id)
            elif action == 'play':
                web_server.start_demo()
            elif action == 'stop':
                web_server.stop_demo()
            
            # Return success response
            response = json.dumps({'status': 'success', 'action': action})
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error handling control command: {e}")
            self.send_500()
    
    def handle_control_command_post(self, command_data):
        """Handle control commands from tablet via POST"""
        try:
            action = command_data.get('action')
            
            if action == 'next':
                web_server.next_slide()
            elif action == 'prev':
                web_server.previous_slide()
            elif action == 'goto':
                slide_id = int(command_data.get('slide', 1))
                web_server.goto_slide(slide_id)
            elif action == 'play':
                web_server.start_demo()
            elif action == 'stop':
                web_server.stop_demo()
            
            # Return success response
            response = json.dumps({'status': 'success', 'action': action})
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error handling POST control command: {e}")
            self.send_500()
    
    def serve_css(self):
        """Serve CSS styles for tablet interface"""
        css_content = """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            overflow-x: hidden;
            touch-action: manipulation;
        }
        
        .presentation-container {
            max-width: 100vw;
            margin: 0 auto;
            padding: 10px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .logo {
            font-size: 18px;
            font-weight: bold;
            color: #ffffff;
        }
        
        .controls {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 10px 15px;
            border: none;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s ease;
            min-width: 60px;
            text-align: center;
        }
        
        .btn:hover, .btn:active {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
        }
        
        .btn-primary {
            background: #FF6600;
        }
        
        .btn-primary:hover {
            background: #e55a00;
        }
        
        .slide-container {
            flex: 1;
            background: white;
            border-radius: 12px;
            margin-bottom: 15px;
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            min-height: 400px;
            position: relative;
        }
        
        .slide-content {
            padding: 30px;
            height: 100%;
            display: flex;
            flex-direction: column;
        }
        
        .slide-title {
            font-size: 28px;
            font-weight: bold;
            color: #1E88E5;
            margin-bottom: 20px;
            text-align: center;
            border-bottom: 3px solid #FF6600;
            padding-bottom: 10px;
        }
        
        .slide-text {
            font-size: 16px;
            line-height: 1.6;
            color: #1F1F1F;
            flex: 1;
            white-space: pre-line;
        }
        
        .slide-images {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-top: 20px;
        }
        
        .slide-image {
            max-width: 200px;
            max-height: 150px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        
        .navigation {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 15px;
            margin-top: 10px;
        }
        
        .slide-info {
            font-size: 16px;
            font-weight: 500;
        }
        
        .nav-buttons {
            display: flex;
            gap: 10px;
        }
        
        .loading {
            text-align: center;
            padding: 50px;
            font-size: 18px;
            color: rgba(255, 255, 255, 0.7);
        }
        
        .error {
            text-align: center;
            padding: 50px;
            color: #ff6b6b;
            font-size: 18px;
        }
        
        @media (max-width: 768px) {
            .presentation-container {
                padding: 5px;
            }
            
            .slide-content {
                padding: 20px;
            }
            
            .slide-title {
                font-size: 24px;
            }
            
            .slide-text {
                font-size: 14px;
            }
            
            .controls, .nav-buttons {
                flex-direction: column;
                width: 100%;
            }
            
            .btn {
                width: 100%;
                margin-bottom: 5px;
            }
        }
        
        /* Auto-refresh indicator */
        .refresh-indicator {
            position: fixed;
            top: 10px;
            right: 10px;
            background: rgba(0, 255, 0, 0.7);
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        
        .refresh-indicator.active {
            opacity: 1;
        }
        """
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/css')
        self.send_header('Content-Length', str(len(css_content.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(css_content.encode('utf-8'))
    
    def serve_javascript(self):
        """Serve JavaScript for tablet interface"""
        js_content = """
        class BertrandtPresentation {
            constructor() {
                this.currentSlide = 1;
                this.totalSlides = 1;
                this.autoRefresh = true;
                this.refreshInterval = 3000; // 3 seconds
                this.init();
            }
            
            init() {
                this.loadCurrentSlide();
                this.setupEventListeners();
                this.startAutoRefresh();
                this.setupSwipeGestures();
            }
            
            setupEventListeners() {
                // Navigation buttons
                document.getElementById('prevBtn').addEventListener('click', () => this.previousSlide());
                document.getElementById('nextBtn').addEventListener('click', () => this.nextSlide());
                document.getElementById('playBtn').addEventListener('click', () => this.toggleDemo());
                document.getElementById('refreshBtn').addEventListener('click', () => this.loadCurrentSlide());
                
                // Keyboard navigation
                document.addEventListener('keydown', (e) => {
                    switch(e.key) {
                        case 'ArrowLeft':
                            this.previousSlide();
                            break;
                        case 'ArrowRight':
                        case ' ':
                            this.nextSlide();
                            break;
                        case 'Home':
                            this.gotoSlide(1);
                            break;
                        case 'End':
                            this.gotoSlide(this.totalSlides);
                            break;
                    }
                });
            }
            
            setupSwipeGestures() {
                let startX, startY, endX, endY;
                const slideContainer = document.querySelector('.slide-container');
                
                slideContainer.addEventListener('touchstart', (e) => {
                    startX = e.touches[0].clientX;
                    startY = e.touches[0].clientY;
                });
                
                slideContainer.addEventListener('touchend', (e) => {
                    if (!startX || !startY) return;
                    
                    endX = e.changedTouches[0].clientX;
                    endY = e.changedTouches[0].clientY;
                    
                    const deltaX = startX - endX;
                    const deltaY = startY - endY;
                    
                    // Horizontal swipe
                    if (Math.abs(deltaX) > Math.abs(deltaY)) {
                        if (Math.abs(deltaX) > 50) { // Minimum swipe distance
                            if (deltaX > 0) {
                                this.nextSlide(); // Swipe left = next
                            } else {
                                this.previousSlide(); // Swipe right = previous
                            }
                        }
                    }
                    
                    startX = startY = endX = endY = null;
                });
            }
            
            async loadCurrentSlide() {
                try {
                    this.showRefreshIndicator();
                    const response = await fetch('/api/current_slide');
                    const data = await response.json();
                    
                    if (data.error) {
                        this.showError(data.error);
                        return;
                    }
                    
                    this.currentSlide = data.slide_id;
                    this.totalSlides = data.total_slides;
                    this.renderSlide(data);
                    this.updateNavigation();
                    
                } catch (error) {
                    console.error('Error loading slide:', error);
                    this.showError('Verbindungsfehler beim Laden der Folie');
                }
            }
            
            async loadSlide(slideId) {
                try {
                    const response = await fetch(`/api/slide?id=${slideId}`);
                    const data = await response.json();
                    
                    if (data.error) {
                        this.showError(data.error);
                        return;
                    }
                    
                    this.currentSlide = data.slide_id;
                    this.renderSlide(data);
                    this.updateNavigation();
                    
                } catch (error) {
                    console.error('Error loading slide:', error);
                    this.showError('Fehler beim Laden der Folie');
                }
            }
            
            renderSlide(slideData) {
                const container = document.getElementById('slideContent');
                
                let imagesHtml = '';
                if (slideData.canvas_elements) {
                    const imageElements = slideData.canvas_elements.filter(el => el.type === 'image');
                    if (imageElements.length > 0) {
                        imagesHtml = '<div class="slide-images">';
                        imageElements.forEach(img => {
                            if (img.web_url) {
                                imagesHtml += `<img src="${img.web_url}" class="slide-image" alt="Slide Image">`;
                            }
                        });
                        imagesHtml += '</div>';
                    }
                }
                
                container.innerHTML = `
                    <div class="slide-content">
                        <h1 class="slide-title">${slideData.title || 'Untitled'}</h1>
                        <div class="slide-text">${slideData.content || ''}</div>
                        ${imagesHtml}
                    </div>
                `;
            }
            
            updateNavigation() {
                document.getElementById('slideInfo').textContent = 
                    `Folie ${this.currentSlide} von ${this.totalSlides}`;
                
                document.getElementById('prevBtn').disabled = this.currentSlide <= 1;
                document.getElementById('nextBtn').disabled = this.currentSlide >= this.totalSlides;
            }
            
            async sendCommand(action, slideId = null) {
                try {
                    const data = { action };
                    if (slideId !== null) data.slide = slideId;
                    
                    const response = await fetch('/api/control', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(data)
                    });
                    
                    const result = await response.json();
                    if (result.status === 'success') {
                        setTimeout(() => this.loadCurrentSlide(), 500);
                    }
                    
                } catch (error) {
                    console.error('Error sending command:', error);
                }
            }
            
            previousSlide() {
                if (this.currentSlide > 1) {
                    this.sendCommand('prev');
                }
            }
            
            nextSlide() {
                if (this.currentSlide < this.totalSlides) {
                    this.sendCommand('next');
                }
            }
            
            gotoSlide(slideId) {
                if (slideId >= 1 && slideId <= this.totalSlides) {
                    this.sendCommand('goto', slideId);
                }
            }
            
            toggleDemo() {
                // Toggle demo mode (start/stop)
                this.sendCommand('play');
            }
            
            startAutoRefresh() {
                if (this.autoRefresh) {
                    setInterval(() => {
                        this.loadCurrentSlide();
                    }, this.refreshInterval);
                }
            }
            
            showRefreshIndicator() {
                const indicator = document.getElementById('refreshIndicator');
                indicator.classList.add('active');
                setTimeout(() => {
                    indicator.classList.remove('active');
                }, 1000);
            }
            
            showError(message) {
                const container = document.getElementById('slideContent');
                container.innerHTML = `<div class="error">${message}</div>`;
            }
        }
        
        // Initialize when page loads
        document.addEventListener('DOMContentLoaded', () => {
            new BertrandtPresentation();
        });
        """
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/javascript')
        self.send_header('Content-Length', str(len(js_content.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(js_content.encode('utf-8'))
    
    def get_presentation_html(self):
        """Generate the main presentation HTML page"""
        return """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bertrandt Präsentation - Tablet View</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="refresh-indicator" id="refreshIndicator">🔄 Aktualisiert</div>
    
    <div class="presentation-container">
        <div class="header">
            <div class="logo">🚗 BERTRANDT Dynamic Messe Stand V4</div>
            <div class="controls">
                <button class="btn" id="refreshBtn">🔄 Aktualisieren</button>
                <button class="btn btn-primary" id="playBtn">▶ Demo</button>
            </div>
        </div>
        
        <div class="slide-container" id="slideContent">
            <div class="loading">Lädt Präsentation...</div>
        </div>
        
        <div class="navigation">
            <div class="slide-info" id="slideInfo">Folie 1 von 1</div>
            <div class="nav-buttons">
                <button class="btn" id="prevBtn">◀ Zurück</button>
                <button class="btn" id="nextBtn">Weiter ▶</button>
            </div>
        </div>
    </div>
    
    <script src="/static/script.js"></script>
</body>
</html>"""
    
    def send_404(self):
        """Send 404 Not Found response"""
        self.send_response(404)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<h1>404 Not Found</h1>')
    
    def send_500(self):
        """Send 500 Internal Server Error response"""
        self.send_response(500)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<h1>500 Internal Server Error</h1>')
    
    def log_message(self, format, *args):
        """Override to use our logger instead of stderr"""
        logger.debug(f"HTTP: {format % args}")

class WebPresentationServer:
    """Main Web Server für Remote-Präsentationen"""
    
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
        self.running = False
        self.current_slide_id = 1
        
        # Callbacks für slide control
        self.slide_change_callbacks = []
        
        # Content manager observer hinzufügen
        content_manager.add_observer(self.on_content_changed)
    
    def add_slide_change_callback(self, callback):
        """Add callback for slide changes from web interface"""
        self.slide_change_callbacks.append(callback)
    
    def on_content_changed(self, slide_id, slide_data, action='update'):
        """Handle content changes from main application"""
        # Update current slide if it was modified
        if slide_id == self.current_slide_id:
            logger.debug(f"Web server: Content updated for current slide {slide_id}")
    
    def start_server(self):
        """Start the web server"""
        try:
            if self.running:
                logger.warning("Web server is already running")
                return False
            
            self.server = ThreadedHTTPServer((self.host, self.port), PresentationRequestHandler)
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            
            self.running = True
            logger.info(f"Web presentation server started on http://{self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting web server: {e}")
            return False
    
    def stop_server(self):
        """Stop the web server"""
        try:
            if not self.running:
                return False
            
            if self.server:
                self.server.shutdown()
                self.server.server_close()
            
            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=5)
            
            self.running = False
            self.server = None
            self.server_thread = None
            
            logger.info("Web presentation server stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping web server: {e}")
            return False
    
    def set_current_slide(self, slide_id):
        """Set current slide for web interface"""
        self.current_slide_id = slide_id
        logger.debug(f"Web server: Current slide set to {slide_id}")
    
    def next_slide(self):
        """Handle next slide command from web interface"""
        slides = content_manager.get_all_slides()
        max_slide = max(slides.keys()) if slides else 1
        
        if self.current_slide_id < max_slide:
            self.current_slide_id += 1
            self._notify_slide_change('next', self.current_slide_id)
    
    def previous_slide(self):
        """Handle previous slide command from web interface"""
        if self.current_slide_id > 1:
            self.current_slide_id -= 1
            self._notify_slide_change('prev', self.current_slide_id)
    
    def goto_slide(self, slide_id):
        """Handle goto slide command from web interface"""
        slides = content_manager.get_all_slides()
        if slide_id in slides:
            self.current_slide_id = slide_id
            self._notify_slide_change('goto', slide_id)
    
    def start_demo(self):
        """Handle start demo command from web interface"""
        self._notify_slide_change('play', self.current_slide_id)
    
    def stop_demo(self):
        """Handle stop demo command from web interface"""
        self._notify_slide_change('stop', self.current_slide_id)
    
    def _notify_slide_change(self, action, slide_id):
        """Notify main application about slide changes from web interface"""
        for callback in self.slide_change_callbacks:
            try:
                callback(action, slide_id)
            except Exception as e:
                logger.error(f"Error in slide change callback: {e}")
    
    def get_server_info(self):
        """Get server information"""
        return {
            'running': self.running,
            'host': self.host,
            'port': self.port,
            'url': f"http://{self.host}:{self.port}" if self.running else None,
            'current_slide': self.current_slide_id
        }

# Global web server instance
web_server = WebPresentationServer()
