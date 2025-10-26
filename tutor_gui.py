#!/usr/bin/env python3
"""
Chavr AI Tutor GUI - Focused on text study and AI Q&A.
Simplified interface without speech transcription.
"""

import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime
from tutor_app import TutorApp
from sefaria_manager import SefariaManager


class TutorGUI:
    """Simplified GUI for AI Torah tutor."""
    
    def __init__(self):
        """Initialize the GUI application."""
        self.root = tk.Tk()
        self.root.title("Chavr - Your AI Torah Tutor")
        self.root.geometry("900x1000")
        self.root.minsize(800, 700)
        self.root.configure(bg="#F5F5F5")
        
        # State management
        self.current_session = None
        self.sefaria_manager = SefariaManager()
        self.current_text_content = None
        self.current_text_language = "en"
        
        # Initialize app
        self.app = TutorApp(question_callback=self._on_ai_response)
        
        # Start a session automatically
        self.app.start_session()
        self.current_session = self.app.current_session
        
        # Build UI
        self._setup_ui()
        
        # Bind keyboard shortcuts
        self._bind_shortcuts()
    
    def _setup_ui(self):
        """Setup the main UI layout."""
        # Main container
        main_frame = tk.Frame(self.root, bg="#F5F5F5")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        self._create_header(main_frame)
        
        # Text input section
        self._create_text_input_section(main_frame)
        
        # Text display (50% of screen)
        self._create_text_display(main_frame)
        
        # Chat section (40% of screen)
        self._create_chat_section(main_frame)
        
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
    
    def _create_text_input_section(self, parent):
        """Create smart text finder interface."""
        finder_frame = tk.Frame(parent, bg="#FFFFFF", relief=tk.SOLID, bd=1)
        finder_frame.pack(fill=tk.X, pady=(0, 15))
        
        inner = tk.Frame(finder_frame, bg="#FFFFFF", padx=15, pady=15)
        inner.pack(fill=tk.BOTH, expand=True)
        
        # Search box
        self._create_search_box(inner)
        
        # Popular texts quick access
        self._create_popular_texts(inner)
        
        # Language toggle
        lang_frame = tk.Frame(inner, bg="#FFFFFF")
        lang_frame.pack(anchor=tk.E, pady=(5, 0))
        
        self.lang_btn = tk.Button(
            lang_frame,
            text="EN",
            command=self._toggle_language,
            bg="#10B981",
            fg="white",
            font=("Arial", 9, "bold"),
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2"
        )
        self.lang_btn.pack(side=tk.RIGHT)
    
    def _create_search_box(self, parent):
        """Create search box with live results."""
        search_frame = tk.Frame(parent, bg="#FFFFFF")
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            search_frame,
            text="Find a text to study:",
            font=("Arial", 11, "bold"),
            bg="#FFFFFF",
            fg="#374151"
        ).pack(anchor=tk.W, pady=(0, 5))
        
        entry_frame = tk.Frame(search_frame, bg="#FFFFFF")
        entry_frame.pack(fill=tk.X)
        
        self.text_ref_entry = tk.Entry(
            entry_frame,
            font=("Arial", 12),
            relief=tk.SOLID,
            bd=1
        )
        self.text_ref_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 10))
        self.text_ref_entry.bind('<KeyRelease>', self._on_search_keypress)
        self.text_ref_entry.bind('<Return>', lambda e: self._load_text())
        self.text_ref_entry.bind('<Down>', lambda e: self._focus_first_result())
        self.text_ref_entry.bind('<Escape>', lambda e: self._hide_search_results())
        
        search_btn = tk.Button(
            entry_frame,
            text="Search",
            command=self._load_text,
            bg="#3B82F6",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2"
        )
        search_btn.pack(side=tk.LEFT)
        
        # Search results dropdown (initially hidden)
        self.search_results_frame = None
        self._search_timer = None
    
    def _create_popular_texts(self, parent):
        """Create popular text quick access buttons."""
        popular_frame = tk.Frame(parent, bg="#FFFFFF")
        popular_frame.pack(fill=tk.X, pady=(5, 0))
        
        tk.Label(
            popular_frame,
            text="Quick Access:",
            font=("Arial", 9, "bold"),
            bg="#FFFFFF",
            fg="#6B7280"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # Get popular texts
        popular_texts = self.sefaria_manager.get_popular_texts(limit=6)
        
        # Create button frame
        btn_frame = tk.Frame(popular_frame, bg="#FFFFFF")
        btn_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        for text in popular_texts:
            btn = tk.Button(
                btn_frame,
                text=text['name'],
                command=lambda t=text['name']: self._load_text_by_name(t),
                bg="#EBF5FF",
                fg="#1E40AF",
                font=("Arial", 9),
                relief=tk.FLAT,
                padx=10,
                pady=5,
                cursor="hand2"
            )
            btn.pack(side=tk.LEFT, padx=3)
    
    def _on_search_keypress(self, event):
        """Handle search box key press."""
        query = self.text_ref_entry.get()
        
        if len(query) < 2:
            self._hide_search_results()
            return
        
        # Debounce search
        if self._search_timer:
            self.root.after_cancel(self._search_timer)
        
        self._search_timer = self.root.after(150, lambda: self._perform_search(query))
    
    def _perform_search(self, query):
        """Perform search and show results."""
        results = self.sefaria_manager.search_texts(query, limit=6)
        self._show_search_results(results)
    
    def _show_search_results(self, results):
        """Display search results dropdown."""
        # Hide existing results
        self._hide_search_results()
        
        if not results:
            return
        
        # Create results frame
        self.search_results_frame = tk.Frame(
            self.text_ref_entry.master.master,
            bg="#FFFFFF",
            relief=tk.SOLID,
            bd=1
        )
        
        # Position below search box
        self.search_results_frame.place(
            x=self.text_ref_entry.winfo_x() + self.text_ref_entry.master.winfo_x(),
            y=self.text_ref_entry.winfo_y() + self.text_ref_entry.master.winfo_y() + 40,
            width=self.text_ref_entry.winfo_width() + 110
        )
        
        # Display results
        for idx, result in enumerate(results):
            result_frame = tk.Frame(self.search_results_frame, bg="#FFFFFF")
            result_frame.pack(fill=tk.X, padx=2, pady=1)
            
            # Display text info
            text_info = f"{result['name']}"
            if result.get('hebrew_name'):
                text_info += f" ({result['hebrew_name']})"
            
            label = tk.Label(
                result_frame,
                text=text_info,
                font=("Arial", 10),
                bg="#FFFFFF",
                fg="#1F2937",
                cursor="hand2",
                anchor=tk.W,
                padx=10,
                pady=8
            )
            label.pack(fill=tk.X)
            
            # Bind click to load
            label.bind('<Button-1>', lambda e, r=result['name']: self._load_text_by_search_result(r))
            result_frame.bind('<Button-1>', lambda e, r=result['name']: self._load_text_by_search_result(r))
            
            # Hover effect
            def on_enter(e, frame=result_frame):
                frame.configure(bg="#EBF5FF")
            def on_leave(e, frame=result_frame):
                frame.configure(bg="#FFFFFF")
            
            label.bind('<Enter>', on_enter)
            label.bind('<Leave>', on_leave)
            result_frame.bind('<Enter>', on_enter)
            result_frame.bind('<Leave>', on_leave)
    
    def _hide_search_results(self):
        """Hide search results dropdown."""
        if self.search_results_frame:
            self.search_results_frame.destroy()
            self.search_results_frame = None
    
    def _focus_first_result(self):
        """Focus the first search result."""
        # TODO: Implement keyboard navigation
        pass
    
    def _load_text_by_name(self, text_name: str):
        """Load text by catalog name."""
        # Get reference from catalog
        reference = self.sefaria_manager.load_text_by_name(text_name, self.current_text_language)
        
        if reference:
            # Set in entry and load
            self.text_ref_entry.delete(0, tk.END)
            self.text_ref_entry.insert(0, reference)
            self._load_text()
    
    def _load_text_by_search_result(self, text_name: str):
        """Load text from search result click."""
        self._hide_search_results()
        self._load_text_by_name(text_name)
    
    def _create_text_display(self, parent):
        """Create source text display area."""
        text_frame = tk.LabelFrame(parent, text="Source Text", font=("Arial", 11, "bold"), 
                                   bg="#FFFFFF", fg="#374151")
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        self.text_display = scrolledtext.ScrolledText(
            text_frame,
            font=("Arial", 12),
            wrap=tk.WORD,
            bg="#FFFFFF",
            fg="#1F2937",
            relief=tk.SOLID,
            bd=1,
            height=15
        )
        self.text_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.text_display.config(state=tk.DISABLED)
    
    def _create_chat_section(self, parent):
        """Create AI chat section."""
        chat_frame = tk.LabelFrame(parent, text="Chat with Your Tutor", 
                                   font=("Arial", 11, "bold"), bg="#FFFFFF", fg="#374151")
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            font=("Arial", 11),
            wrap=tk.WORD,
            bg="#F9FAFB",
            fg="#1F2937",
            relief=tk.SOLID,
            bd=1,
            height=12
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))
        self.chat_display.config(state=tk.DISABLED)
        
        # Input area
        input_area = tk.Frame(chat_frame, bg="#FFFFFF")
        input_area.pack(fill=tk.X, padx=10, pady=10)
        
        self.question_input = tk.Text(
            input_area,
            font=("Arial", 11),
            wrap=tk.WORD,
            height=2,
            bg="#FFFFFF",
            fg="#1F2937",
            relief=tk.SOLID,
            bd=1
        )
        self.question_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        self.question_input.bind('<Control-Return>', lambda e: self._send_message())
        self.question_input.bind('<Return>', lambda e: self._handle_return())
        
        send_btn = tk.Button(
            input_area,
            text="Ask\n✓",
            command=self._send_message,
            bg="#8B5CF6",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2"
        )
        send_btn.pack(side=tk.LEFT)
    
    def _create_bottom_controls(self, parent):
        """Create bottom control buttons."""
        controls = tk.Frame(parent, bg="#F5F5F5")
        controls.pack(fill=tk.X)
        
        new_session_btn = tk.Button(
            controls,
            text="New Session",
            command=self._new_session,
            bg="#6B7280",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2"
        )
        new_session_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        generate_summary_btn = tk.Button(
            controls,
            text="Generate Summary",
            command=self._generate_summary,
            bg="#059669",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2"
        )
        generate_summary_btn.pack(side=tk.LEFT)
    
    def _bind_shortcuts(self):
        """Bind keyboard shortcuts."""
        self.root.bind('<Command-k>', lambda e: self._focus_input())
        self.root.bind('<Control-k>', lambda e: self._focus_input())
        self.root.bind('<Command-n>', lambda e: self._new_session())
        self.root.bind('<Control-n>', lambda e: self._new_session())
    
    def _focus_input(self):
        """Focus the question input field."""
        self.question_input.focus()
    
    def _handle_return(self, event=None):
        """Handle Enter key in question input."""
        # Send on Enter (can be changed to Ctrl+Enter if preferred)
        self._send_message()
        return "break"
    
    def _load_text(self):
        """Load Sefaria text."""
        reference = self.text_ref_entry.get().strip()
        if not reference:
            self._show_error("Please enter a text reference")
            return
        
        # Update language if needed
        language = "he" if self.current_text_language == "he" else "en"
        
        # Load text
        if self.app.load_sefaria_text(reference, language):
            self._display_text()
            self._add_message(f"Loaded: {reference} ({language})", "system")
        else:
            self._show_error(f"Could not load: {reference}")
    
    def _display_text(self):
        """Display the current text content."""
        content = self.app.get_current_text_content()
        if content:
            self.text_display.config(state=tk.NORMAL)
            self.text_display.delete(1.0, tk.END)
            self.text_display.insert(1.0, content)
            self.text_display.config(state=tk.DISABLED)
        else:
            self.text_display.config(state=tk.NORMAL)
            self.text_display.delete(1.0, tk.END)
            self.text_display.insert(1.0, "No text loaded. Load a Sefaria text above.")
            self.text_display.config(state=tk.DISABLED)
    
    def _toggle_language(self):
        """Toggle between English and Hebrew."""
        if self.current_text_language == "en":
            self.current_text_language = "he"
            self.lang_btn.config(text="HE", bg="#059669")
        else:
            self.current_text_language = "en"
            self.lang_btn.config(text="EN", bg="#10B981")
        
        # Reload text if we have a reference
        if self.text_ref_entry.get().strip():
            self._load_text()
    
    def _send_message(self):
        """Send a question to the AI tutor."""
        question = self.question_input.get(1.0, tk.END).strip()
        if not question:
            return
        
        # Clear input
        self.question_input.delete(1.0, tk.END)
        
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
        """Callback for AI responses."""
        # This is called from the app when AI responds
        pass
    
    def _generate_summary(self):
        """Generate session summary."""
        if not self.app.current_session:
            self._show_error("No active session")
            return
        
        if self.app.current_session.get_ai_interaction_count() < 3:
            self._show_error("Need at least 3 interactions to generate a summary")
            return
        
        self._add_message("Generating summary...", "system")
        
        # End session to trigger summary
        self.app.end_current_session()
        
        self._add_message("Session ended and summary generated!", "system")
    
    def _new_session(self):
        """Start a new session."""
        if self.app.current_session:
            # End current session
            self.app.end_current_session()
        
        # Start new session
        self.app.start_session()
        self.current_session = self.app.current_session
        
        # Clear chat
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        self._add_message("Started new session", "system")
    
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
        self.root.mainloop()


if __name__ == "__main__":
    gui = TutorGUI()
    gui.run()

