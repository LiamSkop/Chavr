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


class ChavrGUI:
    """Main GUI application for Chavr speech recognition."""
    
    def __init__(self, model_size="medium"):
        """Initialize the GUI application."""
        self.root = tk.Tk()
        self.root.title("Chavr")
        self.root.geometry("600x700")
        self.root.minsize(500, 600)
        
        # Configure window properties
        self.root.configure(bg="#FFFFFF")
        
        # State management
        self.is_recording = False
        self.transcript_queue = queue.Queue()
        
        # Initialize ChavrApp with callback and model size
        self.app = ChavrApp(transcript_callback=self._on_transcript, model_size=model_size)
        
        # Build UI components
        self._setup_ui()
        
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
        
        # Large record button
        self._create_record_button(main_frame)
        
        # Transcript display area
        self._create_transcript_display(main_frame)
        
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
        
        # Status indicator
        self.status_indicator = tk.Label(
            header_frame,
            text="●",
            font=("Helvetica", 16),
            fg="#E5E7EB",  # Inactive gray
            bg="#FFFFFF"
        )
        self.status_indicator.pack(side=tk.RIGHT)
    
    def _create_record_button(self, parent):
        """Create the large record/stop button."""
        button_frame = tk.Frame(parent, bg="#FFFFFF")
        button_frame.pack(pady=40)
        
        self.record_btn = tk.Button(
            button_frame,
            text="START",
            command=self._toggle_recording,
            bg="#E5E7EB",  # Inactive gray
            fg="#111827",
            font=("Helvetica", 16, "bold"),
            width=12,
            height=3,
            relief="flat",
            cursor="hand2",
            bd=0,
            padx=20,
            pady=10
        )
        self.record_btn.pack()
    
    def _create_transcript_display(self, parent):
        """Create the transcript display area."""
        # Section header
        transcript_header = tk.Label(
            parent,
            text="Live Transcript",
            font=("Helvetica", 14, "bold"),
            fg="#111827",
            bg="#FFFFFF"
        )
        transcript_header.pack(anchor=tk.W, pady=(20, 10))
        
        # Transcript text area with scrollbar
        text_frame = tk.Frame(parent, bg="#FFFFFF")
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        self.transcript_text = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            font=("Helvetica", 12),
            fg="#111827",
            bg="#FFFFFF",
            relief="flat",
            bd=0,
            padx=10,
            pady=10,
            state=tk.DISABLED,
            spacing1=2,  # Line spacing above
            spacing2=2,  # Line spacing between lines
            spacing3=2   # Line spacing below
        )
        self.transcript_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for different languages
        self.transcript_text.tag_configure("timestamp", foreground="#6B7280", font=("Helvetica", 11))
        self.transcript_text.tag_configure("language", foreground="#10B981", font=("Helvetica", 11, "bold"))
        self.transcript_text.tag_configure("hebrew", font=("Helvetica", 12))
        self.transcript_text.tag_configure("english", font=("Helvetica", 12))
    
    def _create_status_bar(self, parent):
        """Create the status bar with session info."""
        self.status_bar = tk.Label(
            parent,
            text="Ready to record",
            font=("Helvetica", 11),
            fg="#6B7280",
            bg="#FFFFFF",
            anchor=tk.W
        )
        self.status_bar.pack(fill=tk.X, pady=(10, 0))
    
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
        
        # Make sure space bar doesn't interfere with text widget
        self.transcript_text.bind('<space>', lambda e: "break")
    
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
    try:
        gui = ChavrGUI()
        gui.run()
    except Exception as e:
        print(f"Failed to start GUI: {e}")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()
