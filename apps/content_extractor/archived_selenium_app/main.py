#!/usr/bin/env python3
"""
Content Extractor - Main Entry Point

Standalone selenium-based content extraction application.

Created by: Quantum Bear
Date: 2025-01-22
Project: Triad Docker Base
"""

import sys
import os
import argparse
import tkinter as tk
from tkinter import messagebox

# Add the current directory to the path to handle imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def main():
    """Main entry point for the standalone application."""
    parser = argparse.ArgumentParser(
        description="Content Extractor - Selenium-based web content extraction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage:
  Run with GUI:     python main.py
  Run with CLI:     python main.py --cli [CLI_ARGS]
  
Examples:
  python main.py
  python main.py --cli extract https://example.com --output data.json
  python main.py --cli create-config --template lab-equipment
        """
    )
    
    parser.add_argument('--cli', action='store_true',
                       help='Use command line interface instead of GUI')
    parser.add_argument('--version', action='version', version='Content Extractor 1.0.0')
    
    # Parse known args to separate our args from CLI args
    args, cli_args = parser.parse_known_args()
    
    if args.cli:
        # Use CLI interface
        try:
            from cli import ContentExtractorCLI
            cli = ContentExtractorCLI()
            return cli.run(cli_args)
        except ImportError as e:
            print(f"Error importing CLI module: {e}")
            return 1
        except Exception as e:
            print(f"CLI error: {e}")
            return 1
    else:
        # Use GUI interface
        try:
            # Check if we can create tkinter window
            root = tk.Tk()
            root.withdraw()  # Hide the root window
            
            from gui import ContentExtractorGUI
            app = ContentExtractorGUI()
            app.run()
            return 0
            
        except ImportError as e:
            print("GUI not available (tkinter import failed). Use --cli for command line interface.")
            print(f"Error: {e}")
            return 1
        except tk.TclError as e:
            print("GUI not available (no display). Use --cli for command line interface.")
            print(f"Error: {e}")
            return 1
        except Exception as e:
            print(f"GUI error: {e}")
            print("Falling back to CLI interface...")
            
            try:
                from cli import ContentExtractorCLI
                cli = ContentExtractorCLI()
                print("\nContent Extractor CLI")
                print("Use 'python main.py --cli --help' for usage information")
                return 0
            except ImportError:
                print("Neither GUI nor CLI interface available")
                return 1


if __name__ == '__main__':
    sys.exit(main()) 