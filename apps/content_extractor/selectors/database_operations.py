"""
Database Operations for Interactive Selector

Handles all database persistence operations for AI preparation records,
session management, and content extraction tracking.

Created by: Thunder Apex
Date: 2025-01-08
Updated by: Stellar Hawk  
Date: 2025-01-22
Project: Triad Docker Base - AI Preparation System
"""

import logging
import uuid
from typing import Dict, List, Optional
from urllib.parse import urlparse
from django.utils import timezone
from apps.content_extractor.models import SiteConfiguration, FieldConfiguration

logger = logging.getLogger(__name__)


class DatabaseOperationsManager:
    """Manages all database operations for AI preparation record storage."""
    
    def __init__(self, session_name: str = None):
        """
        Initialize database operations manager.
        
        Args:
            session_name: Session identifier for grouping AI preparation records
        """
        self.session_name = session_name or f"ai_session_{uuid.uuid4().hex[:8]}"
        
    def get_domain_from_url(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower().replace('www.', '')
        except:
            return 'unknown'
    
    def save_ai_preparation_record(self, field_name: str, extracted_content: str, xpath: str,
                                 css_selector: str = "", user_comment: str = "",
                                 extraction_method: str = "page_selection", 
                                 confidence_level: str = "medium",
                                 content_type: str = "text",
                                 source_url: str = "", instance_index: int = 0,
                                 parent_record_id: int = None) -> bool:
        """
        Save AI preparation record to the database.
        
        Args:
            field_name: Name of the field being extracted
            extracted_content: The actual extracted content
            xpath: XPath selector used for extraction
            css_selector: CSS selector alternative (optional)
            user_comment: User-provided context for AI processing
            extraction_method: Method used (page_selection, text_input, xpath_edit)
            confidence_level: Confidence in extraction (high, medium, low)
            content_type: Type of content (text, list, nested_data, html, number, url)
            source_url: URL where content was extracted
            instance_index: Instance number for multi-instance fields
            parent_record_id: Parent record for nested structures
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Create the AI preparation record
            record = SiteConfiguration.objects.create(
                session_id=self.session_name,
                source_url=source_url,
                field_name=field_name,
                extracted_content=extracted_content,
                xpath_used=xpath,
                css_selector_used=css_selector,
                user_comment=user_comment,
                extraction_method=extraction_method,
                confidence_level=confidence_level,
                content_type=content_type,
                instance_index=instance_index,
                parent_record_id=parent_record_id
            )
            
            logger.info(f"Saved AI preparation record for {field_name} (session: {self.session_name})")
            return True
                
        except Exception as e:
            logger.error(f"Failed to save AI preparation record: {e}")
            return False
    
    def get_session_records(self, session_id: str = None) -> List[SiteConfiguration]:
        """
        Get all AI preparation records for a session.
        
        Args:
            session_id: Session ID to retrieve (defaults to current session)
            
        Returns:
            List of SiteConfiguration objects
        """
        try:
            session_id = session_id or self.session_name
            return list(SiteConfiguration.objects.filter(session_id=session_id).order_by(
                'field_name', 'instance_index', 'created_at'
            ))
        except Exception as e:
            logger.error(f"Error retrieving session records: {e}")
            return []
    
    def get_nested_records(self, parent_record_id: int) -> List[SiteConfiguration]:
        """
        Get child records for a nested structure.
        
        Args:
            parent_record_id: ID of the parent record
            
        Returns:
            List of child SiteConfiguration objects
        """
        try:
            return list(SiteConfiguration.objects.filter(
                parent_record_id=parent_record_id
            ).order_by('field_name', 'instance_index'))
        except Exception as e:
            logger.error(f"Error retrieving nested records: {e}")
            return []
    
    def update_record_content(self, record_id: int, extracted_content: str, 
                            user_comment: str = "", confidence_level: str = None) -> bool:
        """
        Update an existing AI preparation record.
        
        Args:
            record_id: ID of the record to update
            extracted_content: New extracted content
            user_comment: Updated user comment
            confidence_level: Updated confidence level
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            record = SiteConfiguration.objects.get(id=record_id)
            record.extracted_content = extracted_content
            if user_comment:
                record.user_comment = user_comment
            if confidence_level:
                record.confidence_level = confidence_level
            record.save()
            
            logger.info(f"Updated AI preparation record {record_id}")
            return True
        except SiteConfiguration.DoesNotExist:
            logger.error(f"AI preparation record {record_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error updating AI preparation record: {e}")
            return False
    
    def export_session_for_ai(self, session_id: str = None, format: str = 'structured') -> Dict:
        """
        Export session data formatted for AI processing.
        
        Args:
            session_id: Session ID to export (defaults to current session)
            format: Export format ('structured', 'prompt', 'json')
            
        Returns:
            Dictionary with formatted data for AI consumption
        """
        try:
            from apps.content_extractor.models import AIContextBuilder
            session_id = session_id or self.session_name
            return AIContextBuilder.export_for_ai(session_id, format)
        except Exception as e:
            logger.error(f"Error exporting session for AI: {e}")
            return {}
    
    def get_extraction_statistics(self, session_id: str = None) -> Dict:
        """
        Get statistics about extraction session.
        
        Args:
            session_id: Session ID to analyze (defaults to current session)
            
        Returns:
            Dictionary with session statistics
        """
        try:
            session_id = session_id or self.session_name
            records = SiteConfiguration.objects.filter(session_id=session_id)
            
            stats = {
                'total_records': records.count(),
                'fields_extracted': records.values('field_name').distinct().count(),
                'extraction_methods': {},
                'confidence_levels': {},
                'content_types': {},
                'nested_records': records.filter(parent_record__isnull=False).count(),
                'session_duration': None
            }
            
            # Count by extraction method
            for method in ['page_selection', 'text_input', 'xpath_edit']:
                stats['extraction_methods'][method] = records.filter(extraction_method=method).count()
            
            # Count by confidence level
            for level in ['high', 'medium', 'low']:
                stats['confidence_levels'][level] = records.filter(confidence_level=level).count()
            
            # Count by content type
            for content_type in ['text', 'list', 'nested_data', 'html', 'number', 'url']:
                stats['content_types'][content_type] = records.filter(content_type=content_type).count()
            
            # Calculate session duration if records exist
            if records.exists():
                first_record = records.order_by('created_at').first()
                last_record = records.order_by('created_at').last()
                stats['session_duration'] = (last_record.created_at - first_record.created_at).total_seconds()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating extraction statistics: {e}")
            return {}

    # Legacy compatibility methods (for backward compatibility)
    def save_field_selector(self, field_name: str, xpath: str, css_selector: str = "",
                           requires_manual_input: bool = False, manual_input_note: str = "",
                           domain: str = None) -> bool:
        """
        Legacy compatibility method - redirects to AI preparation record.
        """
        logger.warning("save_field_selector is deprecated, using AI preparation record instead")
        return self.save_ai_preparation_record(
            field_name=field_name,
            extracted_content=manual_input_note if requires_manual_input else "",
            xpath=xpath,
            css_selector=css_selector,
            user_comment=manual_input_note,
            extraction_method="text_input" if requires_manual_input else "page_selection",
            source_url=domain or ""
        ) 