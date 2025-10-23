# Step 19: GUI AI Chat Panel - Implementation Plan

## Goal
Create a comprehensive GUI AI chat panel with collapsible design, multi-line input, dedicated summary panel, and seamless integration with existing GUI layout.

## User Requirements Summary
Based on clarifications:
- **Layout**: Below transcript panel (as planned)
- **Message Style**: User messages (right-aligned, blue), AI messages (left-aligned, gray)
- **Input**: Multi-line text area (like a chat input)
- **Summary Display**: Separate dedicated summary panel
- **Chat History**: Load when session is loaded from file
- **Status Indicators**: Animated spinner/loading indicator
- **Error Handling**: Show errors in chat panel as red text
- **Collapsibility**: Collapsible with expand/collapse button
- **Layout Changes**: Redesign layout to accommodate AI features better
- **Real-time Updates**: Immediate updates + auto-scroll to latest message

## Implementation Plan

### 1. Redesign GUI Layout Structure

**File:** `gui.py`

Create new layout structure to accommodate AI features:

```python
def _setup_ui(self):
    """Setup the main UI layout with AI chat panel."""
    # Main container with padding
    main_frame = tk.Frame(self.root, bg="#FFFFFF", padx=20, pady=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Header with title and status indicator
    self._create_header(main_frame)
    
    # Phase 8: Text input section
    self._create_text_input_section(main_frame)
    
    # Phase 8: Main text display area
    self._create_text_display(main_frame)
    
    # Phase 9: AI Chat Panel (collapsible)
    self._create_ai_chat_panel(main_frame)
    
    # Phase 9: AI Summary Panel (separate, collapsible)
    self._create_ai_summary_panel(main_frame)
    
    # Control buttons
    self._create_control_buttons(main_frame)
    
    # Status bar
    self._create_status_bar(main_frame)
```

### 2. Create AI Chat Panel

**File:** `gui.py`

```python
def _create_ai_chat_panel(self, parent):
    """Create the collapsible AI chat panel."""
    # Chat panel container
    self.ai_chat_frame = tk.Frame(parent, bg="#F8F9FA", relief=tk.RAISED, bd=1)
    self.ai_chat_frame.pack(fill=tk.X, pady=(10, 0))
    
    # Chat panel header with collapse/expand button
    chat_header = tk.Frame(self.ai_chat_frame, bg="#E9ECEF", height=40)
    chat_header.pack(fill=tk.X)
    chat_header.pack_propagate(False)
    
    # Collapse/expand button
    self.ai_chat_collapsed = False
    self.ai_chat_toggle_btn = tk.Button(
        chat_header,
        text="▼ AI Chavruta",
        command=self._toggle_ai_chat,
        bg="#E9ECEF",
        fg="#495057",
        font=("Arial", 10, "bold"),
        relief=tk.FLAT,
        bd=0
    )
    self.ai_chat_toggle_btn.pack(side=tk.LEFT, padx=10, pady=8)
    
    # AI status indicator
    self.ai_status_label = tk.Label(
        chat_header,
        text="Ready",
        bg="#E9ECEF",
        fg="#28A745",
        font=("Arial", 9)
    )
    self.ai_status_label.pack(side=tk.RIGHT, padx=10, pady=8)
    
    # Chat messages area (scrollable)
    self.ai_chat_container = tk.Frame(self.ai_chat_frame, bg="#FFFFFF")
    self.ai_chat_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Create scrollable chat area
    self.ai_chat_canvas = tk.Canvas(
        self.ai_chat_container,
        bg="#FFFFFF",
        highlightthickness=0
    )
    self.ai_chat_scrollbar = tk.Scrollbar(
        self.ai_chat_container,
        orient=tk.VERTICAL,
        command=self.ai_chat_canvas.yview
    )
    self.ai_chat_scrollable_frame = tk.Frame(self.ai_chat_canvas, bg="#FFFFFF")
    
    self.ai_chat_canvas.configure(yscrollcommand=self.ai_chat_scrollbar.set)
    self.ai_chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    self.ai_chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Bind mousewheel to canvas
    self.ai_chat_canvas.bind("<MouseWheel>", self._on_chat_scroll)
    
    # Chat input area
    self._create_chat_input_area()
    
    # Initially collapsed
    self._toggle_ai_chat()

def _create_chat_input_area(self):
    """Create the chat input area with multi-line text."""
    input_frame = tk.Frame(self.ai_chat_frame, bg="#F8F9FA", height=80)
    input_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
    input_frame.pack_propagate(False)
    
    # Multi-line text input
    self.ai_input_text = tk.Text(
        input_frame,
        height=3,
        wrap=tk.WORD,
        font=("Arial", 10),
        bg="#FFFFFF",
        fg="#212529",
        relief=tk.SUNKEN,
        bd=1
    )
    self.ai_input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
    
    # Input buttons frame
    buttons_frame = tk.Frame(input_frame, bg="#F8F9FA")
    buttons_frame.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Ask Chavr button
    self.ask_chavr_btn = tk.Button(
        buttons_frame,
        text="Ask Chavr",
        command=self._ask_chavr_manual,
        bg="#007BFF",
        fg="white",
        font=("Arial", 9, "bold"),
        relief=tk.RAISED,
        bd=1,
        padx=10,
        pady=5
    )
    self.ask_chavr_btn.pack(fill=tk.X, pady=(0, 5))
    
    # Clear button
    self.clear_chat_btn = tk.Button(
        buttons_frame,
        text="Clear",
        command=self._clear_chat,
        bg="#6C757D",
        fg="white",
        font=("Arial", 9),
        relief=tk.RAISED,
        bd=1,
        padx=10,
        pady=5
    )
    self.clear_chat_btn.pack(fill=tk.X)
    
    # Bind Enter key to send (Ctrl+Enter for new line)
    self.ai_input_text.bind("<Return>", self._on_input_return)
    self.ai_input_text.bind("<Control-Return>", self._on_input_ctrl_return)
```

### 3. Create AI Summary Panel

**File:** `gui.py`

```python
def _create_ai_summary_panel(self, parent):
    """Create the separate AI summary panel."""
    # Summary panel container
    self.ai_summary_frame = tk.Frame(parent, bg="#F0F8FF", relief=tk.RAISED, bd=1)
    self.ai_summary_frame.pack(fill=tk.X, pady=(5, 0))
    
    # Summary panel header
    summary_header = tk.Frame(self.ai_summary_frame, bg="#D1ECF1", height=35)
    summary_header.pack(fill=tk.X)
    summary_header.pack_propagate(False)
    
    # Summary toggle button
    self.ai_summary_collapsed = True
    self.ai_summary_toggle_btn = tk.Button(
        summary_header,
        text="▶ Session Summary",
        command=self._toggle_ai_summary,
        bg="#D1ECF1",
        fg="#0C5460",
        font=("Arial", 9, "bold"),
        relief=tk.FLAT,
        bd=0
    )
    self.ai_summary_toggle_btn.pack(side=tk.LEFT, padx=10, pady=6)
    
    # Generate summary button
    self.generate_summary_btn = tk.Button(
        summary_header,
        text="Generate Summary",
        command=self._generate_summary_manual,
        bg="#17A2B8",
        fg="white",
        font=("Arial", 8),
        relief=tk.RAISED,
        bd=1,
        padx=8,
        pady=3
    )
    self.generate_summary_btn.pack(side=tk.RIGHT, padx=10, pady=6)
    
    # Summary content area
    self.ai_summary_content = tk.Text(
        self.ai_summary_frame,
        height=6,
        wrap=tk.WORD,
        font=("Arial", 10),
        bg="#FFFFFF",
        fg="#212529",
        relief=tk.SUNKEN,
        bd=1,
        state=tk.DISABLED
    )
    
    # Initially collapsed
    self._toggle_ai_summary()
```

### 4. Implement Chat Panel Functionality

**File:** `gui.py`

```python
def _toggle_ai_chat(self):
    """Toggle AI chat panel visibility."""
    if self.ai_chat_collapsed:
        # Expand
        self.ai_chat_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.ai_chat_toggle_btn.configure(text="▼ AI Chavruta")
        self.ai_chat_collapsed = False
    else:
        # Collapse
        self.ai_chat_container.pack_forget()
        self.ai_chat_toggle_btn.configure(text="▶ AI Chavruta")
        self.ai_chat_collapsed = True

def _toggle_ai_summary(self):
    """Toggle AI summary panel visibility."""
    if self.ai_summary_collapsed:
        # Expand
        self.ai_summary_content.pack(fill=tk.X, padx=5, pady=5)
        self.ai_summary_toggle_btn.configure(text="▼ Session Summary")
        self.ai_summary_collapsed = False
    else:
        # Collapse
        self.ai_summary_content.pack_forget()
        self.ai_summary_toggle_btn.configure(text="▶ Session Summary")
        self.ai_summary_collapsed = True

def _ask_chavr_manual(self):
    """Handle manual 'Ask Chavr' button click."""
    question = self.ai_input_text.get("1.0", tk.END).strip()
    if not question:
        self._show_error("Please enter a question")
        return
    
    # Clear input
    self.ai_input_text.delete("1.0", tk.END)
    
    # Add user message to chat
    self._add_chat_message(question, "user")
    
    # Set status to processing
    self._set_ai_status("Processing...", "#FFC107")
    
    # Disable button during processing
    self.ask_chavr_btn.configure(state=tk.DISABLED)
    
    # Process question through AI
    if hasattr(self.app, 'gemini_manager') and self.app.gemini_manager:
        # Use existing AI processing
        from datetime import datetime
        timestamp = datetime.now()
        self.app._handle_ai_question(question, timestamp)
    else:
        self._add_chat_message("AI not available (no API key)", "error")
        self._set_ai_status("Not Available", "#DC3545")
        self.ask_chavr_btn.configure(state=tk.NORMAL)

def _generate_summary_manual(self):
    """Handle manual summary generation."""
    if not self.app.current_session:
        self._show_error("No active session to summarize")
        return
    
    if self.app.current_session.get_transcript_count() < 5:
        self._show_error("Need at least 5 transcripts to generate summary")
        return
    
    # Set status to processing
    self._set_ai_status("Generating Summary...", "#FFC107")
    self.generate_summary_btn.configure(state=tk.DISABLED)
    
    # Generate summary
    if hasattr(self.app, 'gemini_manager') and self.app.gemini_manager:
        try:
            summary = self.app.gemini_manager.generate_session_summary(self.app.current_session)
            if summary:
                self.app.current_session.set_ai_summary(summary)
                self._display_summary(summary)
                self._set_ai_status("Summary Generated", "#28A745")
            else:
                self._show_error("Failed to generate summary")
                self._set_ai_status("Failed", "#DC3545")
        except Exception as e:
            self._show_error(f"Error generating summary: {e}")
            self._set_ai_status("Error", "#DC3545")
    else:
        self._show_error("AI not available (no API key)")
        self._set_ai_status("Not Available", "#DC3545")
    
    self.generate_summary_btn.configure(state=tk.NORMAL)

def _add_chat_message(self, text: str, sender: str):
    """Add a message to the chat panel."""
    # Create message frame
    message_frame = tk.Frame(self.ai_chat_scrollable_frame, bg="#FFFFFF")
    message_frame.pack(fill=tk.X, padx=5, pady=2)
    
    # Configure alignment and colors based on sender
    if sender == "user":
        align = tk.RIGHT
        bg_color = "#007BFF"
        fg_color = "white"
        label_text = "You"
    elif sender == "ai":
        align = tk.LEFT
        bg_color = "#6C757D"
        fg_color = "white"
        label_text = "AI Chavruta"
    elif sender == "error":
        align = tk.LEFT
        bg_color = "#DC3545"
        fg_color = "white"
        label_text = "Error"
    else:
        align = tk.LEFT
        bg_color = "#6C757D"
        fg_color = "white"
        label_text = sender
    
    # Message bubble
    bubble_frame = tk.Frame(message_frame, bg=bg_color, relief=tk.RAISED, bd=1)
    if align == tk.RIGHT:
        bubble_frame.pack(side=tk.RIGHT, padx=(50, 5))
    else:
        bubble_frame.pack(side=tk.LEFT, padx=(5, 50))
    
    # Message text
    message_label = tk.Label(
        bubble_frame,
        text=text,
        bg=bg_color,
        fg=fg_color,
        font=("Arial", 10),
        wraplength=400,
        justify=tk.LEFT
    )
    message_label.pack(padx=10, pady=5)
    
    # Timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M")
    time_label = tk.Label(
        message_frame,
        text=f"{label_text} • {timestamp}",
        bg="#FFFFFF",
        fg="#6C757D",
        font=("Arial", 8)
    )
    if align == tk.RIGHT:
        time_label.pack(side=tk.RIGHT, padx=(50, 5))
    else:
        time_label.pack(side=tk.LEFT, padx=(5, 50))
    
    # Update canvas scroll region
    self.ai_chat_canvas.update_idletasks()
    self.ai_chat_canvas.configure(scrollregion=self.ai_chat_canvas.bbox("all"))
    
    # Auto-scroll to bottom
    self.ai_chat_canvas.yview_moveto(1.0)

def _display_summary(self, summary: str):
    """Display summary in the summary panel."""
    self.ai_summary_content.configure(state=tk.NORMAL)
    self.ai_summary_content.delete("1.0", tk.END)
    self.ai_summary_content.insert("1.0", summary)
    self.ai_summary_content.configure(state=tk.DISABLED)
    
    # Expand summary panel if collapsed
    if self.ai_summary_collapsed:
        self._toggle_ai_summary()

def _set_ai_status(self, status: str, color: str):
    """Set AI status indicator."""
    self.ai_status_label.configure(text=status, fg=color)

def _clear_chat(self):
    """Clear the chat panel."""
    for widget in self.ai_chat_scrollable_frame.winfo_children():
        widget.destroy()
    self.ai_chat_canvas.configure(scrollregion=self.ai_chat_canvas.bbox("all"))

def _on_input_return(self, event):
    """Handle Enter key in input (send message)."""
    self._ask_chavr_manual()
    return "break"  # Prevent default behavior

def _on_input_ctrl_return(self, event):
    """Handle Ctrl+Enter (new line)."""
    # Allow default behavior (new line)
    pass

def _on_chat_scroll(self, event):
    """Handle mousewheel scrolling in chat."""
    self.ai_chat_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
```

### 5. Integrate AI Callback Handling

**File:** `gui.py`

```python
def _on_transcript(self, text: str, language: str, timestamp):
    """Enhanced transcript callback to handle AI responses."""
    # Existing transcript handling
    if language == 'ai':
        # This is an AI response
        self._add_chat_message(text, "ai")
        self._set_ai_status("Ready", "#28A745")
        self.ask_chavr_btn.configure(state=tk.NORMAL)
    else:
        # Regular transcript
        # ... existing transcript display logic ...
        pass

def _load_session_chat_history(self, session):
    """Load chat history when session is loaded."""
    if not session:
        return
    
    # Clear existing chat
    self._clear_chat()
    
    # Load AI interactions
    if hasattr(session, 'ai_interactions') and session.ai_interactions:
        for interaction in session.ai_interactions:
            # Add user question
            self._add_chat_message(interaction['question'], "user")
            # Add AI response
            self._add_chat_message(interaction['response'], "ai")
    
    # Load summary if available
    if hasattr(session, 'ai_summary') and session.ai_summary:
        self._display_summary(session.ai_summary)
```

### 6. Update Session Loading

**File:** `gui.py`

```python
def _load_session(self, session_id: str):
    """Load a session and its chat history."""
    # ... existing session loading logic ...
    
    # Load chat history
    self._load_session_chat_history(self.current_session)
```

### 7. Add Loading Animation

**File:** `gui.py`

```python
def _show_loading_animation(self):
    """Show loading animation in AI status."""
    import threading
    import time
    
    def animate():
        dots = ["Processing", "Processing.", "Processing..", "Processing..."]
        i = 0
        while hasattr(self, '_loading') and self._loading:
            self.ai_status_label.configure(text=dots[i % len(dots)])
            i += 1
            time.sleep(0.5)
    
    self._loading = True
    self.loading_thread = threading.Thread(target=animate)
    self.loading_thread.daemon = True
    self.loading_thread.start()

def _hide_loading_animation(self):
    """Hide loading animation."""
    self._loading = False
```

## Testing Strategy

### Unit Tests

Create `test_gui_ai_integration.py`:

```python
#!/usr/bin/env python3
"""Test GUI AI integration"""

import tkinter as tk
from gui import ChavrGUI

def test_chat_panel_creation():
    """Test AI chat panel creation."""
    root = tk.Tk()
    gui = ChavrGUI(root)
    
    # Test panel exists
    assert hasattr(gui, 'ai_chat_frame')
    assert hasattr(gui, 'ai_chat_toggle_btn')
    assert hasattr(gui, 'ai_input_text')
    
    root.destroy()
    print("✓ Chat panel creation test passed")

def test_message_display():
    """Test message display functionality."""
    root = tk.Tk()
    gui = ChavrGUI(root)
    
    # Test adding messages
    gui._add_chat_message("Test question", "user")
    gui._add_chat_message("Test response", "ai")
    
    root.destroy()
    print("✓ Message display test passed")

if __name__ == "__main__":
    test_chat_panel_creation()
    test_message_display()
```

## Files Modified

1. **`gui.py`** - Complete GUI redesign with AI chat panel
2. **`test_gui_ai_integration.py`** (new) - GUI AI tests

## Acceptance Criteria

- [ ] AI chat panel below transcript panel
- [ ] User messages (right-aligned, blue), AI messages (left-aligned, gray)
- [ ] Multi-line text input for questions
- [ ] Separate dedicated summary panel
- [ ] Chat history loads when session loaded
- [ ] Animated spinner for AI processing
- [ ] Error messages shown in chat as red text
- [ ] Collapsible panels with expand/collapse buttons
- [ ] Redesigned layout accommodates AI features
- [ ] Real-time updates with auto-scroll
- [ ] Manual "Ask Chavr" button works
- [ ] Manual "Generate Summary" button works
- [ ] Chat history persistence
- [ ] Summary display in dedicated panel
- [ ] Loading states and error handling
- [ ] Responsive design

## Success Metrics

- [ ] Chat panel loads and displays messages correctly
- [ ] Manual questions work through GUI
- [ ] Voice commands still work and appear in chat
- [ ] Summary generation works from GUI
- [ ] Chat history loads correctly
- [ ] Panels collapse/expand smoothly
- [ ] No GUI freezing during AI processing
- [ ] Error handling works gracefully
- [ ] Layout is responsive and intuitive

---

**Estimated Implementation Time:** 3-4 hours  
**Complexity:** Medium-High (GUI redesign + AI integration)  
**Dependencies:** Step 18 (AI integration) complete

