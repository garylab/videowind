import html
from typing import Any, Dict, List, Optional

import requests

from src.constants.config import WpConfig


class WordPress:
    def __init__(self, base_url: Optional[str] = None, username: Optional[str] = None, password: Optional[str] = None):
        """Initialize the WordPress API client.
        
        Args:
            base_url: WordPress site URL (e.g., https://example.com)
            username: WordPress username for authenticated requests (optional)
            password: WordPress password for authenticated requests (optional)
        """
        # Use provided parameters or fall back to config
        self.base_url = base_url or WpConfig.url
        if not self.base_url:
            raise ValueError("WordPress URL is required")
            
        self.base_url = self.base_url.rstrip('/')
        self.api_url = f"{self.base_url}/wp-json/wp/v2"
        self.username = username or WpConfig.username
        self.password = password or WpConfig.password
        self.auth = (self.username, self.password) if self.username and self.password else None

    def get_posts(self, page: int = 1, per_page: int = 10, search: str = '') -> Dict[str, Any]:
        """Get a list of posts with pagination.
        
        Args:
            page: Page number
            per_page: Number of posts per page
            search: Search keyword
            
        Returns:
            Dict containing posts and total count
        """
        params = {
            'page': page,
            'per_page': per_page,
            '_embed': 'true',  # Include featured media and author info
        }
        
        if search:
            params['search'] = search
            
        try:
            response = requests.get(f"{self.api_url}/posts", params=params)
            response.raise_for_status()
            
            # Extract total pages and posts count from headers
            total_posts = int(response.headers.get('X-WP-Total', 0))
            total_pages = int(response.headers.get('X-WP-TotalPages', 0))
            
            posts = response.json()
            
            # Clean up post data for display
            cleaned_posts = []
            for post in posts:
                cleaned_post = {
                    'id': post.get('id'),
                    'title': html.unescape(post.get('title', {}).get('rendered', '')),
                    'excerpt': html.unescape(post.get('excerpt', {}).get('rendered', '')),
                    'date': post.get('date'),
                    'link': post.get('link'),
                    'featured_image': None,
                }
                
                # Get featured image if available
                if '_embedded' in post and 'wp:featuredmedia' in post['_embedded']:
                    media = post['_embedded']['wp:featuredmedia']
                    if media and len(media) > 0 and 'source_url' in media[0]:
                        cleaned_post['featured_image'] = media[0]['source_url']
                
                cleaned_posts.append(cleaned_post)
            
            return {
                'posts': cleaned_posts,
                'total_posts': total_posts,
                'total_pages': total_pages,
                'current_page': page
            }
            
        except requests.RequestException as e:
            return {
                'error': f"Failed to fetch posts: {str(e)}",
                'posts': [],
                'total_posts': 0,
                'total_pages': 0,
                'current_page': page
            }

    def get_post(self, post_id: int) -> Dict[str, Any]:
        """Get a single post by ID.
        
        Args:
            post_id: WordPress post ID
            
        Returns:
            Dict containing post data
        """
        try:
            response = requests.get(f"{self.api_url}/posts/{post_id}?_embed=true")
            response.raise_for_status()
            
            post = response.json()
            
            # Clean up post data
            cleaned_post = {
                'id': post.get('id'),
                'title': html.unescape(post.get('title', {}).get('rendered', '')),
                'content': html.unescape(post.get('content', {}).get('rendered', '')),
                'date': post.get('date'),
                'modified': post.get('modified'),
                'link': post.get('link'),
                'featured_image': None,
                'author': None,
                'categories': [],
                'tags': []
            }
            
            # Get featured image
            if '_embedded' in post and 'wp:featuredmedia' in post['_embedded']:
                media = post['_embedded']['wp:featuredmedia']
                if media and len(media) > 0 and 'source_url' in media[0]:
                    cleaned_post['featured_image'] = media[0]['source_url']
            
            # Get author info
            if '_embedded' in post and 'author' in post['_embedded']:
                authors = post['_embedded']['author']
                if authors and len(authors) > 0:
                    cleaned_post['author'] = {
                        'name': authors[0].get('name', ''),
                        'avatar': authors[0].get('avatar_urls', {}).get('96', '')
                    }
            
            # Get categories and tags
            if '_embedded' in post and 'wp:term' in post['_embedded']:
                terms = post['_embedded']['wp:term']
                if terms and len(terms) > 0:
                    # Categories are in the first array, tags in the second
                    if len(terms) > 0:  # Categories
                        cleaned_post['categories'] = [
                            {'id': cat.get('id'), 'name': cat.get('name')}
                            for cat in terms[0] if cat.get('taxonomy') == 'category'
                        ]
                    
                    if len(terms) > 1:  # Tags
                        cleaned_post['tags'] = [
                            {'id': tag.get('id'), 'name': tag.get('name')}
                            for tag in terms[1] if tag.get('taxonomy') == 'post_tag'
                        ]
            
            return cleaned_post
            
        except requests.RequestException as e:
            return {'error': f"Failed to fetch post: {str(e)}"} 