import requests
import re
import nltk
from difflib import SequenceMatcher
from bs4 import BeautifulSoup
from apps.scrapers.selectors.base import Selector, Selected, SelectedType
import logging

# Configure logging
logger = logging.getLogger(__name__)

class Scraper:
    def __init__(self, filepath):
        self.selector = Selector.fromFilePath(filepath)

    def scrape(self, href):
        new_soup = BeautifulSoup(requests.get(href).text, 'html.parser')
        result = self.selector.select(Selected(new_soup, SelectedType.SINGLE)).collapsed_value
        
        # Post-process the result to handle fallbacks
        if isinstance(result, dict):
            # Apply short description fallback if needed
            self._apply_short_description_fallback(result)
            
        return result
        
    def _apply_short_description_fallback(self, result):
        """
        Implement fallback mechanism for short descriptions.
        If short_description is empty but full_description and name exist,
        extract a suitable short description from the full description.
        """
        # Check if we need to apply fallback logic
        if (not result.get('short_description') and 
            result.get('full_description') and 
            result.get('name')):
            
            name = result['name']
            full_desc = result['full_description']
            
            # Try to extract text content from HTML if necessary
            if '<' in full_desc and '>' in full_desc:
                soup = BeautifulSoup(full_desc, 'html.parser')
                full_desc = soup.get_text()
            
            # Simple fallback approach using regex in case NLTK fails
            sentences = re.split(r'(?<=[.!?])\s+', full_desc)
            
            # Try NLTK for better sentence tokenization, but don't fail if unavailable
            try:
                nltk_sentences = nltk.sent_tokenize(full_desc)
                if nltk_sentences:
                    sentences = nltk_sentences
            except Exception as e:
                logger.warning(f"NLTK sentence tokenization failed, using regex fallback: {str(e)}")
            
            if not sentences:
                return
                
            # Try to find the best sentence with fuzzy matching
            best_sentence = None
            best_score = 0
            
            # Get words from the product name
            name_words = set(re.findall(r'\b\w+\b', name.lower()))
            
            for sentence in sentences:
                # Skip very short sentences
                if len(sentence) < 20:
                    continue
                    
                # Method 1: Check if any product name word appears in the sentence
                sentence_lower = sentence.lower()
                matches = [word for word in name_words if word in sentence_lower]
                
                # Method 2: Use sequence matcher for fuzzy matching
                similarity = SequenceMatcher(None, name.lower(), sentence_lower).ratio()
                
                # Calculate combined score (word matches + similarity)
                score = len(matches)/max(1, len(name_words)) + similarity
                
                if score > best_score:
                    best_score = score
                    best_sentence = sentence
            
            # If no good match found, use the first substantial sentence
            if not best_sentence and len(sentences) > 0:
                for sentence in sentences:
                    if len(sentence) >= 20:
                        best_sentence = sentence
                        break
                        
            # If we found a suitable sentence, use it as short description
            if best_sentence:
                # Clean up and limit length
                best_sentence = best_sentence.strip()
                # Truncate if too long (aim for ~200 chars max)
                if len(best_sentence) > 200:
                    best_sentence = best_sentence[:197] + "..."
                    
                result['short_description'] = best_sentence

