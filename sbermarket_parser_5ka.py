# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
from time import sleep
from datetime import datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
#from utils.insert_into_ch_table import insert_into_ch_table
#from utils.get_attribute_from_name import get_attribute_from_name
from get_carbonated_flg import get_carbonated_flg
from clickhouse_driver import Client
import pendulum
import re

import json
import time
import sys
sys.path.append('/mnt/d/utils')

from undetected_chromedriver import Chrome, ChromeOptions

LOCAL_TZ = pendulum.timezone("Europe/Moscow")



load_timestamp = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")


data = []
options = ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
# options.add_argument('--headless')
driver = Chrome(options=options)
wait = WebDriverWait(driver, 10)


def ScrollPageForLoad():
    #листаем страницу туда сюда, чтобы прогрузилась
    wait.until(EC.visibility_of_element_located((By.XPATH,"//a[@class='Link_root__fd7C0 Link_disguised__PSFAR ProductCardLink_root__69qxV']")))
    for i in range(15):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(2)
        driver.execute_script("window.scrollTo(0, -document.body.scrollHeight);")
        
        sleep(2)

def CheckExists(name,price,data):
    for el in data:
        if el[3]==name and el[6]==price:
            return True
    return False

driver.get('https://sbermarket.ru/')


# Load JSON Cookie
#with open('sbermarket_magnit_moscow_cookie.json') as f:
with open('sbermarket_magnit_samara_cookie.json') as f:
#with open('sbermarket_5ka_samara_cookie.json') as f:
    cookie_dict = json.load(f)

sleep(5)
#set cookie from file
driver.delete_all_cookies()
for i in cookie_dict:
    del i['sameSite']
    driver.add_cookie(i)

# driver.refresh()
driver.get('https://sbermarket.ru/magnit_express/c/voda-soki-napitki-copy')
#driver.get('https://sbermarket.ru/5ka/c/voda-soki-napitki-copy')


# sleep(5)

ScrollPageForLoad()

#GET SUBCATEGORY

subcategory_setions = driver.find_elements(By.XPATH,"//section[@class='TaxonPreview_root__Q4a7h']")
subcategory_info =[]

sleep(5)
#загрузка подкатегорий
for i in subcategory_setions:
    
    
        subcategory_name = i.find_element(By.XPATH,".//div[@class='Link_iconContainer__YX1oQ']").text
        try:
            subcategory_link = i.find_element(By.XPATH,".//a[@class='Link_root__fd7C0 LinkButton_root__QQOLn LinkButton_outline__OOWhz LinkButton_primary___TA53 LinkButton_smSize__Pm2CT']").get_attribute('href')
            subcategory_info.append({'subcategory_name':subcategory_name,'link':subcategory_link})
        except:
            pass
        
    

print(len(subcategory_info))

# sleep(15)
#----------

#загрузка карточек продуктов в категории 
for sub_link in subcategory_info:#category parsing
    driver.get(sub_link['link'])
    ScrollPageForLoad()

    #--PARSING--
    links = []
    link_elements = driver.find_elements(By.XPATH,"//a[@class='Link_root__fd7C0 Link_disguised__PSFAR ProductCardLink_root__69qxV']")
    for i in link_elements:
        links.append(i.get_attribute('href'))

    print('Найдено ссылок: ',len(links),sub_link['subcategory_name'])
    # print(links)
    sleep(5)
    count_added =0
    count_exists =0

    for i in links:#product parsing
        driver.get(i)
        wait.until(EC.visibility_of_element_located((By.XPATH,"//h1[@class='ProductTitle_title__aJyqe']")))

        retailer = 'Магнит'
        city = 'Самара'
        subcategory = sub_link['subcategory_name']

        name = driver.find_element(By.XPATH,"//h1[@class='ProductTitle_title__aJyqe']").text
        link = i

        prices = driver.find_elements(By.XPATH,"//div[@class='PriceContent_price__8BKOP']/div")
        brand = driver.find_element(By.XPATH,'//div[@itemprop="brand"]').text

        try:
            brand = driver.find_element(By.XPATH,'//div[@itemprop="brand"]').text
        except:
            brand="не указано"
        brand = str.upper(brand)

        volume = driver.find_element(By.XPATH,'//p[@class="PriceContent_volume__uz5CW"]').text
        volume = volume.replace('мл','').replace('л','').replace(',','.')
        volume = re.sub(r'[^0-9.]', '', volume)
        volume = float(volume)

        if volume > 900 or volume <= 6:
            volume = volume * 1000
        
        #status = driver.find_element(By.XPATH,"//div[@class='PriceCell_addToCart__Sc6ok']/button").text
        try:
            pack_type = driver.find_elements(By.XPATH,"//li/div[contains(text(),'Вид упаковки')]//parent::*/div")[1].text
        except:
            pack_type = ""
        try:
            carbonation = driver.find_elements(By.XPATH,"//li/div[contains(text(),'Газирование')]//parent::*/div")[1].text
            if not carbonation:
                carbonation = get_carbonated_flg(name)
        except:
            carbonation = get_carbonated_flg(name)
        try:
            pack_count =  driver.find_elements(By.XPATH,"//li/div[contains(text(),'Количеств')]//parent::*/div")[1].text

            if pack_count:
                pack_count = int(re.sub('\D',"",pack_count))
        except:
            pack_count = 1
        
            
        
        if len(prices)==2:
            price = prices[1].text
        else:
            price = prices[0].text
            price_discount = 0
        price = price.replace('\u2009\u2009','').replace("₽","").replace(",",".")
        price = float(price)

        name_mapped = ''

        # if status!='Нет в наличии':
        #     print(name,brand,price,price_discount,volume,pack_type,link)
        #     products.append([load_timestamp,retailer,city,name,link,price,price_discount,brand,volume,pack_type])
        # else:
        #     print('Нет в наличии')

        comment = ''
        #if status!='Нет в наличии':
        data_row = [
                        load_timestamp,
                        retailer,
                        city,
                        name,
                        name_mapped,
                        link,
                        price,
                        brand,
                        volume,
                        carbonation,
                        pack_type,
                        pack_count,
                        comment,
                        subcategory
                                ]
        if not CheckExists(name=name,price=price,data=data):
            data.append(data_row)
            count_added+=1
        else:
            count_exists+=1

    print('END parsing',sub_link['link'],'count added',count_added,'count exists',count_exists)
        
print('Загружено товаров: ',len(data))
sleep(15)
#добавляем записи в таблицу
            
driver.quit()


