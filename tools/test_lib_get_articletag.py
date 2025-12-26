import os
import json
from lib_get_articletag import get_article_containers

# Test with existing files
if __name__ == "__main__":
    try:
        # Use the same file paths as in the original code
        html_path = 'index2.html'
        config_path = 'scrapy_page1.json'
        
        # Check if files exist
        if not os.path.exists(html_path):
            print(f"HTML file not found: {html_path}")
            exit(1)
        html_content = open(html_path, 'r', encoding='utf-8').read()

        if not os.path.exists(config_path):
            print(f"Config file not found: {config_path}")
            exit(1)
        
        # Read and parse config file
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Get article containers
        containers = get_article_containers(html_content, config)
        print(f"find {len(containers)} article containers")
        
    except Exception as e:
        print(f"Error: {e}")
