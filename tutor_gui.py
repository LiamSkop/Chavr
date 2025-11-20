#!/usr/bin/env python3
"""
Chavr AI Tutor GUI - Focused on text study and AI Q&A.
Simplified interface without speech transcription.
"""

import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime
from pathlib import Path
import http.server
import socketserver
import threading
import webbrowser
from tutor_app import TutorApp
from sefaria_manager import SefariaManager

# Try to import webview, but handle gracefully if not available
try:
    import webview
    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False
    print("Warning: pywebview not installed. Text display will use fallback.")


class TutorGUI:
    """Simplified GUI for AI Torah tutor."""
    
    def __init__(self):
        """Initialize the GUI application."""
        self.root = tk.Tk()
        self.root.title("Chavr - Your AI Torah Tutor")
        self.root.geometry("900x1200")  # Increased height for text display panel
        self.root.minsize(800, 800)  # Increased minimum height
        self.root.configure(bg="#F5F5F5")
        
        # State management
        self.sefaria_manager = SefariaManager()
        self.current_text_content = None
        self.current_text_language = "en"
        self._terms_extracting = False
        self.selected_phrase = None  # Track selected text for phrase selection
        self.webview_window = None  # Webview window for text display
        
        # Initialize app
        self.app = TutorApp(question_callback=self._on_ai_response)
        
        # Build UI
        self._setup_ui()
        
        # Bind keyboard shortcuts (after UI is built so widgets exist)
        self._bind_shortcuts()
    
    def _setup_ui(self):
        """Setup the main UI layout - streamlined Q&A focus."""
        # Main container
        main_frame = tk.Frame(self.root, bg="#F5F5F5")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        self._create_header(main_frame)
        
        # Text reference section (minimal - just for context)
        self._create_text_reference_section(main_frame)
        
        # Text display panel (Premium webview-based)
        self._create_text_display_section(main_frame)
        
        # Challenging terms section (expandable)
        self._create_challenging_terms_section(main_frame)
        
        # Large question input (60% of screen)
        self._create_question_section(main_frame)
        
        # AI response display (40% of screen)
        self._create_response_section(main_frame)
        
        # Bottom controls
        self._create_bottom_controls(main_frame)
    
    def _create_header(self, parent):
        """Create header section."""
        header = tk.Frame(parent, bg="#FFFFFF", relief=tk.SOLID, bd=1)
        header.pack(fill=tk.X, pady=(0, 15))
        
        title = tk.Label(
            header,
            text="Chavr - Your AI Torah Tutor",
            font=("Arial", 18, "bold"),
            bg="#FFFFFF",
            fg="#1F2937",
            pady=15
        )
        title.pack()
    
    def _create_text_reference_section(self, parent):
        """Create compact text reference selector with navigation."""
        ref_frame = tk.Frame(parent, bg="#FFFFFF", relief=tk.SOLID, bd=1)
        ref_frame.pack(fill=tk.X, pady=(0, 15))
        
        inner = tk.Frame(ref_frame, bg="#FFFFFF", padx=15, pady=12)
        inner.pack(fill=tk.X)
        
        # Left side: Reference display and navigation
        left_frame = tk.Frame(inner, bg="#FFFFFF")
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(
            left_frame,
            text="Studying:",
            font=("Arial", 10, "bold"),
            bg="#FFFFFF",
            fg="#374151"
        ).pack(side=tk.LEFT, padx=(0, 8))
        
        # Current reference display
        self.current_ref_label = tk.Label(
            left_frame,
            text="No text selected",
            font=("Arial", 11),
            bg="#FFFFFF",
            fg="#1F2937"
        )
        self.current_ref_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Navigation buttons
        nav_frame = tk.Frame(left_frame, bg="#FFFFFF")
        nav_frame.pack(side=tk.LEFT)
        
        self.prev_btn = tk.Button(
            nav_frame,
            text="◀ Previous",
            command=self._previous_chapter,
            bg="#E5E7EB",
            fg="#374151",
            font=("Arial", 9),
            relief=tk.FLAT,
            padx=12,
            pady=5,
            cursor="hand2",
            state=tk.DISABLED
        )
        self.prev_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.next_btn = tk.Button(
            nav_frame,
            text="Next ▶",
            command=self._next_chapter,
            bg="#E5E7EB",
            fg="#374151",
            font=("Arial", 9),
            relief=tk.FLAT,
            padx=12,
            pady=5,
            cursor="hand2",
            state=tk.DISABLED
        )
        self.next_btn.pack(side=tk.LEFT)
        
        # Right side: Change text button and language toggle
        right_frame = tk.Frame(inner, bg="#FFFFFF")
        right_frame.pack(side=tk.RIGHT)
        
        change_btn = tk.Button(
            right_frame,
            text="Change Text",
            command=self._show_text_selector,
            bg="#3B82F6",
            fg="white",
            font=("Arial", 9, "bold"),
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2"
        )
        change_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.lang_btn = tk.Button(
            right_frame,
            text="EN",
            command=self._toggle_language,
            bg="#10B981",
            fg="white",
            font=("Arial", 9, "bold"),
            relief=tk.FLAT,
            padx=12,
            pady=5,
            cursor="hand2"
        )
        self.lang_btn.pack(side=tk.LEFT)
        
        # Store current reference for navigation
        self.current_reference = None
    
    def _create_text_display_section(self, parent):
        """Create premium webview-based text display panel."""
        # Main container frame
        text_display_frame = tk.LabelFrame(
            parent,
            text="Text",
            font=("Arial", 12, "bold"),
            bg="#FFFFFF",
            fg="#374151"
        )
        text_display_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        if not WEBVIEW_AVAILABLE:
            # Fallback: show message to install pywebview
            error_label = tk.Label(
                text_display_frame,
                text="Please install pywebview: pip install pywebview",
                fg="#DC2626",
                bg="#FFFFFF",
                pady=20
            )
            error_label.pack()
            return
        
        # Start local HTTP server for serving static files
        self._start_local_server()
        
        # Get path to HTML file
        static_dir = Path(__file__).parent / "static"
        html_path = static_dir / "text_display.html"
        
        # Create API class for communication
        self.text_display_api = TextDisplayAPI(self)
        
        # Store webview window reference (will be created when needed)
        self.webview_window = None
        self.webview_initialized = False
        
        # Create webview window - but start it properly integrated with tkinter
        try:
            # Use file:// URL for local files
            file_url = f"file://{html_path.absolute()}"
            
            # Create window configuration
            self.webview_config = {
                'title': 'Text Display',
                'url': file_url,
                'width': 850,
                'height': 250,
                'resizable': True,
                'js_api': self.text_display_api,
                'background_color': '#1F2937',
                'frameless': False
            }
            
            # Don't initialize webview here - we'll do it before mainloop starts
            # Store config for later initialization
            self._webview_ready = False
            
        except Exception as e:
            print(f"Error setting up webview: {e}")
            error_label = tk.Label(
                text_display_frame,
                text=f"Error loading text display: {e}",
                fg="#DC2626",
                bg="#FFFFFF"
            )
            error_label.pack(pady=20)
    
    def _start_local_server(self):
        """Start a local HTTP server for serving static files and handling API calls."""
        static_dir = Path(__file__).parent / "static"
        gui_instance = self  # Capture reference for API calls
        
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(static_dir), **kwargs)
            
            def do_OPTIONS(self):
                """Handle CORS preflight requests."""
                self.send_response(200)
                self.end_headers()
            
            def do_POST(self):
                """Handle POST requests from JavaScript (button clicks, selections)."""
                if self.path == '/api/ask-about-selection':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    
                    try:
                        import json
                        data = json.loads(post_data.decode('utf-8'))
                        phrase = data.get('phrase', '')
                        siman = data.get('siman')
                        klal = data.get('klal')
                        
                        if not phrase:
                            raise ValueError("Missing phrase")
                        
                        response_text = gui_instance._generate_selection_response(phrase, siman, klal)
                        
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            'status': 'ok',
                            'response': response_text or ''
                        }).encode())
                    except Exception as e:
                        print(f"Error handling API request: {e}")
                        self.send_response(500)
                        self.send_header('Content-Type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            'status': 'error',
                            'message': str(e)
                        }).encode())
                elif self.path == '/api/text-selected':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    
                    try:
                        import json
                        data = json.loads(post_data.decode('utf-8'))
                        text = data.get('text', '')
                        
                        # Store selected text
                        gui_instance.root.after(0, lambda: gui_instance._on_text_selected(text))
                        
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps({'status': 'ok'}).encode())
                    except Exception as e:
                        print(f"Error handling selection: {e}")
                        self.send_response(500)
                        self.end_headers()
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def end_headers(self):
                # Add CORS headers for all responses
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                super().end_headers()
        
        # Use a fixed port for consistency
        port = 8765
        try:
            self.http_server = socketserver.TCPServer(("", port), Handler)
            self.http_port = port
        except OSError:
            # Port in use, try another
            port = 8766
            self.http_server = socketserver.TCPServer(("", port), Handler)
            self.http_port = port
        
        def serve():
            try:
                self.http_server.serve_forever()
            except Exception as e:
                print(f"HTTP server error: {e}")
        
        thread = threading.Thread(target=serve, daemon=True)
        thread.start()
        
        self.http_url = f"http://localhost:{self.http_port}"
    
    def _initialize_webview(self):
        """Initialize webview - workaround for main thread conflict."""
        # pywebview requires main thread but conflicts with tkinter
        # Solution: Use a local HTTP server and open in system browser
        # OR use webview in a separate process
        # For now, we'll use a simpler approach: open HTML file directly
        
        try:
            if not self.webview_initialized:
                static_dir = Path(__file__).parent / "static"
                html_path = static_dir / "text_display.html"
                
                # Open HTML file via HTTP server for better functionality
                # This provides the premium experience but in a separate window
                import webbrowser
                http_url = f"{self.http_url}/text_display.html"
                
                print(f"Opening text display in browser: {http_url}")
                webbrowser.open(http_url)
                
                self.webview_initialized = True
                print("Note: Text display opened in browser.")
                print("For embedded display, consider using cefpython3 or restructuring the app.")
                
        except Exception as e:
            print(f"Error initializing webview: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_text_display(self, text_content, language, structured_content=None):
        """Update the text display with optional structured content (Klal/Siman)."""
        # Since webview integration is complex, we'll use a file-based approach
        # Write text content to a JSON file that the HTML can read via polling
        try:
            static_dir = Path(__file__).parent / "static"
            data_file = static_dir / "text_data.json"
            
            import json
            data = {
                'text': text_content,
                'language': language,
                'timestamp': datetime.now().isoformat(),
                'structured': structured_content  # Add structured content
            }
            
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # If webview window exists, try to update it
            if self.webview_window:
                try:
                    escaped_text = text_content.replace("'", "\\'").replace("\n", "\\n")
                    escaped_lang = language.replace("'", "\\'")
                    js_code = f"window.setTextContent('{escaped_text}', '{escaped_lang}')"
                    self.webview_window.evaluate_js(js_code)
                except:
                    pass  # Webview might not be ready yet
            
        except Exception as e:
            print(f"Error updating text display: {e}")
    
    def _on_text_selected(self, selected_text):
        """Handle text selection from webview."""
        self.selected_phrase = selected_text
        # Note: Button is handled in webview, but we store the selection
    
    def _generate_selection_response(self, phrase, siman=None, klal=None):
        """Generate AI response for a selected phrase synchronously."""
        if not phrase:
            raise ValueError("No phrase provided")
        
        if not self.current_reference:
            raise ValueError("Please select a text to study first")
        
        question = self._build_selection_question(phrase, siman, klal)
        response = self.app.ask_question(question)
        return response or ""
    
    def _build_selection_question(self, phrase, siman=None, klal=None):
        """Build the question string for a selected phrase."""
        cleaned = phrase.strip()
        if not cleaned:
            raise ValueError("No phrase provided")
        
        try:
            siman = int(siman) if siman is not None else None
        except (TypeError, ValueError):
            siman = None
        
        try:
            klal = int(klal) if klal is not None else None
        except (TypeError, ValueError):
            klal = None
        
        if siman and klal:
            return f"What does '{cleaned}' mean in Klal {klal}, Siman {siman}?"
        if siman:
            return f"What does '{cleaned}' mean in Siman {siman}?"
        return f"What does '{cleaned}' mean in this context?"
    
    def _ask_about_selection(self, phrase=None, siman=None, klal=None):
        """Legacy handler for manual selection questions."""
        selected = phrase or self.selected_phrase
        if not selected:
            return
        
        try:
            response = self._generate_selection_response(selected, siman, klal)
            if response:
                self._add_message(f"AI Tutor: {response}", "ai")
        except Exception as e:
            self._show_error(f"Error asking about selection: {str(e)}")
    
    def _create_question_section(self, parent):
        """Create large, prominent question input area."""
        question_frame = tk.LabelFrame(
            parent,
            text="Ask Your Question",
            font=("Arial", 12, "bold"),
            bg="#FFFFFF",
            fg="#374151"
        )
        question_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Large text input
        self.question_input = scrolledtext.ScrolledText(
            question_frame,
            font=("Arial", 14),
            wrap=tk.WORD,
            bg="#FFFFFF",
            fg="#1F2937",
            relief=tk.SOLID,
            bd=1,
            height=8
        )
        self.question_input.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        # Enter sends, Shift+Enter creates new line
        self.question_input.bind('<Return>', lambda e: self._handle_return())
        self.question_input.bind('<Shift-Return>', lambda e: None)  # Allow new line
        
        # Placeholder text hint
        self.question_input.insert("1.0", "Type your question here...")
        self.question_input.config(fg="#9CA3AF")
        self.question_input.bind('<FocusIn>', self._on_question_focus_in)
        
        # Auto-focus on load
        self.root.after(100, lambda: self.question_input.focus())
    
    def _create_response_section(self, parent):
        """Create AI response display area."""
        response_frame = tk.LabelFrame(
            parent,
            text="AI Tutor Response",
            font=("Arial", 12, "bold"),
            bg="#FFFFFF",
            fg="#374151"
        )
        response_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Response display
        self.chat_display = scrolledtext.ScrolledText(
            response_frame,
            font=("Arial", 12),
            wrap=tk.WORD,
            bg="#F9FAFB",
            fg="#1F2937",
            relief=tk.SOLID,
            bd=1,
            height=10
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        self.chat_display.config(state=tk.DISABLED)
    
    def _create_challenging_terms_section(self, parent):
        """Create expandable section for challenging terms."""
        # Main container frame
        self.terms_frame = tk.Frame(parent, bg="#FFFFFF", relief=tk.SOLID, bd=1)
        self.terms_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Header with toggle button
        header_frame = tk.Frame(self.terms_frame, bg="#FFFFFF", padx=15, pady=10)
        header_frame.pack(fill=tk.X)
        
        self.terms_toggle_btn = tk.Button(
            header_frame,
            text="▼ Challenging Terms",
            command=self._toggle_terms_panel,
            bg="#10B981",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2",
            anchor="w"
        )
        self.terms_toggle_btn.pack(side=tk.LEFT)
        
        # Loading indicator (initially hidden)
        self.terms_loading_label = tk.Label(
            header_frame,
            text="Analyzing text...",
            font=("Arial", 9),
            bg="#FFFFFF",
            fg="#6B7280"
        )
        
        # Terms content frame (initially collapsed)
        self.terms_content_frame = tk.Frame(self.terms_frame, bg="#FFFFFF")
        self.terms_content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Scrollable frame for terms list
        terms_canvas = tk.Canvas(self.terms_content_frame, bg="#F9FAFB", highlightthickness=0)
        scrollbar = tk.Scrollbar(self.terms_content_frame, orient="vertical", command=terms_canvas.yview)
        self.terms_scrollable_frame = tk.Frame(terms_canvas, bg="#F9FAFB")
        
        self.terms_scrollable_frame.bind(
            "<Configure>",
            lambda e: terms_canvas.configure(scrollregion=terms_canvas.bbox("all"))
        )
        
        terms_canvas.create_window((0, 0), window=self.terms_scrollable_frame, anchor="nw")
        terms_canvas.configure(yscrollcommand=scrollbar.set)
        
        terms_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.terms_canvas = terms_canvas
        
        # Initially hide content
        self.terms_expanded = False
        self.terms_content_frame.pack_forget()
    
    def _toggle_terms_panel(self):
        """Toggle the challenging terms panel."""
        self.terms_expanded = not self.terms_expanded
        
        if self.terms_expanded:
            self.terms_content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
            self.terms_toggle_btn.config(text="▲ Challenging Terms")
            self._refresh_terms_display()
        else:
            self.terms_content_frame.pack_forget()
            self.terms_toggle_btn.config(text="▼ Challenging Terms")
    
    def _refresh_terms_display(self):
        """Refresh the display of challenging terms."""
        # Clear existing terms
        for widget in self.terms_scrollable_frame.winfo_children():
            widget.destroy()
        
        terms = self.app.get_challenging_terms()
        
        if not terms:
            # Show loading or empty state
            if hasattr(self, '_terms_extracting') and self._terms_extracting:
                tk.Label(
                    self.terms_scrollable_frame,
                    text="Analyzing text for challenging terms...",
                    font=("Arial", 10),
                    bg="#F9FAFB",
                    fg="#6B7280",
                    pady=20
                ).pack()
            else:
                tk.Label(
                    self.terms_scrollable_frame,
                    text="No challenging terms identified yet.",
                    font=("Arial", 10),
                    bg="#F9FAFB",
                    fg="#6B7280",
                    pady=20
                ).pack()
            return
        
        # Display terms
        for idx, term_data in enumerate(terms):
            term = term_data.get('term', '')
            explanation = term_data.get('explanation', '')
            context = term_data.get('context', '')
            
            # Term frame
            term_frame = tk.Frame(self.terms_scrollable_frame, bg="#FFFFFF", relief=tk.SOLID, bd=1)
            term_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Term name (bold)
            term_label = tk.Label(
                term_frame,
                text=term,
                font=("Arial", 11, "bold"),
                bg="#FFFFFF",
                fg="#1F2937",
                anchor="w"
            )
            term_label.pack(fill=tk.X, padx=10, pady=(10, 5))
            
            # Explanation
            explanation_label = tk.Label(
                term_frame,
                text=explanation,
                font=("Arial", 10),
                bg="#FFFFFF",
                fg="#374151",
                anchor="w",
                wraplength=600,
                justify="left"
            )
            explanation_label.pack(fill=tk.X, padx=10, pady=(0, 5))
            
            # Context (if available)
            if context:
                context_label = tk.Label(
                    term_frame,
                    text=f"Context: {context}",
                    font=("Arial", 9, "italic"),
                    bg="#FFFFFF",
                    fg="#6B7280",
                    anchor="w",
                    wraplength=600,
                    justify="left"
                )
                context_label.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Update scroll region
        self.terms_scrollable_frame.update_idletasks()
        self.terms_canvas.configure(scrollregion=self.terms_canvas.bbox("all"))
    
    def _update_terms_display(self, terms_data):
        """Update terms display when extraction completes."""
        terms = terms_data.get('terms', [])
        reference = terms_data.get('reference', '')
        
        # Hide loading indicator
        self.terms_loading_label.pack_forget()
        self._terms_extracting = False
        
        # Refresh display if panel is expanded
        if self.terms_expanded:
            self._refresh_terms_display()
        
        # Update button text to show count
        if terms:
            self.terms_toggle_btn.config(text=f"▼ Challenging Terms ({len(terms)})")
    
    
    def _create_bottom_controls(self, parent):
        """Create bottom control buttons."""
        # No controls needed - stateless app
        pass
    
    def _bind_shortcuts(self):
        """Bind keyboard shortcuts - simplified."""
        # Focus question input
        self.root.bind('<Command-k>', lambda e: self._focus_input())
        self.root.bind('<Control-k>', lambda e: self._focus_input())
        
        # Chapter navigation
        self.root.bind('<Command-Left>', lambda e: self._previous_chapter())
        self.root.bind('<Control-Left>', lambda e: self._previous_chapter())
        self.root.bind('<Command-Right>', lambda e: self._next_chapter())
        self.root.bind('<Control-Right>', lambda e: self._next_chapter())
    
    def _focus_input(self):
        """Focus the question input field."""
        self.question_input.focus()
    
    def _handle_return(self, event=None):
        """Handle Enter key in question input."""
        # Send on Enter
        self._send_message()
        return "break"
    
    def _on_question_focus_in(self, event):
        """Handle focus in on question input - clear placeholder."""
        if self.question_input.get(1.0, tk.END).strip() == "Type your question here...":
            self.question_input.delete(1.0, tk.END)
            self.question_input.config(fg="#1F2937")
    
    def _set_reference(self, reference: str):
        """Set text reference and load context for LLM."""
        if not reference:
            return False
        
        reference = reference.strip()
        language = "he" if self.current_text_language == "he" else "en"
        
        # Load text context (for LLM and display)
        if self.app.load_sefaria_text(reference, language):
            self.current_reference = reference
            self.current_ref_label.config(text=reference)
            
            # Update text display panel (webview)
            text_content = self.app.get_current_text_content()
            structured_content = self.app.get_structured_content()
            if text_content:
                self._update_text_display(text_content, language, structured_content)
            else:
                self._update_text_display("Text content not available...", language)
            
            # Clear any previous selection
            self.selected_phrase = None
            
            # Enable navigation buttons
            self.prev_btn.config(state=tk.NORMAL)
            self.next_btn.config(state=tk.NORMAL)
            
            # Check if terms are being extracted
            terms = self.app.get_challenging_terms()
            if not terms:
                # Show loading indicator
                self.terms_loading_label.pack(side=tk.LEFT, padx=(10, 0))
                self._terms_extracting = True
            else:
                # Update button with count
                self.terms_toggle_btn.config(text=f"▼ Challenging Terms ({len(terms)})")
            
            self._add_message(f"Studying: {reference} ({language})", "system")
            return True
        else:
            self._show_error(f"Could not load: {reference}")
            return False
    
    def _show_text_selector(self):
        """Show popup window for selecting text."""
        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title("Select Text to Study")
        popup.geometry("600x500")
        popup.configure(bg="#FFFFFF")
        
        # Frame for content
        content = tk.Frame(popup, bg="#FFFFFF", padx=20, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Search box
        tk.Label(
            content,
            text="Find a text:",
            font=("Arial", 11, "bold"),
            bg="#FFFFFF",
            fg="#374151"
        ).pack(anchor=tk.W, pady=(0, 5))
        
        search_entry = tk.Entry(content, font=("Arial", 12), width=50)
        search_entry.pack(fill=tk.X, pady=(0, 10))
        search_entry.focus()
        
        # Popular texts
        tk.Label(
            content,
            text="Popular:",
            font=("Arial", 10, "bold"),
            bg="#FFFFFF",
            fg="#6B7280"
        ).pack(anchor=tk.W, pady=(10, 5))
        
        popular_frame = tk.Frame(content, bg="#FFFFFF")
        popular_frame.pack(fill=tk.X, pady=(0, 10))
        
        popular_texts = self.sefaria_manager.get_popular_texts(limit=6)
        for text in popular_texts:
            btn = tk.Button(
                popular_frame,
                text=text['name'],
                command=lambda t=text['name']: self._select_text_from_popup(t, popup),
                bg="#EBF5FF",
                fg="#1E40AF",
                font=("Arial", 9),
                relief=tk.FLAT,
                padx=10,
                pady=5,
                cursor="hand2"
            )
            btn.pack(side=tk.LEFT, padx=3)
        
        # Results list (initially empty)
        results_frame = tk.Frame(content, bg="#FFFFFF")
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        results_listbox = tk.Listbox(results_frame, font=("Arial", 11), height=10)
        results_listbox.pack(fill=tk.BOTH, expand=True)
        
        # Search handler
        def on_search(event=None):
            query = search_entry.get()
            if len(query) < 1:
                results_listbox.delete(0, tk.END)
                return
            
            results = self.sefaria_manager.search_texts(query, limit=10)
            results_listbox.delete(0, tk.END)
            
            for result in results:
                display = f"{result['name']}"
                if result.get('hebrew_name'):
                    display += f" ({result['hebrew_name']})"
                results_listbox.insert(tk.END, display)
        
        search_entry.bind('<KeyRelease>', on_search)
        results_listbox.bind('<Double-Button-1>', lambda e: self._select_text_from_listbox(results_listbox, popup))
        
        # Select button
        select_btn = tk.Button(
            content,
            text="Select",
            command=lambda: self._select_text_from_listbox(results_listbox, popup),
            bg="#3B82F6",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2"
        )
        select_btn.pack(pady=(10, 0))
    
    def _select_text_from_popup(self, text_name: str, popup):
        """Select text from popular button."""
        reference = self.sefaria_manager.load_text_by_name(text_name, self.current_text_language)
        if reference:
            self._set_reference(reference)
            popup.destroy()
    
    def _select_text_from_listbox(self, listbox, popup):
        """Select text from listbox."""
        selection = listbox.curselection()
        if not selection:
            return
        
        text_display = listbox.get(selection[0])
        # Extract text name (before parenthesis if Hebrew name shown)
        text_name = text_display.split(' (')[0]
        
        reference = self.sefaria_manager.load_text_by_name(text_name, self.current_text_language)
        if reference:
            self._set_reference(reference)
            popup.destroy()
    
    def _toggle_language(self):
        """Toggle between English and Hebrew."""
        if self.current_text_language == "en":
            self.current_text_language = "he"
            self.lang_btn.config(text="HE", bg="#059669")
        else:
            self.current_text_language = "en"
            self.lang_btn.config(text="EN", bg="#10B981")
        
        # Reload text if we have a reference (this will update the text display)
        if self.current_reference:
            self._set_reference(self.current_reference)
    
    def _parse_reference(self, ref: str) -> tuple:
        """
        Parse a reference like "Genesis 1:1" into (book, chapter, verse).
        
        Returns:
            (book, chapter, verse) or (book, chapter, None) or (book, None, None)
        """
        import re
        
        # Pattern: "Book Chapter:Verse" or "Book Chapter" or "Book"
        pattern = r'^(.+?)\s+(\d+)(?::(\d+))?$'
        match = re.match(pattern, ref.strip())
        
        if match:
            book = match.group(1).strip()
            chapter = int(match.group(2))
            verse = int(match.group(3)) if match.group(3) else None
            return (book, chapter, verse)
        
        # Fallback: just book name
        return (ref.strip(), None, None)
    
    def _format_reference(self, book: str, chapter: int = None, verse: int = None) -> str:
        """Format reference components into string."""
        if chapter is None:
            return book
        elif verse is None:
            return f"{book} {chapter}"
        else:
            return f"{book} {chapter}:{verse}"
    
    def _previous_chapter(self):
        """Navigate to previous chapter."""
        if not self.current_reference:
            return
        
        book, chapter, verse = self._parse_reference(self.current_reference)
        
        if chapter is None:
            # Can't navigate if no chapter
            return
        
        # Decrement chapter
        new_chapter = chapter - 1
        
        if new_chapter < 1:
            # Would go below chapter 1 - don't navigate
            return
        
        new_ref = self._format_reference(book, new_chapter, None)
        self._set_reference(new_ref)
    
    def _next_chapter(self):
        """Navigate to next chapter."""
        if not self.current_reference:
            return
        
        book, chapter, verse = self._parse_reference(self.current_reference)
        
        if chapter is None:
            # If no chapter, start at chapter 1
            new_ref = self._format_reference(book, 1, None)
        else:
            # Increment chapter
            new_chapter = chapter + 1
            new_ref = self._format_reference(book, new_chapter, None)
        
        self._set_reference(new_ref)
    
    def _send_message(self):
        """Send a question to the AI tutor."""
        question = self.question_input.get(1.0, tk.END).strip()
        
        # Skip if empty or placeholder
        if not question or question == "Type your question here...":
            return
        
        # Check if we have a reference set
        if not self.current_reference:
            self._show_error("Please select a text to study first (click 'Change Text')")
            return
        
        # Clear input and reset placeholder
        self.question_input.delete(1.0, tk.END)
        self.question_input.insert("1.0", "Type your question here...")
        self.question_input.config(fg="#9CA3AF")
        
        # Show user message
        self._add_message(f"You: {question}", "user")
        
        # Get AI response
        self._add_message("Thinking...", "system")
        
        # Call the app's ask_question method
        response = self.app.ask_question(question)
        
        if response:
            # Remove "Thinking..." and add AI response
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete("end-2l", "end-1l")
            self._add_message(f"AI Tutor: {response}", "ai")
            self.chat_display.config(state=tk.DISABLED)
        else:
            self._add_message("No response from AI tutor.", "error")
    
    def _on_ai_response(self, sender, response, timestamp):
        """Callback for AI responses and other events."""
        # Handle terms ready signal
        if sender == 'terms_ready':
            self._update_terms_display(response)
        # Regular AI responses are handled in _send_message
    
    def _add_message(self, text: str, sender: str):
        """Add a message to the chat display."""
        self.chat_display.config(state=tk.NORMAL)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M")
        
        # Color coding
        colors = {
            "user": "#1E40AF",  # Blue
            "ai": "#059669",    # Green
            "system": "#6B7280", # Gray
            "error": "#DC2626"  # Red
        }
        
        color = colors.get(sender, "#000000")
        self.chat_display.insert(tk.END, f"[{timestamp}] ", ("timestamp",))
        self.chat_display.insert(tk.END, f"{text}\n\n", (sender,))
        
        # Configure tags
        self.chat_display.tag_config("timestamp", foreground="#9CA3AF", font=("Arial", 9))
        self.chat_display.tag_config(sender, foreground=color)
        
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def _show_error(self, message: str):
        """Show an error message."""
        self._add_message(f"Error: {message}", "error")
    
    def run(self):
        """Start the GUI main loop."""
        # Initialize webview before starting mainloop
        if hasattr(self, 'webview_config') and not self.webview_initialized:
            self._initialize_webview()
        
        # Start tkinter mainloop
        # Note: If webview was started, it will block here
        # We need to integrate them properly
        self.root.mainloop()
        
        # If webview needs to be started, we'll need a different approach
        # For now, webview won't start automatically due to main thread conflict


class TextDisplayAPI:
    """API class for communication between Python and JavaScript."""
    
    def __init__(self, gui):
        self.gui = gui
    
    def onTextSelected(self, text):
        """Called when text is selected in webview."""
        self.gui._on_text_selected(text)
    
    def askAboutSelection(self, phrase):
        """Called when user clicks 'What does this mean?' button."""
        self.gui._ask_about_selection(phrase)


if __name__ == "__main__":
    gui = TutorGUI()
    gui.run()

