def extract_text_from_element(element):
    """Extract text from a Selenium WebElement."""
    return element.text if element else ""
