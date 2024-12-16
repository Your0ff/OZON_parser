import time

from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from bs4 import BeautifulSoup as bs
import json


def get_html(url):
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(500, 500)
    driver.get(url=url)
    button = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'rb')))
    time.sleep(0.3)
    button.click()
    time.sleep(0.3)
    soup = bs(driver.page_source, "html.parser")
    time.sleep(0.3)
    driver.close()
    driver.quit()
    return soup


def get_articule(articules):

    dct = dict()

    soup = get_html(f'https://www.ozon.ru/product/{articules}')

    try:
        div_data = soup.find(id='state-webGallery-3311629-default-1')['data-state']
    except TypeError:
        div_data = soup.find(id='state-webGallery-3311626-default-1')['data-state']

    div_title = soup.find(id='state-webStickyProducts-726428-default-1')['data-state']
    div_price = soup.find(id='state-webPrice-3121879-default-1')['data-state']
    dct['img'] = json.loads(div_data)['images'][0]['src']
    dct['name'] = json.loads(div_title)['name']
    dct['article'] = articules
    dct['seller'] = json.loads(div_title)['seller']['name']
    dct['allprice'] = [json.loads(div_price)["price"].replace('\u2009', ' '),
                       json.loads(div_price)["cardPrice"].replace('\u2009', ' ')]

    return dct


if __name__ == "__main__":
    print(get_articule(input()))
