from datetime import datetime, timedelta
from time import sleep
import re
from collections import defaultdict
import ast
import shutil
import pendulum
from bs4 import BeautifulSoup
from selenium_profiles.profiles import profiles
from get_weight_from_name import get_weight_from_name
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from clickhouse_driver import Client
from selenium import webdriver
from selenium_stealth import stealth
from undetected_chromedriver import Chrome, ChromeOptions
from selenium.webdriver.common.keys import Keys
#from airflow import DAG
#from airflow.operators.python import PythonOperator




LOCAL_TZ = pendulum.timezone("Europe/Moscow")
# REGION = 'Самара'


def load_prices_magnit(REGION,QUERY):
    from selenium import webdriver  # pylint: disable=import-outside-toplevel

    url_prefix = "https://dostavka.magnit.ru"
    retailer = "Магнит"
    print()
    print(f"{retailer}: парсим данные...")

    driver = None
    try:
        # запускаем драйвер chrome для selenium
        #chromedriver_directory = "/home/airflow/.local/share/undetected_chromedriver/"
        chromedriver_directory = "/home/user/.local/share/undetected_chromedriver/"

        # запускаем драйвер chrome для selenium
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # options.add_argument("--headless")
        options.add_argument("--windows-size=1000x500")
        options.page_load_strategy = "none"
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager(path=chromedriver_directory).install()),
            options=options,
        )

        # открываем сайт Google и ищем сайт сети
        print("Открываем сайт Google и ищем сайт сети...")
        driver.get("https://www.google.com/")
        sleep(3)
        google_input = driver.find_element(By.CLASS_NAME, "gLFyf")
        google_input.send_keys("магнит доставка")
        search_button = driver.find_element(By.CLASS_NAME, "gNO89b")
        driver.execute_script("arguments[0].click();", search_button)
        sleep(3)

        # переходим по ссылке сети из общей выборки Google
        print("Переходим по ссылке сети из общей выборки Google...")
        magnit_link = driver.find_element(By.PARTIAL_LINK_TEXT, "dostavka")
        driver.execute_script("arguments[0].click();", magnit_link)
        sleep(3)

        # выбираем нужную категорию товаров
        # print("Выбираем категорию товаров...")
        # category_link = driver.find_elements(
        #     By.CLASS_NAME, "m-header-bottom__link.is-dynamic"
        # )[0]
        # driver.execute_script("arguments[0].click();", category_link)
        # sleep(3)

        # выбираем адрес доставки
        print("Выбираем адрес доставки...")
        address_selector = driver.find_element(By.CLASS_NAME, "select-address__address")
        driver.execute_script("arguments[0].click();", address_selector)
        sleep(3)

        address_input = driver.find_element(
            By.CLASS_NAME, "m-input-address__input-container"
        ).find_element(By.CLASS_NAME, "m-input-text__input")
        address_input.send_keys(REGION)#аддресс из аргумента функции
        sleep(3)

        address_button = driver.find_element(
            By.XPATH,
            "/html/body/div/div/div/section/div/section/div/div/div/form/div[1]/div[1]/section",
        ).find_element(By.CLASS_NAME, "m-input-address__suggestions__item")
        driver.execute_script("arguments[0].click();", address_button)
        sleep(3)

        address_button_2 = driver.find_element(
            By.CLASS_NAME,
            "m-button.user-address-map__form-submit.m-button-color--black.accept-address",
        )
        driver.execute_script("arguments[0].click();", address_button_2)
        sleep(3)

        # закрываем уведомление о том, что магазин закрыт
        try:
            store_closed = driver.find_element(
                By.CLASS_NAME,
                "m-button-icon.m-button-close.modal-abstraction__close.is-rounded",
            )
            driver.execute_script("arguments[0].click();", store_closed)
            sleep(2)
            close_popup = driver.find_element(
                By.XPATH,
                "/html/body/div[2]/div/div/section/div/section/div/div[1]/button",
            )
            driver.execute_script("arguments[0].click();", close_popup)
            sleep(2)
        except NoSuchElementException:
            pass

        # выбираем нужную категорию товаров
        # category = driver.find_element(
        #     By.XPATH,
        #     "/html/body/div/div/div/header/div/div[3]/div/a[1]",
        # )
        # driver.execute_script("arguments[0].click();", category)

        # Ищем строку поиска вписываем запрос затем нажимаем ENTER
        input = driver.find_element(By.XPATH,"//input")
        input.send_keys(QUERY)
        input.send_keys(Keys.RETURN)
        sleep(3)

        # category_filter = driver.find_element(
        #     By.XPATH,
        #     "/html/body/div[2]/div/div/main/div[2]/div[2]/div/div/main/div[1]/div/button",
        # )
        # driver.execute_script("arguments[0].click();", category_filter)
        # sleep(3)

        # subcategory = driver.find_element(
        #     By.XPATH,
        #     "/html/body/div/div/div/main/div[2]/div[2]/div/div/main/div[1]/div/section/div[2]/div/div[2]/div/section/div/ul/li[6]/a",
        # )
        # driver.execute_script("arguments[0].click();", subcategory)
        # sleep(3)

        # загружаем полный каталог товаров
        items = []
        page = 2
        while True:
            try:
                show_next = driver.find_element(
                    By.CLASS_NAME,
                    "m-button.btn-show-more.m-button-type--square.m-button-type--outline.m-button-type--large",
                )
                print(f"Загружаем страницу {page}...")
                driver.execute_script("arguments[0].click();", show_next)
                sleep(3)

                catalog_page_soup = BeautifulSoup(driver.page_source, "lxml")
                page_items = catalog_page_soup.findAll(
                    "div", "product__container product_border"
                )

                items.extend(page_items)

                page += 1
            except NoSuchElementException:
                break

        items = set(items)
        data = []
        load_timestamp = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")

        # ALL_ATTRIBUTES = []

        # перебираем товары из каталога
        for item in items:
            name = str.strip(item.find("span", class_="text__content").getText())

            # если блок с товаром не имеет ссылки - пропускаем товар
            try:
                link = url_prefix + item.find(
                    "a", class_="app-link product-card product-list__item"
                ).get("href")

                print(name)
                print(link)
            except TypeError:
                continue

            price_div = item.find("div", class_="m-price__current")
            price = str.split(price_div.find("span").getText(), " ")[0].replace(
                ",", "."
            )
            price = float(price)
            print(f"Цена: {price} руб.")

            # переходим на страницу товара
            driver.get(link)
            sleep(2)
            page_soup = BeautifulSoup(driver.page_source, "lxml")

            # парсим блок с пищевой ценностью
            nutrients_div = page_soup.find("div", class_="nutritional-values__list")
            if nutrients_div is not None:
                nutrients_dict = {}
                nutrients_div = page_soup.find("div", class_="nutritional-values__list")
                nutrients_items = nutrients_div.findAll("div", class_="nutritional-values__elem")
                for n in nutrients_items:
                    key = str.strip(
                        n.find("span", class_="nutritional-values__name").getText()
                    )
                    value = str.strip(
                        n.find("span", class_="nutritional-values__value").getText()
                    )
                    nutrients_dict[key] = value
            else:
                nutrients_dict = {
                    "белки": "0.0",
                    "жиры": "0.0",
                    "углеводы": "0.0",
                    "ккал": "0.0",
                }

            # парсим характеристики товара
            attributes = page_soup.findAll(
                "div", class_="product-characteristics__elem"
            )
            attributes_dict = {}
            for a in attributes:
                key = str.strip(
                    a.find("span", class_="product-characteristics__name").getText()
                )
                value = str.strip(
                    a.find("span", class_="product-characteristics__value").getText()
                )
                attributes_dict[key] = value

            attributes_dict = {**attributes_dict, **nutrients_dict}
            # print(attributes_dict)
            # ALL_ATTRIBUTES += attributes_dict.keys()

            #приводим характеристики товара к нужным типам
            brand = attributes_dict.get("Бренд:", "")
            # if brand == "":
            #     brand = get_attribute_from_name(client, name, "brand", table_name=TABLE_NAME)
            # brand = str.upper(brand)

            country = str.upper(attributes_dict.get("Страна происхождения:", ""))

            # food_energy_value = attributes_dict.get(
            #     "ккал", "0.0"
            # )
            # if food_energy_value == "0.0" or food_energy_value=="Не указан на упаковке":
            #     food_energy_value = attributes_dict.get(
            #         "Энергетическая_ценность:", "0.0"
            #     )
            # food_energy_value = float(
            #     food_energy_value.replace(",", ".")
            # )

            # proteins = attributes_dict.get("белки", "0.0")
            # proteins = float(str.split(proteins, " ")[0].replace(",", "."))

            # fats = attributes_dict.get("жиры", "0.0")
            # fats = float(str.split(fats, " ")[0].replace(",", "."))

            # carbonhydrates = attributes_dict.get("углеводы", "0.0")
            # carbonhydrates = float(str.split(carbonhydrates, " ")[0].replace(",", "."))

            # min_temp = float(
            #     attributes_dict.get("Мин. температура хранения, °C:", "0.0")
            # )
            # max_temp = float(
            #     attributes_dict.get("Макс. температура хранения, °C:", "0.0")
            # )
            # composition = attributes_dict.get("Состав:", "")

            product_type = attributes_dict.get("Тип продукта :")
            print(product_type)
            # if product_type == "":
            #     product_type = attributes_dict.get("Вид продуктов:", "")
            # elif product_type == "":
            #     product_type = attributes_dict.get("Вид:", "")
            # elif product_type == "":
            #     product_type = attributes_dict.get("Вид орехов:", "")
            # elif product_type == "":
            #     product_type = attributes_dict.get("Вид сухофруктов:", "")
            # elif product_type == "":
            #     product_type = get_attribute_from_name(client, name, "product_type", TABLE_NAME)

            packing_type = attributes_dict.get("Тип упаковки:", "")

            shelf_life_days = attributes_dict.get("Срок хранения", "0.0")
            if shelf_life_days == "0.0":
                shelf_life_days = attributes_dict.get("Срок годности:", "0.0")
            shelf_life_days = float(shelf_life_days)

            weight = float(attributes_dict.get("Вес, кг:", "0.0")) * 1000
            flavor = attributes_dict.get("Вкус:", "")

            name_mapped=""
            comment=""
            # добавляем характеристики в список
            data_row = [
                load_timestamp,
                retailer,
                name,
                name_mapped,
                link,
                price,
                brand,  # Бренд
                country,  # Страна-производитель
                # food_energy_value,  # Энергетическая ценность, ккал/100 г
                # proteins,  # Белки
                # fats,  # 'Жиры, г
                # carbonhydrates,  # Углеводы, г
                # min_temp,  # Температура хранения мин.
                # max_temp,  # Температура хранения макс.
                # composition,  # Состав
                # product_type,  # Тип продукта
                # packing_type,  # Тип упаковки
                # shelf_life_days,  # Срок хранения, дн
                weight,  # Вес, кг
                comment,
                # flavor,  # Вкус
            ]
            
            if 'корм' in name.lower():
                data.append(data_row)
                print('found in name')
                print(data_row)
                print("================================================================================")
            elif product_type!=None:
                if 'корм' in product_type.lower():
                    print('found in product_type')
                    data.append(data_row)
                    print(data_row)
                    print("================================================================================")
        # добавляем записи в таблицу
        #insert_into_ch_table(TABLE_NAME, data, client)

        # print(set(ALL_ATTRIBUTES))

        # удаляем файлы вебдрайвера
        # shutil.rmtree(chromedriver_directory + ".wdm/")

        # проверяем и заполняем пустые дни
        #parser_fill_empty_days(client, TABLE_NAME, retailer)

    except (NoSuchElementException, AttributeError) as e:
        if driver:
            driver.quit()
        raise e

    # останавливаем работу драйвера
    print('SUCCESSFULL COMPLETE')
    driver.quit()

load_prices_magnit('Тольяти','Корма для животных')