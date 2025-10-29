#!/usr/bin/env python3
"""
Run the Chavr AI Tutor application.
Simplified entry point for the pivoted application.
"""

import sys

def main():
    """Main entry point for Chavr AI Tutor."""
    try:
        from tutor_gui import TutorGUI
        
        print("=" * 50)
        print("Chavr AI Tutor - Starting...")
        print("=" * 50)
        
        # Create and run GUI
        gui = TutorGUI()
        gui.run()
        
    except ImportError as e:
        print(f"Error: Could not import required modules: {e}")
        print("\nPlease install dependencies:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nChavr AI Tutor - Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

