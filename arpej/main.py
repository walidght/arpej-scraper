from datetime import datetime
import os
import re
import json
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from .config import configs as driver_configs
import logging


def read_data_file(file_path):
    file = open(file_path, 'r', encoding='utf-8')
    data = json.load(file)
    file.close()
    return data


DIRNAME = os.path.dirname(os.path.abspath(__file__))[:-6]
SENT_PATH = f'{DIRNAME}/results/sent-{datetime.today().strftime("%d-%m")}.json'
UNWANTED_PATH = f"{DIRNAME}/all_unwanted_arpej.txt"

configs = read_data_file(f'{DIRNAME}/configs.json')
ARPEJ_LINK = configs['ARPEJ_LINK']
MAX_PRICE = configs['MAX_PRICE']
WAIT_TIME = 10


def setup_driver(configs):
    driver = webdriver.Chrome(service=Service(
        configs.chromedriver_path), options=configs.chrome_options)

    driver.set_page_load_timeout(30)  # Timeout in seconds

    return driver


def get_url(driver, url):
    try:
        driver.get(url)

        return True
    except Exception as e:
        print(f"Error opening the URL: {e}")
        return False


def reject_cookies(driver):
    # Wait for the cookie consent popup and click the "Refuser" button
    try:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.CLASS_NAME, "cky-btn-reject"))).click()
    except Exception as e:
        print(
            f"Cookie consent popup not found or error in clicking the 'Refuser' button: {e}")


def get_price_interval(text):
    match = re.search(r"de (\d+,\d+) € à (\d+,\d+) €", text)
    if match:
        return float(match.group(1).replace(',', '.')), float(match.group(2).replace(',', '.'))
    else:
        logging.warning(f"Price interval format not recognized: {text}")
        return None, None


def click_button(driver, selector):
    button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
    button.click()


def get_main_div(driver, selector):
    return WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selector)))


def close_and_switch_back(driver):
    try:
        if len(driver.window_handles) > 1:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

    except Exception as e:
        logging.error(f"Error while closing and switching back: {e}")


def load_page(driver, url):
    while not get_url(driver, url):
        continue
    return True


def wait_for_element(driver, class_name, wait_time):
    WebDriverWait(driver, wait_time).until(
        EC.presence_of_element_located((By.CLASS_NAME, class_name))
    )


def load_sent_residences(file_path):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as file:
            file.write("[]")
    with open(file_path, 'r', encoding='utf-8') as file:
        sent = json.load(file)
    return {residence['link'] for residence in sent}


def filter_residences_by_price(residences, max_price):
    return [r for r in residences if r.get('from_price', 0) < max_price]


def filter_out_sent_residences(residences, sent_links):
    return [r for r in residences if r['link'] not in sent_links]


def save_residences(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print(f"Data saved to {path}")


def get_residences(driver):
    all_unwanted = open(UNWANTED_PATH,   "r").read().splitlines()

    available_residences = []
    while True:

        # Find all the cards
        cards = driver.find_elements(By.CLASS_NAME, "card-residence")

        # Loop through each card and extract the desired information
        for card in cards:
            try:
                name = card.find_element(
                    By.CLASS_NAME, "card-residence__title").text
                address = card.find_element(
                    By.CLASS_NAME, "card-residence__address").text
                price = card.find_element(By.CLASS_NAME, "card-residence__price").text.replace(
                    "À partir de\n", "").replace("€/MOIS", "")
                link = card.get_attribute('href')
                reserved = "Résidence réservataire" in card.text
                data = {
                    "name": ' '.join(name.split()),
                    "address": ' '.join(address.split()),
                    "link": link
                }

                if not reserved and link not in all_unwanted:
                    available_residences.append(data)
            except Exception as e:
                print(f"Error extracting data from a card: {e}")

        next_button = driver.find_elements(
            By.CLASS_NAME, "pagination-arrow--next")

        if len(next_button) > 0:
            next_button[0].click()
        else:
            break
    return available_residences


def enrich_residences_with_prices(driver, available_residences):
    for residence in available_residences:
        attempt = 0
        succeeded = False
        while not succeeded and attempt < 3:
            attempt += 1
            try:
                driver.get(residence["link"])

                click_button(
                    driver, "a.folder-cta[href*='reservation-d-un-logement']")

                # Switch to the new tab
                driver.switch_to.window(driver.window_handles[1])

                # Wait for the main div to be present
                main_div = get_main_div(
                    driver, "div.accomodationCard.optional-services")

                # Find the span within the main div and get the text
                price_span = main_div.find_element(
                    By.CSS_SELECTOR, "span[data-v-fb046f6c]")
                from_price, to_price = get_price_interval(price_span.text)

                if from_price and to_price:
                    # Update the residence data
                    residence["from_price"] = from_price
                    residence["to_price"] = to_price

                succeeded = True

            except Exception as e:
                logging.error(
                    f"Error with {residence['name']} at {residence['link']} [attempt number {attempt}]")
            finally:
                close_and_switch_back(driver)

        if not succeeded:
            logging.info(
                f"Skipping {residence['name']} after 3 failed attempts")


def scrap_arpej():
    driver = setup_driver(driver_configs)

    try:
        if not load_page(driver, ARPEJ_LINK):
            print("Failed to load ARPEJ page.")
            return

        reject_cookies(driver)
        wait_for_element(driver, "residences-list__container", WAIT_TIME)

        available = get_residences(driver)
        enrich_residences_with_prices(driver, available)

        available = filter_residences_by_price(available, MAX_PRICE)

        # Ensure the sent file exists and load sent residences
        sent_links = load_sent_residences(SENT_PATH)

        available = filter_out_sent_residences(available, sent_links)

        # Save data to JSON files
        save_residences(available, f"{DIRNAME}/results/available.json")

        print("Scraping completed successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()
