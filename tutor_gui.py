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
        self.sefaria_manager = SefariaManager()
        self.current_text_content = None
        self.current_text_language = "en"
        
        # Initialize app
        self.app = TutorApp(question_callback=self._on_ai_response)
        
        # Build UI
        self._setup_ui()
        
        # Bind keyboard shortcuts
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
        
        # Load text context (for LLM, not display)
        if self.app.load_sefaria_text(reference, language):
            self.current_reference = reference
            self.current_ref_label.config(text=reference)
            
            # Enable navigation buttons
            self.prev_btn.config(state=tk.NORMAL)
            self.next_btn.config(state=tk.NORMAL)
            
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
        
        # Reload text if we have a reference
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
        """Callback for AI responses."""
        # This is called from the app when AI responds
        pass
    
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

