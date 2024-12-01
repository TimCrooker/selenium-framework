from selenium.webdriver.common.by import By

def extract_text_from_element(element):
    return element.text if element else ""

def extract_list_items(element):
    items = element.find_elements(By.TAG_NAME, 'li')
    return [item.text for item in items if item]

def extract_table_data(element):
    rows = element.find_elements(By.TAG_NAME, 'tr')
    table_data = []
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, 'td')
        row_data = [cell.text for cell in cells if cell]
        table_data.append(row_data)
    return table_data

def extract_attribute_from_element(element, attribute):
    if element:
        return element.get_attribute(attribute)
    return None

def extract_all_links(driver):
    links = driver.find_elements(By.TAG_NAME, 'a')
    return [link.get_attribute('href') for link in links if link.get_attribute('href')]

def extract_images(driver):
    images = driver.find_elements(By.TAG_NAME, 'img')
    return [img.get_attribute('src') for img in images if img.get_attribute('src')]

def extract_form_inputs(form_element):
    inputs = form_element.find_elements(By.TAG_NAME, 'input')
    return {input_elem.get_attribute('name'): input_elem.get_attribute('value') for input_elem in inputs if input_elem.get_attribute('name')}
