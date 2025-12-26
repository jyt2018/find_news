from bs4 import BeautifulSoup
from lxml import etree
import json

def get_article_containers(html_content, config):
    """
    Extract article containers from HTML content based on configuration.
    
    Args:
        html_content (str): The HTML content to parse. 
        config (dict): Configuration dictionary containing article_item settings.
        
    Returns:
        list: List of BeautifulSoup elements representing article containers.
        
    Raises:
        ValueError: If no article containers are found.
        NotImplementedError: If the article_item type is not supported.
    """
    # Parse HTML with BeautifulSoup and lxml
    soup = BeautifulSoup(html_content, 'html.parser')
    tree = etree.HTML(html_content)  # For XPath if needed
    
    # Extract article item configuration
    article_item_conf = config['article_item']
    
    # Process based on the article item type
    if article_item_conf['type'] == 'bs4_find_all':
        selector = article_item_conf['selector']
        if isinstance(selector, dict):
            # If selector is a dictionary, unpack it as keyword arguments
            article_containers = soup.find_all(**selector)
        else:
            # If selector is a string, use it directly
            article_containers = soup.find_all(selector)
        
        if not article_containers:
            raise ValueError("No article containers found using the provided selector")
        
        return article_containers
    else:
        raise NotImplementedError(f"Article item type '{article_item_conf['type']}' is not supported")


if __name__ == "__main__":
    # Test the function with sample string and dictionary inputs
    sample_html = """<html>
<body>
    <article class="news-item">
        <h2>News Title 1</h2>
        <p>News content 1</p>
    </article>
    <article class="news-item">
        <h2>News Title 2</h2>
        <p>News content 2</p>
    </article>
</body>
</html>"""
    
    sample_config = {
        "article_item": {
            "type": "bs4_find_all",
            "selector": "article"
        }
    }
    
    print("Testing get_article_containers function with string and dictionary inputs...")
    
    try:
        # Test with sample data
        containers = get_article_containers(sample_html, sample_config)
        print(f"✓ Successfully extracted {len(containers)} article containers")
        
        # Print the content of each container
        for i, container in enumerate(containers, 1):
            print(f"\nArticle {i}:")
            print(container.h2.text)
            print(container.p.text)
            
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test edge case: no containers found
    print("\nTesting edge case: no containers found...")
    try:
        no_containers_config = {
            "article_item": {
                "type": "bs4_find_all",
                "selector": "non_existent_tag"
            }
        }
        get_article_containers(sample_html, no_containers_config)
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
