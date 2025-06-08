"""
GUI Interface for Content Extractor App

Simple tkinter-based GUI for the selenium content extraction functionality.

Created by: Quantum Bear
Date: 2025-01-22
Project: Triad Docker Base
"""

import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import logging
from pathlib import Path

from .app import ContentExtractorApp

logger = logging.getLogger(__name__)


class ContentExtractorGUI:
    """GUI interface for the content extractor."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.app = None
        self.extraction_thread = None
        self.config_file = None
        self.output_file = "extracted_content.json"
        
        self.setup_ui()
        self.setup_logging()
    
    def setup_ui(self):
        """Set up the GUI interface."""
        self.root.title("Content Extractor")
        self.root.geometry("800x600")
        
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # URL input
        ttk.Label(main_frame, text="URL to Extract:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=60)
        url_entry.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Configuration file
        ttk.Label(main_frame, text="Configuration File:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.config_var = tk.StringVar(value="None selected")
        config_label = ttk.Label(main_frame, textvariable=self.config_var, relief=tk.SUNKEN)
        config_label.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        config_btn = ttk.Button(main_frame, text="Browse...", command=self.browse_config)
        config_btn.grid(row=1, column=2, pady=5, padx=(5, 0))
        
        # Output file
        ttk.Label(main_frame, text="Output File:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.output_var = tk.StringVar(value=self.output_file)
        output_entry = ttk.Entry(main_frame, textvariable=self.output_var, width=40)
        output_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        
        output_btn = ttk.Button(main_frame, text="Browse...", command=self.browse_output)
        output_btn.grid(row=2, column=2, pady=5, padx=(5, 0))
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        options_frame.columnconfigure(1, weight=1)
        
        self.headless_var = tk.BooleanVar(value=True)
        headless_cb = ttk.Checkbox(options_frame, text="Run in headless mode (no browser window)", 
                                 variable=self.headless_var)
        headless_cb.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Session ID
        ttk.Label(options_frame, text="Session ID (optional):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.session_var = tk.StringVar()
        session_entry = ttk.Entry(options_frame, textvariable=self.session_var, width=30)
        session_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=4, column=0, columnspan=3, pady=20)
        
        self.extract_btn = ttk.Button(buttons_frame, text="Extract Content", 
                                    command=self.start_extraction, style="Accent.TButton")
        self.extract_btn.pack(side=tk.LEFT, padx=5)
        
        create_config_btn = ttk.Button(buttons_frame, text="Create Config Template", 
                                     command=self.create_config_template)
        create_config_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(buttons_frame, text="Stop", command=self.stop_extraction, 
                                 state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.grid(row=6, column=0, columnspan=3, pady=5)
        
        # Log output
        log_frame = ttk.LabelFrame(main_frame, text="Log Output", padding="5")
        log_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Example URL for testing
        example_url = "https://www.airscience.com/product-category-page?brandname=safeswab-swab-dryers&brand=30"
        self.url_var.set(example_url)
    
    def setup_logging(self):
        """Set up logging to display in the GUI."""
        class GUILogHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
            
            def emit(self, record):
                msg = self.format(record)
                self.text_widget.insert(tk.END, msg + '\n')
                self.text_widget.see(tk.END)
                self.text_widget.update()
        
        # Add GUI handler to logger
        gui_handler = GUILogHandler(self.log_text)
        gui_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(gui_handler)
        logging.getLogger().setLevel(logging.INFO)
    
    def browse_config(self):
        """Browse for configuration file."""
        filename = filedialog.askopenfilename(
            title="Select Configuration File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.config_file = filename
            self.config_var.set(os.path.basename(filename))
    
    def browse_output(self):
        """Browse for output file location."""
        filename = filedialog.asksaveasfilename(
            title="Save Output As",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.output_file = filename
            self.output_var.set(filename)
    
    def create_config_template(self):
        """Create a configuration template file."""
        templates = {
            "Basic": "basic",
            "Lab Equipment": "lab-equipment", 
            "Product Page": "product"
        }
        
        # Create selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Create Configuration Template")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Select template type:").pack(pady=10)
        
        template_var = tk.StringVar(value="Lab Equipment")
        for name in templates.keys():
            ttk.Radiobutton(dialog, text=name, variable=template_var, value=name).pack(anchor=tk.W, padx=20)
        
        def create_template():
            template_type = templates[template_var.get()]
            filename = filedialog.asksaveasfilename(
                title="Save Configuration Template",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")],
                parent=dialog
            )
            
            if filename:
                from .cli import ContentExtractorCLI
                cli = ContentExtractorCLI()
                config = cli.get_config_template(template_type)
                
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=2, ensure_ascii=False)
                    
                    messagebox.showinfo("Success", f"Template created: {filename}", parent=dialog)
                    
                    # Ask if they want to use this config
                    if messagebox.askyesno("Use Template", "Use this configuration for extraction?", parent=dialog):
                        self.config_file = filename
                        self.config_var.set(os.path.basename(filename))
                    
                    dialog.destroy()
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to create template: {e}", parent=dialog)
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Create", command=create_template).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def start_extraction(self):
        """Start content extraction in a separate thread."""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL to extract from")
            return
        
        # Update UI state
        self.extract_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress.start()
        self.status_var.set("Extracting content...")
        
        # Clear log
        self.log_text.delete(1.0, tk.END)
        
        # Start extraction thread
        self.extraction_thread = threading.Thread(target=self.run_extraction, args=(url,))
        self.extraction_thread.daemon = True
        self.extraction_thread.start()
    
    def run_extraction(self, url):
        """Run the content extraction process."""
        try:
            headless = self.headless_var.get()
            output_file = self.output_var.get()
            session_id = self.session_var.get().strip() or None
            
            logger.info(f"Starting extraction from: {url}")
            logger.info(f"Browser mode: {'headless' if headless else 'visible'}")
            
            with ContentExtractorApp(headless=headless, config_file=self.config_file) as app:
                self.app = app
                
                # Load configuration
                if self.config_file:
                    logger.info(f"Using configuration: {os.path.basename(self.config_file)}")
                else:
                    logger.info("Using default configuration")
                    from .cli import ContentExtractorCLI
                    cli = ContentExtractorCLI()
                    app.config = cli.get_default_config()
                
                # Extract content
                extracted_data = app.extract_content(url)
                
                if not extracted_data:
                    logger.error("No content was extracted")
                    self.update_ui_on_completion("No content extracted", False)
                    return
                
                # Display results
                logger.info(f"Extracted {len(extracted_data)} fields:")
                for field_name, field_data in extracted_data.items():
                    content = field_data.get('content', '')
                    status = '✓' if content else '✗'
                    preview = content[:100] + '...' if len(content) > 100 else content
                    logger.info(f"  {status} {field_name}: {preview}")
                
                # Save output
                if app.save_export_file(output_file, session_id):
                    logger.info(f"Data exported to: {output_file}")
                    logger.info(f"Session ID: {app.session_id}")
                    logger.info("Ready for upload to Django admin")
                    self.update_ui_on_completion(f"Extraction completed successfully!\nData saved to: {output_file}", True)
                else:
                    logger.error("Failed to save export file")
                    self.update_ui_on_completion("Failed to save export file", False)
                    
        except Exception as e:
            logger.exception(f"Extraction failed: {e}")
            self.update_ui_on_completion(f"Extraction failed: {e}", False)
    
    def update_ui_on_completion(self, message, success):
        """Update UI when extraction is complete."""
        def update():
            self.extract_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.progress.stop()
            self.status_var.set(message)
            
            if success:
                messagebox.showinfo("Success", message)
            else:
                messagebox.showerror("Error", message)
        
        # Schedule UI update on main thread
        self.root.after(0, update)
    
    def stop_extraction(self):
        """Stop the extraction process."""
        if self.app:
            self.app.close()
            self.app = None
        
        self.extract_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress.stop()
        self.status_var.set("Extraction stopped")
        
        logger.info("Extraction stopped by user")
    
    def run(self):
        """Start the GUI application."""
        self.root.mainloop()
    
    def __del__(self):
        """Cleanup when GUI is destroyed."""
        if self.app:
            self.app.close()


def main():
    """Main entry point for GUI."""
    app = ContentExtractorGUI()
    app.run()


if __name__ == '__main__':
    main() 