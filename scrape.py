"""
TODO: Scrape digitalkamera.de instead of digicamfinder.com since it has more info
"""

import os
import sqlite3
import sys
import time

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class Scrape:
    """
    :param self:
    :return:
    """
    def __init__(self):
        super.__init__()

    def main(self):
        """
        :param self:
        :return:
        """
        self.driver = self.setup_driver()

    def setup_driver(self):
        """
        Setup the webdriver for the application.

        :return: Configured Chrome webdriver
        """
        if getattr(sys, "frozen", False):
            # Running as packaged executable, driver is in same directory
            base_path = sys._MEIPASS
        else:
            # Running as normal script, driver is in parent directory
            base_path = os.path.dirname(os.path.abspath(__file__))
        chromedriver_path = os.path.join(base_path, 'chromedriver.exe')
        chrome_options = webdriver.ChromeOptions()
        chrome_options.binary_location = os.path.join(base_path, 'chrome', 'win64-118.0.5993.70', 'chrome-win64',
                                                      'chrome.exe')

        service = Service(chromedriver_path)

        try:
            return webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            print(f"An error occurred: {e}")

    def setup_db(self):
        """
        :return: This method sets up a connection to a SQLite database named "CameraArchive.db" and creates a cursor
        object for executing SQL statements.

        """
        self.conn = sqlite3.connect("CameraAarchive.db")
        self.c = conn.cursor()

    def scrapeNet(self):
        """

        """
        self.driver.get("https://www.digitalkamera.de/Kamera/Schnellzugriff.aspx")

        # wait for page to load
        self.wait(EC.visibility_of_element_located((By.CSS_SELECTOR, "div[id='center-col'] h2")))

        # get content container
        content_container = self.wait(EC.presence_of_element_located((By.CSS_SELECTOR, ".schnellzugriff-links")))
        brand_elements = content_container.find_elements(By.CLASS_NAME, 'schnellzugriff-hersteller')
        product_elements = content_container.find_elements(By.CLASS_NAME, 'schnellzugriff-produkt')

        brand_link_dict = {}

        # If the brand_elements and product_elements have the same length
        if len(brand_elements) == len(product_elements):
            for i in range(len(brand_elements)):
                camera_elements = product_elements[i]
                camera_link_elements = camera_elements.find_elements(By.TAG_NAME, 'a')

                links = [element.get_attribute('href') for element in camera_link_elements]
                brand_link_dict[brand_elements[i].text] = links
        else:
            print("Error: Mismatch in the length of brand and product elements.")

    def wait(self, condition):
        """
        :param condition: The condition to wait for
        :return: The result of WebDriverWait's 'until' method
        """
        return WebDriverWait(self.driver, 10).until(condition)


if __name__ == '__main__':
    scrape = Scrape()
    scrape.main()
    time.sleep(2)
