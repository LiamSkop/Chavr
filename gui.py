#!/usr/bin/env python3
"""
Chavr GUI - Minimal Lovable Product Interface
Clean, simple GUI for speech recognition and transcription.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, font
import threading
import queue
from datetime import datetime
from main import ChavrApp
from sefaria_manager import SefariaManager


class ChavrGUI:
    """Main GUI application for Chavr speech recognition."""
    
    def __init__(self, model_size="medium", device="cpu", compute_type="int8", hebrew_only=False):
        """Initialize the GUI application."""
        self.root = tk.Tk()
        self.root.title("Chavr - Phase 8 Enhanced")
        self.root.geometry("800x900")
        self.root.minsize(700, 800)
        
        # Configure window properties
        self.root.configure(bg="#FFFFFF")
        
        # State management
        self.is_recording = False
        self.transcript_queue = queue.Queue()
        
        # Phase 8: Sefaria text integration
        self.sefaria_manager = SefariaManager()
        self.sefaria_manager.set_error_callback(self._show_error)
        self.current_text_reference = None
        self.current_text_language = "en"
        self.transcript_panel_collapsed = False
        
        # Phase 8: Autocomplete state
        self.autocomplete_listbox = None
        self.autocomplete_window = None
        
        # Initialize ChavrApp with callback and Phase 7 parameters
        self.app = ChavrApp(
            transcript_callback=self._on_transcript, 
            model_size=model_size,
            device=device,
            compute_type=compute_type,
            hebrew_only=hebrew_only
        )
        
        # Build UI components
        self._setup_ui()
        
        # Load last studied text
        self._load_last_text()
        
        # Start GUI update loop
        self._update_gui()
        
        # Bind keyboard shortcuts
        self._bind_shortcuts()
    
    def _setup_ui(self):
        """Setup the main UI layout."""
        # Main container with padding
        main_frame = tk.Frame(self.root, bg="#FFFFFF", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header with title and status indicator
        self._create_header(main_frame)
        
        # Phase 8: Text input section
        self._create_text_input_section(main_frame)
        
        # Phase 8: Main text display area
        self._create_text_display(main_frame)
        
        # Phase 8: Collapsible transcript panel
        self._create_transcript_panel(main_frame)
        
        # Status bar
        self._create_status_bar(main_frame)
    
    def _create_header(self, parent):
        """Create header with title and status indicator."""
        header_frame = tk.Frame(parent, bg="#FFFFFF")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Title
        title_label = tk.Label(
            header_frame,
            text="Chavr",
            font=("Helvetica", 24, "bold"),
            fg="#111827",
            bg="#FFFFFF"
        )
        title_label.pack(side=tk.LEFT)
        
        # Model info
        model_info = tk.Label(
            header_frame,
            text="Phase 8 Enhanced",
            font=("Helvetica", 10),
            fg="#6B7280",
            bg="#FFFFFF"
        )
        model_info.pack(side=tk.LEFT, padx=(10, 0))
        
        # Status indicator
        self.status_indicator = tk.Label(
            header_frame,
            text="●",
            font=("Helvetica", 16),
            fg="#E5E7EB",  # Inactive gray
            bg="#FFFFFF"
        )
        self.status_indicator.pack(side=tk.RIGHT)
    
    def _create_text_input_section(self, parent):
        """Create text input section with reference field and controls."""
        input_frame = tk.Frame(parent, bg="#FFFFFF")
        input_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Text reference input
        ref_label = tk.Label(
            input_frame,
            text="Text Reference:",
            font=("Helvetica", 12, "bold"),
            fg="#111827",
            bg="#FFFFFF"
        )
        ref_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Input field and buttons frame
        controls_frame = tk.Frame(input_frame, bg="#FFFFFF")
        controls_frame.pack(fill=tk.X)
        
        self.text_ref_entry = tk.Entry(
            controls_frame,
            font=("Helvetica", 12),
            relief="solid",
            bd=1,
            width=30
        )
        self.text_ref_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.text_ref_entry.bind('<Return>', lambda e: self._load_text())
        # Bind autocomplete events
        self.text_ref_entry.bind('<KeyRelease>', self._on_text_input_change)
        self.text_ref_entry.bind('<Down>', self._on_autocomplete_down)
        self.text_ref_entry.bind('<Escape>', self._hide_autocomplete)
        
        # Load text button
        self.load_text_btn = tk.Button(
            controls_frame,
            text="Load Text",
            command=self._load_text,
            bg="#3B82F6",  # Blue
            fg="#FFFFFF",
            font=("Helvetica", 11, "bold"),
            relief="flat",
            cursor="hand2",
            bd=0,
            padx=15,
            pady=8
        )
        self.load_text_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Language toggle button
        self.lang_toggle_btn = tk.Button(
            controls_frame,
            text="EN",
            command=self._toggle_language,
            bg="#10B981",  # Green
            fg="#FFFFFF",
            font=("Helvetica", 11, "bold"),
            relief="flat",
            cursor="hand2",
            bd=0,
            padx=15,
            pady=8
        )
        self.lang_toggle_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Record button (moved here)
        self.record_btn = tk.Button(
            controls_frame,
            text="START",
            command=self._toggle_recording,
            bg="#E5E7EB",  # Inactive gray
            fg="#111827",
            font=("Helvetica", 11, "bold"),
            relief="flat",
            cursor="hand2",
            bd=0,
            padx=15,
            pady=8
        )
        self.record_btn.pack(side=tk.RIGHT)
    
    def _create_text_display(self, parent):
        """Create the main text display area."""
        # Section header
        text_header = tk.Label(
            parent,
            text="Sefaria Text",
            font=("Helvetica", 14, "bold"),
            fg="#111827",
            bg="#FFFFFF"
        )
        text_header.pack(anchor=tk.W, pady=(0, 10))
        
        # Text display area with scrollbar
        text_frame = tk.Frame(parent, bg="#FFFFFF")
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        self.text_display = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            font=("Helvetica", 12),
            fg="#111827",
            bg="#FFFFFF",
            relief="solid",
            bd=1,
            padx=15,
            pady=15,
            state=tk.DISABLED,
            spacing1=3,  # Line spacing above
            spacing2=2,  # Line spacing between lines
            spacing3=3   # Line spacing below
        )
        self.text_display.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for different languages
        self.text_display.tag_configure("hebrew", font=("Arial Unicode MS", 12), justify='right')
        self.text_display.tag_configure("english", font=("Helvetica", 12))
        self.text_display.tag_configure("reference", foreground="#6B7280", font=("Helvetica", 11, "italic"))
    
    def _create_transcript_panel(self, parent):
        """Create the collapsible transcript display panel."""
        # Panel container
        self.transcript_panel = tk.Frame(parent, bg="#FFFFFF")
        self.transcript_panel.pack(fill=tk.X, pady=(0, 20))
        
        # Collapsible header with toggle button
        header_frame = tk.Frame(self.transcript_panel, bg="#F3F4F6", relief="solid", bd=1)
        header_frame.pack(fill=tk.X)
        
        self.transcript_toggle_btn = tk.Button(
            header_frame,
            text="▼ Live Transcript",
            command=self._toggle_transcript_panel,
            bg="#F3F4F6",
            fg="#111827",
            font=("Helvetica", 12, "bold"),
            relief="flat",
            cursor="hand2",
            bd=0,
            padx=10,
            pady=8,
            anchor=tk.W
        )
        self.transcript_toggle_btn.pack(fill=tk.X)
        
        # Transcript content frame (initially hidden)
        self.transcript_content_frame = tk.Frame(self.transcript_panel, bg="#FFFFFF")
        # Don't pack initially - will be shown/hidden by toggle
        
        # Transcript text area with scrollbar
        self.transcript_text = scrolledtext.ScrolledText(
            self.transcript_content_frame,
            wrap=tk.WORD,
            font=("Helvetica", 11),
            fg="#111827",
            bg="#FFFFFF",
            relief="solid",
            bd=1,
            padx=10,
            pady=10,
            state=tk.DISABLED,
            height=8,  # Fixed height for collapsible panel
            spacing1=2,  # Line spacing above
            spacing2=2,  # Line spacing between lines
            spacing3=2   # Line spacing below
        )
        self.transcript_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for different languages
        self.transcript_text.tag_configure("timestamp", foreground="#6B7280", font=("Helvetica", 10))
        self.transcript_text.tag_configure("language", foreground="#10B981", font=("Helvetica", 10, "bold"))
        self.transcript_text.tag_configure("hebrew", font=("Helvetica", 11))
        self.transcript_text.tag_configure("english", font=("Helvetica", 11))
    
    def _create_status_bar(self, parent):
        """Create the status bar with session info."""
        # Determine model type for display
        model_type = "Fine-tuned Hebrew" if self.app.faster_whisper_adapter else "OpenAI Whisper"
        device_info = f"({self.app.device})" if hasattr(self.app, 'device') else ""
        
        self.status_bar = tk.Label(
            parent,
            text=f"Ready to record - {model_type} {device_info}",
            font=("Helvetica", 11),
            fg="#6B7280",
            bg="#FFFFFF",
            anchor=tk.W
        )
        self.status_bar.pack(fill=tk.X, pady=(10, 0))
    
    def _load_text(self):
        """Load text from Sefaria."""
        reference = self.text_ref_entry.get().strip()
        if not reference:
            self._show_error("Please enter a text reference")
            return
        
        # Disable load button during loading
        self.load_text_btn.configure(state=tk.DISABLED, text="Loading...")
        self.status_bar.configure(text="Loading text...")
        
        # Load text asynchronously
        self.sefaria_manager.fetch_text_async(
            reference, 
            self.current_text_language, 
            self._on_text_loaded
        )
    
    def _on_text_loaded(self, text_data):
        """Callback for when text is loaded."""
        # Re-enable load button
        self.load_text_btn.configure(state=tk.NORMAL, text="Load Text")
        
        if text_data:
            # Update display
            self._display_text(text_data)
            
            # Save reference and update session
            reference = self.text_ref_entry.get().strip()
            self.current_text_reference = reference
            self.sefaria_manager.save_last_text(reference, self.current_text_language)
            
            # Update session if recording
            if self.app.current_session:
                self.app.current_session.set_sefaria_text(reference, self.current_text_language)
            
            self.status_bar.configure(text=f"Loaded: {reference}")
        else:
            self._show_error("Failed to load text")
    
    def _display_text(self, text_data):
        """Display text in the main text area."""
        import re
        
        self.text_display.configure(state=tk.NORMAL)
        self.text_display.delete(1.0, tk.END)
        
        # Extract text content from Sefaria response based on language selection
        content = None
        if isinstance(text_data, dict):
            if self.current_text_language == 'he':
                # Try Hebrew fields in order of preference
                content = text_data.get('he') or text_data.get('hebrew') or text_data.get('text')
            else:
                # Try English fields in order of preference  
                content = text_data.get('text') or text_data.get('en') or text_data.get('english')
            
            # Fallback if no content found
            if not content:
                content = str(text_data)
        else:
            content = str(text_data)
        
        # Add reference header
        reference = self.text_ref_entry.get().strip()
        self.text_display.insert(tk.END, f"{reference} ({self.current_text_language.upper()})\n\n", "reference")
        
        # Process content: handle lists and strip HTML
        if isinstance(content, list):
            # Join verses with double newlines, strip HTML from each verse
            verses = []
            for i, verse in enumerate(content, 1):
                # Remove HTML tags
                clean_verse = re.sub(r'<[^>]+>', '', str(verse))
                # Add verse number and text
                verses.append(f"{i}. {clean_verse.strip()}")
            final_text = '\n\n'.join(verses)
        elif isinstance(content, str):
            # Strip HTML tags from string content
            final_text = re.sub(r'<[^>]+>', '', content)
        else:
            final_text = str(content)
        
        # Add text content with appropriate tag
        if self.current_text_language in ['he', 'iw']:
            self.text_display.insert(tk.END, final_text, "hebrew")
        else:
            self.text_display.insert(tk.END, final_text, "english")
        
        self.text_display.configure(state=tk.DISABLED)
        self.text_display.see(1.0)  # Scroll to top
    
    def _toggle_language(self):
        """Toggle between English and Hebrew."""
        if self.current_text_language == "en":
            self.current_text_language = "he"
            self.lang_toggle_btn.configure(text="HE")
        else:
            self.current_text_language = "en"
            self.lang_toggle_btn.configure(text="EN")
        
        # Reload current text in new language
        if self.current_text_reference:
            self._load_text()
    
    def _toggle_transcript_panel(self):
        """Toggle transcript panel visibility."""
        if self.transcript_panel_collapsed:
            # Show panel
            self.transcript_content_frame.pack(fill=tk.X, pady=(0, 0))
            self.transcript_toggle_btn.configure(text="▼ Live Transcript")
            self.transcript_panel_collapsed = False
        else:
            # Hide panel
            self.transcript_content_frame.pack_forget()
            self.transcript_toggle_btn.configure(text="▶ Live Transcript")
            self.transcript_panel_collapsed = True
    
    def _load_last_text(self):
        """Load last studied text on startup."""
        reference, language = self.sefaria_manager.load_last_text()
        if reference and language:
            self.text_ref_entry.insert(0, reference)
            self.current_text_language = language
            self.lang_toggle_btn.configure(text=language.upper())
            # Auto-load the text
            self._load_text()
    
    def _on_text_input_change(self, event):
        """Handle text input changes for autocomplete."""
        # Ignore special keys
        if event.keysym in ['Down', 'Up', 'Return', 'Escape', 'Left', 'Right']:
            return
        
        query = self.text_ref_entry.get().strip()
        
        if len(query) < 2:
            self._hide_autocomplete()
            return
        
        # Search for completions in background
        def search_and_show():
            results = self.sefaria_manager.search_text_names(query)
            if results:
                self.root.after(0, lambda: self._show_autocomplete(results))
            else:
                self.root.after(0, self._hide_autocomplete)
        
        threading.Thread(target=search_and_show, daemon=True).start()

    def _show_autocomplete(self, results):
        """Show autocomplete dropdown with results."""
        self._hide_autocomplete()  # Clear any existing
        
        if not results:
            return
        
        # Create toplevel window for dropdown
        self.autocomplete_window = tk.Toplevel(self.root)
        self.autocomplete_window.wm_overrideredirect(True)
        self.autocomplete_window.configure(bg="#FFFFFF")
        
        # Ensure entry field is rendered before getting position
        self.text_ref_entry.update_idletasks()
        
        x = self.text_ref_entry.winfo_rootx()
        y = self.text_ref_entry.winfo_rooty() + self.text_ref_entry.winfo_height() + 2
        width = self.text_ref_entry.winfo_width()
        
        self.autocomplete_window.wm_geometry(f"+{x}+{y}")
        
        # Create listbox
        self.autocomplete_listbox = tk.Listbox(
            self.autocomplete_window,
            height=min(len(results), 8),
            width=30,  # Fixed width in characters (matches entry field)
            font=("Helvetica", 11),
            relief="solid",
            bd=1,
            bg="#FFFFFF",           # White background
            fg="#000000",           # Black text
            selectbackground="#4A90E2",  # Blue selection
            selectforeground="#FFFFFF",   # White selected text
            highlightthickness=0
        )
        self.autocomplete_listbox.pack()
        
        # Populate with results
        for result in results:
            self.autocomplete_listbox.insert(tk.END, result)
        
        # Bind selection events
        self.autocomplete_listbox.bind('<Button-1>', self._on_autocomplete_select)
        self.autocomplete_listbox.bind('<Return>', self._on_autocomplete_select)
        
        # Focus on first item and ensure visibility
        if results:
            self.autocomplete_listbox.selection_set(0)
            self.autocomplete_listbox.activate(0)
            # Force the listbox to update and show content
            self.autocomplete_listbox.update_idletasks()
            self.autocomplete_listbox.see(0)  # Ensure first item is visible
        
        # Add binding to close on focus out
        self.autocomplete_window.bind('<FocusOut>', self._hide_autocomplete)
        
        # Force the window to update and render properly
        self.autocomplete_window.update_idletasks()
        self.autocomplete_window.lift()  # Bring to front

    def _hide_autocomplete(self, event=None):
        """Hide autocomplete dropdown."""
        if self.autocomplete_window:
            self.autocomplete_window.destroy()
            self.autocomplete_window = None
            self.autocomplete_listbox = None

    def _on_autocomplete_select(self, event):
        """Handle autocomplete selection."""
        if not self.autocomplete_listbox:
            return
        
        selection = self.autocomplete_listbox.curselection()
        if selection:
            selected_text = self.autocomplete_listbox.get(selection[0])
            self.text_ref_entry.delete(0, tk.END)
            self.text_ref_entry.insert(0, selected_text)
            self._hide_autocomplete()
            # Auto-load the selected text
            self._load_text()

    def _on_autocomplete_down(self, event):
        """Handle down arrow to move to autocomplete list."""
        if self.autocomplete_listbox and self.autocomplete_window:
            self.autocomplete_listbox.focus_set()
            return 'break'
    
    def _toggle_recording(self):
        """Toggle recording state."""
        if not self.is_recording:
            self._start_recording()
        else:
            self._stop_recording()
    
    def _start_recording(self):
        """Start recording."""
        try:
            self.app.start_continuous_listening()
            self.is_recording = True
            
            # Update UI
            self.record_btn.configure(
                text="STOP",
                bg="#10B981",  # Green for active
                fg="#FFFFFF"
            )
            self.status_indicator.configure(fg="#10B981")
            
            # Set Sefaria text in session if available
            if self.current_text_reference and self.app.current_session:
                self.app.current_session.set_sefaria_text(
                    self.current_text_reference, 
                    self.current_text_language
                )
            
            self.status_bar.configure(text="Recording...")
            
        except Exception as e:
            self._show_error(f"Failed to start recording: {e}")
    
    def _stop_recording(self):
        """Stop recording."""
        try:
            self.app.stop_continuous_listening()
            self.is_recording = False
            
            # Update UI
            self.record_btn.configure(
                text="START",
                bg="#E5E7EB",  # Gray for inactive
                fg="#111827"
            )
            self.status_indicator.configure(fg="#E5E7EB")
            self.status_bar.configure(text="Session saved")
            
        except Exception as e:
            self._show_error(f"Failed to stop recording: {e}")
    
    def _on_transcript(self, text, language, timestamp):
        """Callback for new transcript from ChavrApp."""
        if text == "PROCESSING":
            # Show processing indicator
            self.status_bar.configure(text="Processing speech...")
        else:
            self.transcript_queue.put((text, language, timestamp))
            self.status_bar.configure(text="Recording...")
    
    def _update_gui(self):
        """Update GUI elements (called periodically)."""
        # Process transcript queue
        while not self.transcript_queue.empty():
            try:
                text, language, timestamp = self.transcript_queue.get_nowait()
                self._add_transcript(text, language, timestamp)
            except queue.Empty:
                break
        
        # Update status bar
        if self.is_recording and self.app.current_session:
            duration = self.app.current_session.duration
            transcript_count = self.app.current_session.get_transcript_count()
            self.status_bar.configure(
                text=f"Recording... Session: {duration:.0f}s | {transcript_count} transcripts"
            )
        
        # Schedule next update
        self.root.after(100, self._update_gui)
    
    def _add_transcript(self, text, language, timestamp):
        """Add a new transcript to the display."""
        self.transcript_text.configure(state=tk.NORMAL)
        
        # Format timestamp
        time_str = timestamp.strftime("%H:%M:%S")
        
        # Format language name
        lang_name = self.app.supported_languages.get(language, language)
        
        # Add transcript with formatting
        self.transcript_text.insert(tk.END, f"[{time_str}] ", "timestamp")
        self.transcript_text.insert(tk.END, f"[{lang_name}] ", "language")
        
        # Add text with language-specific formatting
        if language in ['he', 'iw']:
            self.transcript_text.insert(tk.END, f"{text}\n", "hebrew")
        else:
            self.transcript_text.insert(tk.END, f"{text}\n", "english")
        
        # Auto-scroll to bottom
        self.transcript_text.see(tk.END)
        self.transcript_text.configure(state=tk.DISABLED)
    
    def _show_error(self, message):
        """Show error message in status bar."""
        self.status_bar.configure(text=f"Error: {message}")
        # Reset after 3 seconds
        self.root.after(3000, lambda: self.status_bar.configure(text="Ready to record"))
    
    def _bind_shortcuts(self):
        """Bind keyboard shortcuts."""
        # Space bar to toggle recording
        self.root.bind('<space>', lambda e: self._toggle_recording())
        
        # Cmd/Ctrl+Q to quit
        self.root.bind('<Command-q>', lambda e: self._quit())
        self.root.bind('<Control-q>', lambda e: self._quit())
        
        # Cmd/Ctrl+L to load text
        self.root.bind('<Command-l>', lambda e: self._load_text())
        self.root.bind('<Control-l>', lambda e: self._load_text())
        
        # Cmd/Ctrl+T to toggle language
        self.root.bind('<Command-t>', lambda e: self._toggle_language())
        self.root.bind('<Control-t>', lambda e: self._toggle_language())
        
        # Make sure space bar doesn't interfere with text widgets
        self.transcript_text.bind('<space>', lambda e: "break")
        self.text_display.bind('<space>', lambda e: "break")
    
    def _quit(self):
        """Clean quit with proper cleanup."""
        if self.is_recording:
            self._stop_recording()
        
        # Cleanup ChavrApp
        if hasattr(self.app, 'cleanup'):
            self.app.cleanup()
        
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """Run the GUI application."""
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self._quit)
        
        # Start the GUI
        self.root.mainloop()


def main():
    """Main function to run the GUI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Chavr GUI - Phase 8 Enhanced")
    parser.add_argument('--model', choices=['tiny', 'base', 'small', 'medium', 'large'], 
                       default='medium', help='Whisper model size (default: medium)')
    parser.add_argument('--device', choices=['cpu', 'cuda'], default='cpu',
                       help='Device to use for faster-whisper (default: cpu)')
    parser.add_argument('--compute', choices=['int8', 'float16'], default='int8',
                       help='Compute type for faster-whisper (default: int8)')
    parser.add_argument('--hebrew-only', action='store_true',
                       help='Force Hebrew-only mode for accuracy testing')
    args = parser.parse_args()
    
    try:
        gui = ChavrGUI(
            model_size=args.model,
            device=args.device,
            compute_type=args.compute,
            hebrew_only=args.hebrew_only
        )
        gui.run()
    except Exception as e:
        print(f"Failed to start GUI: {e}")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()
