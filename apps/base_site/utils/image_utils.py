"""
Image utilities for downloading and processing images from URLs.

Created by: Azure Hawk
Date: 2025-01-22
Project: Triad Docker Base
"""

import requests
import logging
from urllib.parse import urljoin, urlparse
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from wagtail.images.models import Image
import os
import time

logger = logging.getLogger(__name__)


def download_image_from_url(url, title=None, alt_text=None, timeout=30):
    """
    Download image from URL and create Wagtail Image object.
    
    Args:
        url (str): URL of the image to download
        title (str, optional): Title for the image object
        alt_text (str, optional): Alt text suggestion for SEO (used as title if title not provided)
        timeout (int): Request timeout in seconds
        
    Returns:
        Image or None: Wagtail Image object if successful, None if failed
    """
    try:
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            logger.warning(f"Invalid URL format: {url}")
            return None
        
        # Set up request headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Download image
        logger.info(f"Downloading image from: {url}")
        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        if not content_type.startswith('image/'):
            logger.warning(f"URL does not return image content: {url} (content-type: {content_type})")
            return None
        
        # Get filename from URL
        filename = os.path.basename(parsed_url.path)
        if not filename or '.' not in filename:
            # Generate filename from content type
            extension_map = {
                'image/jpeg': '.jpg',
                'image/jpg': '.jpg', 
                'image/png': '.png',
                'image/gif': '.gif',
                'image/webp': '.webp'
            }
            extension = extension_map.get(content_type, '.jpg')
            filename = f"downloaded_image_{int(time.time())}{extension}"
        
        # Create title from alt text or title parameter or filename
        if not title:
            if alt_text:
                # Use alt text as title for SEO
                title = alt_text
            else:
                # Fallback to cleaned filename
                title = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title()
        
        # Check if image already exists (by title)
        try:
            existing_image = Image.objects.get(title=title)
            logger.info(f"Image already exists with title: {title}")
            return existing_image
        except Image.DoesNotExist:
            pass
        
        # Create Wagtail Image object
        content = ContentFile(response.content, name=filename)
        image = Image(title=title, file=content)
        image.save()
        
        logger.info(f"Successfully created image: {title} (ID: {image.id})")
        return image
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout downloading image: {url}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error downloading image {url}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error downloading image {url}: {str(e)}")
        return None


def process_image_urls(image_urls, alt_texts=None, base_url=None):
    """
    Process a list of image URLs and create Wagtail Image objects.
    
    Args:
        image_urls (list): List of image URLs
        alt_texts (list, optional): List of alt text suggestions for SEO
        base_url (str, optional): Base URL for relative URLs
        
    Returns:
        list: List of successfully created Image objects
    """
    if not image_urls:
        return []
    
    images = []
    alt_texts = alt_texts or []
    
    for i, url in enumerate(image_urls):
        try:
            # Convert relative URLs to absolute URLs
            if base_url and not url.startswith(('http://', 'https://')):
                url = urljoin(base_url, url)
            
            # Get alt text for this image for SEO
            alt_text = alt_texts[i] if i < len(alt_texts) else None
            
            # Download image with alt text for SEO
            image = download_image_from_url(url, alt_text=alt_text)
            if image:
                images.append(image)
            else:
                logger.warning(f"Failed to download image {i + 1}: {url}")
                
        except Exception as e:
            logger.error(f"Error processing image {i + 1} ({url}): {str(e)}")
            continue
    
    logger.info(f"Successfully processed {len(images)} out of {len(image_urls)} images")
    return images


def create_gallery_images(page, images, alt_texts=None):
    """
    Create gallery images for a lab equipment page.
    
    Args:
        page: LabEquipmentPage instance
        images (list): List of Wagtail Image objects (already have SEO alt text as title)
        alt_texts (list, optional): List of alt text suggestions (used during image creation)
        
    Returns:
        list: List of created LabEquipmentGalleryImage objects
    """
    if not images:
        return []
    
    from apps.base_site.models import LabEquipmentGalleryImage
    
    gallery_images = []
    
    for i, image in enumerate(images):
        try:
            # Create gallery image - no caption field, alt text is stored in image.title
            gallery_image = LabEquipmentGalleryImage(
                page=page,
                internal_image=image,
                sort_order=i
            )
            gallery_image.save()
            gallery_images.append(gallery_image)
            
        except Exception as e:
            logger.error(f"Error creating gallery image {i + 1}: {str(e)}")
            continue
    
    logger.info(f"Created {len(gallery_images)} gallery images for page: {page.title}")
    return gallery_images 