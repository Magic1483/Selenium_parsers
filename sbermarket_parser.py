# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
from time import sleep
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import json
import time

from undetected_chromedriver import Chrome, ChromeOptions

def generate_timestamp():
    return time.strftime("%Y%m%d-%H%M%S", time.localtime())

links = []
products = []

options = ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument('--headless')
driver = Chrome(options=options)
wait = WebDriverWait(driver, 10)

driver.get('https://sbermarket.ru/')


# Load JSON Cookie
with open('sbermarket_msk_cookie.json') as f:
    cookie_dict = json.load(f)

# wait.until(EC.visibility_of_element_located((By.XPATH,"//a[@class='Link_root__fd7C0 Link_disguised__PSFAR ProductCardLink_root__69qxV']")))
sleep(5)
#set cookie from file
driver.delete_all_cookies()
for i in cookie_dict:
    del i['sameSite']
    driver.add_cookie(i)

# driver.refresh()
driver.get('https://sbermarket.ru/magnit_express/c/voda-soki-napitki-copy')

wait.until(EC.visibility_of_element_located((By.XPATH,"//a[@class='Link_root__fd7C0 Link_disguised__PSFAR ProductCardLink_root__69qxV']")))
for i in range(5):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    sleep(1)
    driver.execute_script("window.scrollTo(0, -document.body.scrollHeight);")
    
    sleep(1)

link_elements = driver.find_elements(By.XPATH,"//a[@class='Link_root__fd7C0 Link_disguised__PSFAR ProductCardLink_root__69qxV']")
for i in link_elements:
    links.append(i.get_attribute('href'))

print('Найдено ссылок: ',len(links))
# print(links)
sleep(5)

for i in links:
    driver.get(i)
    wait.until(EC.visibility_of_element_located((By.XPATH,"//h1[@class='ProductTitle_title__aJyqe']")))

    load_timestamp = generate_timestamp()
    retailer = 'Магнит'
    city = 'Самара'

    name = driver.find_element(By.XPATH,"//h1[@class='ProductTitle_title__aJyqe']").text
    link = i

    prices = driver.find_elements(By.XPATH,"//div[@class='PriceContent_price__8BKOP']/div")
    brand = driver.find_element(By.XPATH,'//div[@itemprop="brand"]').text
    volume = driver.find_element(By.XPATH,'//p[@class="PriceContent_volume__uz5CW"]').text
    status = driver.find_element(By.XPATH,"//div[@class='PriceCell_addToCart__Sc6ok']/button").text
    
    
    pack_type = driver.find_elements(By.XPATH,"//li/div[contains(text(),'Вид упаковки')]//parent::*/div")[1].text
    
    
        
    
    if len(prices)==2:
        price = prices[0].text
        price_discount = prices[1].text
    else:
        price = prices[0].text
        price_discount = 0

    if status!='Нет в наличии':
        print(name,brand,price,price_discount,volume,pack_type)
        products.append([load_timestamp,retailer,city,name,link,price,price_discount,brand,volume,pack_type])
    else:
        print('Нет в наличии')

print('Загружено товаров: ',len(products))
driver.quit()
