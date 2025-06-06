#!/usr/bin/env python3
import logging
import os
import requests
from urllib.parse import urlparse
from django.core.files.base import ContentFile
from wagtail.images.models import Image

logger = logging.getLogger(__name__)

class ImageDownloader:
    """
    Helper class to download and save images for products.
    """
    
    @staticmethod
    def download_image(url, title=None):
        """
        Download image from URL and create a Wagtail Image.
        
        Args:
            url: URL of the image to download
            title: Title for the image (default: derived from URL)
            
        Returns:
            Wagtail Image object if successful, None otherwise
        """
        if not url:
            logger.warning("Empty URL provided for image download")
            return None
            
        try:
            # Get the image file name from the URL
            parsed_url = urlparse(url)
            file_name = os.path.basename(parsed_url.path)
            
            # Use the file name as title if none provided
            if not title:
                title = os.path.splitext(file_name)[0]
                
            # Download the image
            response = requests.get(url, stream=True)
            if response.status_code != 200:
                logger.error(f"Failed to download image from {url}: {response.status_code}")
                return None
                
            # Create a ContentFile from the downloaded image
            image_content = ContentFile(response.content, name=file_name)
            
            # Create the Wagtail Image
            image = Image.objects.create(
                title=title,
                file=image_content
            )
            
            logger.info(f"Successfully downloaded image: {title}")
            return image
            
        except Exception as e:
            logger.error(f"Error downloading image from {url}: {e}")
            return None
            
    @staticmethod
    def download_multiple_images(urls, title_prefix="Product Image"):
        """
        Download multiple images and return a list of Wagtail Image objects.
        
        Args:
            urls: List of image URLs to download
            title_prefix: Prefix for image titles
            
        Returns:
            List of Wagtail Image objects (successful downloads only)
        """
        images = []
        
        for i, url in enumerate(urls):
            title = f"{title_prefix} {i+1}"
            image = ImageDownloader.download_image(url, title)
            if image:
                images.append(image)
                
        logger.info(f"Downloaded {len(images)} of {len(urls)} images")
        return images 