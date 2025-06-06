#!/usr/bin/env python3
"""
Script to download necessary NLTK data packages for the Triad Scientific scraper
"""
import nltk
import sys

def download_nltk_data():
    """Download required NLTK data packages"""
    try:
        print("Downloading NLTK punkt tokenizer data...")
        nltk.download('punkt')
        print("Downloading NLTK punkt_tab data...")
        nltk.download('punkt_tab')
        print("Download complete.")
        return True
    except Exception as e:
        print(f"Error downloading NLTK data: {str(e)}")
        return False

if __name__ == "__main__":
    success = download_nltk_data()
    sys.exit(0 if success else 1) 