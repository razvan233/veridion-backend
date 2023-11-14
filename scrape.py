from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from openai import OpenAI
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CLASS_NAME_GOOGLE_MAPS_LINK = "hfpxzc"
CLASS_NAME_GOOGLE_MAPS_NAV_BUTTONS = "hh2c6"
CLASS_NAME_GOOGLE_MAPS_REVIEW = "MyEned"

def generate_url(subject:str, lat:float, long:float):
    return '''https://www.google.com/maps/search/{}/@{},{},18z?hl=en&radius=10km'''.format(subject, lat, long)

def accept_cookies(driver: webdriver.Chrome, ttw: int):
    "ttw - time to wait in seconds"    
    WebDriverWait(driver, ttw).until(EC.presence_of_element_located((
        By.XPATH, '/html/body/c-wiz/div/div/div/div[2]/div[1]/div[3]/div[1]/div[1]/form[2]/div/div/button')))
    accept_button = driver.find_element(
        By.XPATH, '/html/body/c-wiz/div/div/div/div[2]/div[1]/div[3]/div[1]/div[1]/form[2]/div/div/button')
    accept_button.click()

def scrap_company(driver: webdriver.Chrome, company_name: str, latitude: float, longitude: float, ttw: int):    
    "ttw - time to wait in seconds before accepting cookies and loading the page"
    url = generate_url(company_name, latitude, longitude)
    driver.get(url)
    accept_cookies(driver, ttw)
    html_page = driver.page_source
    soup = BeautifulSoup(html_page, 'html.parser')
    WebDriverWait(driver, ttw).until(EC.presence_of_element_located((By.CLASS_NAME, CLASS_NAME_GOOGLE_MAPS_LINK)))
    google_page = soup.find_all(
        'a', attrs={"class": CLASS_NAME_GOOGLE_MAPS_LINK})[0]
    google_page_url = google_page['href']
    if "hl=ro" in google_page_url:
        google_page_url = google_page_url.replace('hl=ro', 'hl=en')
    driver.get(google_page_url)
    WebDriverWait(driver, ttw).until(EC.presence_of_element_located((By.CLASS_NAME, CLASS_NAME_GOOGLE_MAPS_NAV_BUTTONS)))
    buttons = driver.find_elements(By.CLASS_NAME, CLASS_NAME_GOOGLE_MAPS_NAV_BUTTONS)
    reviews_button = buttons[1]
    reviews_button.click()
    html_page = driver.page_source
    soup = BeautifulSoup(html_page, 'html.parser')
    reviews = soup.find_all('div', attrs={'class': CLASS_NAME_GOOGLE_MAPS_REVIEW})
    reviews_text = [review.span.get_text() for review in reviews]
    return driver, reviews_text

def summarize_reviews(reviews: list, gpt4_api_key: str):
    client = OpenAI(api_key=gpt4_api_key)
    text = ''
    for review in reviews:
        text  += review
        text  += ' '
    response = client.chat.completions.create(
        model='gpt-4',
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant asked to summarize customer reviews."
            },
            {
                "role": "user",
                "content": "Please provide a brief summary focusing on the key points and overall sentiment of these reviews: \n\n" + text 
            }
        ]
    )
    return response.choices[0].message.content.strip()

def get_reviews_summary(company_name: str, company_lat:float, company_long:float, openai_api_key:str, ttw: int = 3):
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        driver, reviews = scrap_company(driver, company_name, company_lat, company_long, ttw = ttw)
        driver.quit()
        reviews_summary = summarize_reviews(reviews, gpt4_api_key=openai_api_key)
        return reviews_summary
    except Exception as error:
        print(error)
        return ''