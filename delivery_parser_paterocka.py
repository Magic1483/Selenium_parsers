from bs4 import BeautifulSoup
from undetected_chromedriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
from time import sleep

def generate_timestamp():
    return time.strftime("%Y%m%d-%H%M%S", time.localtime())

options = ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument('--headless')

driver = Chrome(options=options)
# driver.delete_all_cookies()

# current product address
url='https://www.delivery-club.ru/retail/paterocka/catalog/19286?placeSlug=pyaterochka_cefhw'

ADDRESS = 'Дубининская улица, 27с14'

products = []

driver.get(url)

wait = WebDriverWait(driver, 10)
# Switch address
# driver.find_element(By.XPATH,'//div[@class="DesktopAddressButton_root"]/button')


wait.until(EC.visibility_of_element_located((By.XPATH,'//div[@class="DesktopAddressButton_root"]/button'))).click()

# wait.until(EC.visibility_of_element_located((By.XPATH,"//div[contains(text(),'Добавить новый адрес')]"))).click()

input_address  = wait.until(EC.visibility_of_element_located((By.XPATH,'//input[@data-testid="address-input"]')))

input_address.send_keys(ADDRESS)
input_address.send_keys(Keys.RETURN)

btn = wait.until(EC.visibility_of_element_located((By.XPATH,'//button[@data-testid="desktop-location-modal-confirm-button"]')))
btn.click()
sleep(3)

# driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")#scroll bottom


sleep(6)

links = []

# get the height of the page
height = driver.execute_script("return document.body.scrollHeight")

# scroll the page to the bottom to load additional content
for i in range(0, height, 100):
    driver.execute_script("window.scrollTo(0, {});".format(i))
    l = driver.find_elements(By.XPATH,'//a[@href]')
    for j in l:
        try:
            href = j.get_attribute('href')
            if href not in links and '/retail/paterocka/product' in href:
                links.append(href)
        except: pass
    time.sleep(0.5)

print('всего ссылок ',len(links))
print(links)





# #iterate product pages
for product in links:
    driver.get(product)
    # sleep(5)
    try:
        wait.until(EC.visibility_of_element_located((By.XPATH,"//div[@class='UiKitProductFullCard_descriptionWrapper']/h2")))#шикраная штука ускоряет процесс раз в 10
    except:
        pass
    menu_list = driver.find_elements(By.XPATH,'//a[@class="UiKitBreadcrumbs_link"]/span')
    
    #Получение по типу продукта 
    try:
        type = menu_list[2].text
    except: type="non"

    name = driver.find_element(By.XPATH,"//div[@class='UiKitProductFullCard_descriptionWrapper']/h2").text

    # Проверка по имени и типу продукта 
    if 'корм' in type.lower() or 'корм' in name:
        # name = driver.find_element(By.XPATH,"//div[@class='UiKitProductFullCard_descriptionWrapper']/h2").text
        weight = driver.find_element(By.XPATH,"//div[@class='UiKitProductFullCard_weight']").text
        price = driver.find_element(By.XPATH,"//div[@class='UiKitProductFullCard_control UiKitProductFullCard_priceControl']/div[@class='UiKitCorePrice_root']/span").text
        about = driver.find_elements(By.XPATH,"//div[@class='UiKitProductCardDescriptions_descriptionText UiKitProductCardDescriptions_notExpanded UiKitProductCardDescriptions_descriptionTextShort']")

        retailer = about[0].text
        country = about[1].text
        try:
            brand = about[2].text
        except:
            brand="не указано"
        link = product
        load_timestamp = generate_timestamp()
        name_mapped=""
        comment=""

        price = price.replace('\u2009\u2009','')

        tmp = [load_timestamp,
               retailer,
               country,
               name,
               name_mapped,
               link,
               price,
               brand,
               weight,
               comment]
        
        if tmp not in products:
            products.append(tmp)
            print(tmp)

print(f'найдено {len(products)} кормов')



driver.quit()








