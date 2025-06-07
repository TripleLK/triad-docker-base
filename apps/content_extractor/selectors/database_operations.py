"""
Database Operations for Interactive Selector

Handles all database persistence operations including selector saving,
testing, session management, and success rate tracking.

Created by: Thunder Apex
Date: 2025-01-08
Project: Triad Docker Base
"""

import logging
from typing import Dict, List, Optional
from urllib.parse import urlparse
from django.utils import timezone
from apps.content_extractor.models import SiteFieldSelector, SelectorTestResult, FieldSelectionSession

logger = logging.getLogger(__name__)


class DatabaseOperationsManager:
    """Manages all database operations for the interactive selector."""
    
    def __init__(self, session_name: str = None):
        """
        Initialize database operations manager.
        
        Args:
            session_name: Optional session name for tracking
        """
        self.session_name = session_name
        
    def get_domain_from_url(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower().replace('www.', '')
        except:
            return 'unknown'
    
    def get_or_create_field_session(self, domain: str) -> FieldSelectionSession:
        """Get or create a field selection session for tracking progress."""
        try:
            session, created = FieldSelectionSession.objects.get_or_create(
                session_name=self.session_name,
                site_domain=domain,
                defaults={'started_at': timezone.now()}
            )
            return session
        except Exception as e:
            logger.error(f"Failed to get/create field session: {e}")
            return None
    
    def save_field_selector(self, field_name: str, xpath: str, css_selector: str = "",
                           requires_manual_input: bool = False, manual_input_note: str = "",
                           domain: str = None) -> bool:
        """
        Save a field selector to the database.
        
        Args:
            field_name: Name of the field being selected
            xpath: XPath selector for the element
            css_selector: CSS selector for the element (optional)
            requires_manual_input: Whether this field requires manual input
            manual_input_note: Note about manual input requirements
            domain: Domain to save selector for
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            if not domain:
                logger.error("Domain is required to save field selector")
                return False
                
            # Get site name from domain
            site_name = domain.replace('.com', '').replace('.', '_').title()
            
            # Create the selector record
            selector = SiteFieldSelector.objects.create(
                site_name=site_name,
                site_domain=domain,
                field_name=field_name,
                xpath_selector=xpath,
                css_selector=css_selector or "",
                requires_manual_input=requires_manual_input,
                manual_input_note=manual_input_note or "",
                created_by=self.session_name or "interactive_selector"
            )
            
            logger.info(f"Saved selector for {field_name} on {domain}: {xpath}")
            return True
                
        except Exception as e:
            logger.error(f"Failed to save field selector: {e}")
            return False
    
    def test_selector_on_page(self, selector: SiteFieldSelector, test_url: str, driver) -> Dict:
        """
        Test a saved selector on a specific page.
        
        Args:
            selector: The SiteFieldSelector to test
            test_url: URL to test the selector on
            driver: Selenium WebDriver instance
            
        Returns:
            Dictionary with test results
        """
        try:
            # Load the test page
            driver.get(test_url)
            
            test_result = {
                'selector_id': selector.id,
                'field_name': selector.field_name,
                'test_url': test_url,
                'success': False,
                'error_message': '',
                'extracted_content': '',
                'element_count': 0
            }
            
            # Try XPath first
            try:
                elements = driver.find_elements('xpath', selector.xpath_selector)
                if elements:
                    test_result['success'] = True
                    test_result['element_count'] = len(elements)
                    # Extract content from first matching element
                    test_result['extracted_content'] = elements[0].text.strip()[:200]  # Limit content length
                    
                    # Save test result to database
                    SelectorTestResult.objects.create(
                        selector=selector,
                        test_url=test_url,
                        success=True,
                        element_count=len(elements),
                        extracted_content=test_result['extracted_content'],
                        tested_at=timezone.now()
                    )
                    
                else:
                    test_result['error_message'] = 'No elements found with XPath'
                    
            except Exception as e:
                test_result['error_message'] = f'XPath error: {str(e)}'
                
            # If XPath failed and CSS selector is available, try CSS
            if not test_result['success'] and selector.css_selector:
                try:
                    elements = driver.find_elements('css selector', selector.css_selector)
                    if elements:
                        test_result['success'] = True
                        test_result['element_count'] = len(elements)
                        test_result['extracted_content'] = elements[0].text.strip()[:200]
                        
                        # Save successful CSS test result
                        SelectorTestResult.objects.create(
                            selector=selector,
                            test_url=test_url,
                            success=True,
                            element_count=len(elements),
                            extracted_content=test_result['extracted_content'],
                            tested_at=timezone.now()
                        )
                        
                    else:
                        test_result['error_message'] += ' | No elements found with CSS selector'
                        
                except Exception as e:
                    test_result['error_message'] += f' | CSS error: {str(e)}'
            
            # Save failed test result if both selectors failed
            if not test_result['success']:
                SelectorTestResult.objects.create(
                    selector=selector,
                    test_url=test_url,
                    success=False,
                    error_message=test_result['error_message'],
                    tested_at=timezone.now()
                )
                
            return test_result
            
        except Exception as e:
            logger.error(f"Error testing selector: {e}")
            return {
                'selector_id': selector.id if selector else None,
                'field_name': selector.field_name if selector else 'unknown',
                'test_url': test_url,
                'success': False,
                'error_message': f'Test execution error: {str(e)}',
                'extracted_content': '',
                'element_count': 0
            }
    
    def test_all_selectors_on_page(self, test_url: str, driver, domain: str = None) -> Dict[str, Dict]:
        """
        Test all saved selectors for a domain on a specific page.
        
        Args:
            test_url: URL to test selectors on
            driver: Selenium WebDriver instance
            domain: Optional domain filter
            
        Returns:
            Dictionary mapping field names to test results
        """
        if not domain:
            domain = self.get_domain_from_url(test_url)
            
        selectors = self.get_saved_selectors(domain)
        results = {}
        
        for selector in selectors:
            result = self.test_selector_on_page(selector, test_url, driver)
            results[selector.field_name] = result
            
        return results
    
    def get_saved_selectors(self, domain: str = None) -> List[SiteFieldSelector]:
        """
        Get saved selectors, optionally filtered by domain.
        
        Args:
            domain: Optional domain to filter by
            
        Returns:
            List of SiteFieldSelector objects
        """
        try:
            if domain:
                return list(SiteFieldSelector.objects.filter(site_domain=domain).order_by('-created_at'))
            else:
                return list(SiteFieldSelector.objects.all().order_by('-created_at'))
        except Exception as e:
            logger.error(f"Failed to get saved selectors: {e}")
            return []
    
    def get_selector_success_rates(self, domain: str = None) -> Dict[str, float]:
        """
        Get success rates for selectors by field name.
        
        Args:
            domain: Optional domain to filter by
            
        Returns:
            Dictionary mapping field names to success rates (0.0-1.0)
        """
        try:
            selectors = self.get_saved_selectors(domain)
            success_rates = {}
            
            for selector in selectors:
                test_results = SelectorTestResult.objects.filter(selector=selector)
                if test_results.exists():
                    total_tests = test_results.count()
                    successful_tests = test_results.filter(success=True).count()
                    success_rates[selector.field_name] = successful_tests / total_tests
                else:
                    success_rates[selector.field_name] = 0.0
                    
            return success_rates
            
        except Exception as e:
            logger.error(f"Failed to get selector success rates: {e}")
            return {}
    
    def get_manual_input_fields(self, domain: str = None) -> List[Dict]:
        """
        Get fields that require manual input.
        
        Args:
            domain: Optional domain to filter by
            
        Returns:
            List of dictionaries with field information
        """
        try:
            query = SiteFieldSelector.objects.filter(requires_manual_input=True)
            if domain:
                query = query.filter(site_domain=domain)
                
            manual_fields = []
            for selector in query.order_by('field_name'):
                manual_fields.append({
                    'field_name': selector.field_name,
                    'site_domain': selector.site_domain,
                    'manual_input_note': selector.manual_input_note,
                    'created_at': selector.created_at
                })
                
            return manual_fields
            
        except Exception as e:
            logger.error(f"Failed to get manual input fields: {e}")
            return []
    
    def mark_field_as_manual(self, field_name: str, manual_input_note: str, domain: str) -> bool:
        """
        Mark a field as requiring manual input.
        
        Args:
            field_name: Name of the field
            manual_input_note: Explanation of why manual input is needed
            domain: Domain for the field
            
        Returns:
            True if marked successfully, False otherwise
        """
        try:
            # Create a manual input record
            site_name = domain.replace('.com', '').replace('.', '_').title()
            
            selector = SiteFieldSelector.objects.create(
                site_name=site_name,
                site_domain=domain,
                field_name=field_name,
                xpath_selector='',  # Empty selector for manual fields
                css_selector='',
                requires_manual_input=True,
                manual_input_note=manual_input_note,
                created_by=self.session_name or "interactive_selector"
            )
            
            logger.info(f"Marked {field_name} as manual input for {domain}: {manual_input_note}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark field as manual: {e}")
            return False
    
    def choose_best_selector(self, selections: List[Dict]) -> Dict:
        """
        Choose the most robust selector from multiple selections.
        
        Args:
            selections: List of selection dictionaries
            
        Returns:
            Best selection dictionary
        """
        if not selections:
            return {}
            
        if len(selections) == 1:
            return selections[0]
            
        # Scoring criteria for selector robustness
        def score_selector(selection):
            score = 0
            xpath = selection.get('xpath', '')
            css = selection.get('css_selector', '')
            
            # Prefer selectors with IDs
            if '#' in css or '@id' in xpath:
                score += 10
                
            # Prefer shorter XPaths (more stable)
            score -= len(xpath.split('/')) * 0.5
            
            # Prefer selectors with class names
            if '.' in css or '@class' in xpath:
                score += 3
                
            # Prefer selectors without position-based indexing
            if '[' not in xpath:
                score += 5
                
            return score
        
        # Return the selection with the highest score
        return max(selections, key=score_selector)
    
    def load_test_urls_for_domain(self, domain: str) -> List[str]:
        """
        Load test URLs for a specific domain.
        
        Args:
            domain: Domain to load test URLs for
            
        Returns:
            List of test URLs
        """
        # This is a placeholder - in a real implementation, you would:
        # 1. Load from a database table of test URLs
        # 2. Load from a configuration file
        # 3. Generate based on domain patterns
        
        # For now, return some common page patterns
        base_patterns = [
            f"https://{domain}",
            f"https://www.{domain}",
            f"https://{domain}/products",
            f"https://www.{domain}/products",
            f"https://{domain}/category",
            f"https://www.{domain}/category"
        ]
        
        return base_patterns[:3]  # Return first 3 patterns
    
    def update_session_progress(self, field_name: str, status: str, domain: str) -> bool:
        """
        Update progress for a field selection session.
        
        Args:
            field_name: Name of the field being worked on
            status: Status update (started, completed, failed, etc.)
            domain: Domain being worked on
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            session = self.get_or_create_field_session(domain)
            if not session:
                return False
                
            # Update session progress (this could be expanded to track more detailed progress)
            session.updated_at = timezone.now()
            session.save()
            
            logger.info(f"Updated session progress: {field_name} - {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session progress: {e}")
            return False 