#!/usr/bin/env python3
"""Test GUI AI integration - Step 19"""

import tkinter as tk
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui import ChavrGUI


def test_gui_creation():
    """Test GUI creation with AI panels."""
    print("\n=== Test 1: GUI Creation ===")
    
    root = tk.Tk()
    root.withdraw()  # Hide the window for testing
    
    try:
        gui = ChavrGUI(root)
        
        # Test AI chat panel exists
        assert hasattr(gui, 'ai_chat_frame'), "AI chat frame not found"
        assert hasattr(gui, 'ai_chat_toggle_btn'), "AI chat toggle button not found"
        assert hasattr(gui, 'ai_input_text'), "AI input text not found"
        assert hasattr(gui, 'ask_chavr_btn'), "Ask Chavr button not found"
        
        # Test AI summary panel exists
        assert hasattr(gui, 'ai_summary_frame'), "AI summary frame not found"
        assert hasattr(gui, 'ai_summary_toggle_btn'), "AI summary toggle button not found"
        assert hasattr(gui, 'ai_summary_content'), "AI summary content not found"
        assert hasattr(gui, 'generate_summary_btn'), "Generate summary button not found"
        
        # Test AI status indicator
        assert hasattr(gui, 'ai_status_label'), "AI status label not found"
        
        print("✓ All AI GUI components created successfully")
        return True
        
    except Exception as e:
        print(f"✗ GUI creation failed: {e}")
        return False
    finally:
        root.destroy()


def test_chat_panel_toggle():
    """Test chat panel toggle functionality."""
    print("\n=== Test 2: Chat Panel Toggle ===")
    
    root = tk.Tk()
    root.withdraw()
    
    try:
        gui = ChavrGUI(root)
        
        # Test initial state
        assert gui.ai_chat_collapsed == True, "Chat panel should be collapsed initially"
        
        # Test toggle to expanded
        gui._toggle_ai_chat()
        assert gui.ai_chat_collapsed == False, "Chat panel should be expanded after toggle"
        assert gui.ai_chat_toggle_btn.cget('text') == "▼ AI Chavruta", "Toggle button text should show expanded"
        
        # Test toggle back to collapsed
        gui._toggle_ai_chat()
        assert gui.ai_chat_collapsed == True, "Chat panel should be collapsed after second toggle"
        assert gui.ai_chat_toggle_btn.cget('text') == "▶ AI Chavruta", "Toggle button text should show collapsed"
        
        print("✓ Chat panel toggle functionality works")
        return True
        
    except Exception as e:
        print(f"✗ Chat panel toggle failed: {e}")
        return False
    finally:
        root.destroy()


def test_summary_panel_toggle():
    """Test summary panel toggle functionality."""
    print("\n=== Test 3: Summary Panel Toggle ===")
    
    root = tk.Tk()
    root.withdraw()
    
    try:
        gui = ChavrGUI(root)
        
        # Test initial state
        assert gui.ai_summary_collapsed == True, "Summary panel should be collapsed initially"
        
        # Test toggle to expanded
        gui._toggle_ai_summary()
        assert gui.ai_summary_collapsed == False, "Summary panel should be expanded after toggle"
        assert gui.ai_summary_toggle_btn.cget('text') == "▼ Session Summary", "Toggle button text should show expanded"
        
        # Test toggle back to collapsed
        gui._toggle_ai_summary()
        assert gui.ai_summary_collapsed == True, "Summary panel should be collapsed after second toggle"
        assert gui.ai_summary_toggle_btn.cget('text') == "▶ Session Summary", "Toggle button text should show collapsed"
        
        print("✓ Summary panel toggle functionality works")
        return True
        
    except Exception as e:
        print(f"✗ Summary panel toggle failed: {e}")
        return False
    finally:
        root.destroy()


def test_message_display():
    """Test message display functionality."""
    print("\n=== Test 4: Message Display ===")
    
    root = tk.Tk()
    root.withdraw()
    
    try:
        gui = ChavrGUI(root)
        
        # Expand chat panel for testing
        gui._toggle_ai_chat()
        
        # Test adding user message
        gui._add_chat_message("Test question", "user")
        
        # Test adding AI message
        gui._add_chat_message("Test response", "ai")
        
        # Test adding error message
        gui._add_chat_message("Test error", "error")
        
        # Check that messages were added
        children = gui.ai_chat_scrollable_frame.winfo_children()
        assert len(children) >= 3, f"Expected at least 3 message frames, got {len(children)}"
        
        print("✓ Message display functionality works")
        return True
        
    except Exception as e:
        print(f"✗ Message display failed: {e}")
        return False
    finally:
        root.destroy()


def test_summary_display():
    """Test summary display functionality."""
    print("\n=== Test 5: Summary Display ===")
    
    root = tk.Tk()
    root.withdraw()
    
    try:
        gui = ChavrGUI(root)
        
        # Test displaying summary
        test_summary = "This is a test summary of the study session."
        gui._display_summary(test_summary)
        
        # Check that summary panel is expanded
        assert gui.ai_summary_collapsed == False, "Summary panel should be expanded when displaying summary"
        
        # Check that summary content is set
        content = gui.ai_summary_content.get("1.0", tk.END).strip()
        assert content == test_summary, f"Summary content mismatch: expected '{test_summary}', got '{content}'"
        
        print("✓ Summary display functionality works")
        return True
        
    except Exception as e:
        print(f"✗ Summary display failed: {e}")
        return False
    finally:
        root.destroy()


def test_ai_status():
    """Test AI status indicator functionality."""
    print("\n=== Test 6: AI Status Indicator ===")
    
    root = tk.Tk()
    root.withdraw()
    
    try:
        gui = ChavrGUI(root)
        
        # Test setting different statuses
        gui._set_ai_status("Ready", "#28A745")
        assert gui.ai_status_label.cget('text') == "Ready", "Status text should be 'Ready'"
        assert gui.ai_status_label.cget('fg') == "#28A745", "Status color should be green"
        
        gui._set_ai_status("Processing...", "#FFC107")
        assert gui.ai_status_label.cget('text') == "Processing...", "Status text should be 'Processing...'"
        assert gui.ai_status_label.cget('fg') == "#FFC107", "Status color should be yellow"
        
        gui._set_ai_status("Error", "#DC3545")
        assert gui.ai_status_label.cget('text') == "Error", "Status text should be 'Error'"
        assert gui.ai_status_label.cget('fg') == "#DC3545", "Status color should be red"
        
        print("✓ AI status indicator functionality works")
        return True
        
    except Exception as e:
        print(f"✗ AI status indicator failed: {e}")
        return False
    finally:
        root.destroy()


def test_chat_clear():
    """Test chat clear functionality."""
    print("\n=== Test 7: Chat Clear ===")
    
    root = tk.Tk()
    root.withdraw()
    
    try:
        gui = ChavrGUI(root)
        
        # Expand chat panel for testing
        gui._toggle_ai_chat()
        
        # Add some messages
        gui._add_chat_message("Message 1", "user")
        gui._add_chat_message("Message 2", "ai")
        
        # Check messages were added
        children_before = gui.ai_chat_scrollable_frame.winfo_children()
        assert len(children_before) >= 2, "Messages should be added"
        
        # Clear chat
        gui._clear_chat()
        
        # Check messages were cleared
        children_after = gui.ai_chat_scrollable_frame.winfo_children()
        assert len(children_after) == 0, "Chat should be cleared"
        
        print("✓ Chat clear functionality works")
        return True
        
    except Exception as e:
        print(f"✗ Chat clear failed: {e}")
        return False
    finally:
        root.destroy()


def main():
    """Run all GUI AI integration tests."""
    print("Step 19: GUI AI Integration Tests")
    print("=" * 50)
    
    tests = [
        test_gui_creation,
        test_chat_panel_toggle,
        test_summary_panel_toggle,
        test_message_display,
        test_summary_display,
        test_ai_status,
        test_chat_clear
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All GUI AI integration tests passed!")
    else:
        print("✗ Some tests failed. Check the output above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

