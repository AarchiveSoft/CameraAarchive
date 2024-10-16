"""
TODO: Scrape digitalkamera.de instead of digicamfinder.com since it has more info
"""

import os
import sqlite3
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from unidecode import unidecode


class UserInteraction:
    """
    Allows the user to select from a list of camera brands.

    The user can choose from a list of available camera brands by entering the corresponding number next to the
    brand.
    The user can continue selecting brands until they decide to proceed by typing 'y'.
    The selected brands are stored in a list and returned once the selection process is completed.

    :return: A list of selected camera brands chosen by the user.
    """

    def brand_selection():
        """
        Allows the user to select from a list of camera brands.

        The user can choose from a list of available camera brands by entering the corresponding number next to the
        brand.
        The user can continue selecting brands until they decide to proceed by typing 'y'.
        The selected brands are stored in a list and returned once the selection process is completed.

        :return: A list of selected camera brands chosen by the user.
        """
        brands = ['Nikon', 'Sony', 'Canon', 'Leica', 'Fujifilm']
        selected_brands = []

        while brands:
            print("\nAvailable Brands to Scrape:")
            for idx, brand in enumerate(brands, 1):
                print(f"{idx}: {brand}")

            print("\nOnce you're done with your selection, type 'y' to continue.")
            user_input = input("\nAnswer: ")

            if user_input.lower() == 'y':
                break

            if user_input.isdigit() and 1 <= int(user_input) <= len(brands):
                selected_brand = brands.pop(int(user_input) - 1)
                selected_brands.append(selected_brand)
                print(f"\nYou've selected: {selected_brands}")
            else:
                print("\nWrong Input! Please try again.")

        return selected_brands


class Scrape:
    """
    :param self:
    :return:
    """

    def __init__(self):
        return

    def main(self):
        """
        :param self:
        :return:
        """
        self.selected_brands = UserInteraction.brand_selection()
        print(f"Brands selected for scraping: {self.selected_brands}")
        self.setup_db()
        self.driver = self.setup_driver()
        self.scrape_for_links()
        self.process_cameras()
        # self.driver.quit()

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
        self.conn = sqlite3.connect("CamerAarchive.db")
        self.c = self.conn.cursor()

        self.c.execute("""
            CREATE TABLE IF NOT EXISTS camerAarchive (
            brand TEXT,
            model TEXT PRIMARY KEY
            )
        """)

    def scrape_for_links(self):
        """
        Temp
        """
        self.driver.get("https://www.digitalkamera.de/Kamera/Schnellzugriff.aspx")

        # check for - and if necessary click away - cookie popup
        popup = self.wait(EC.visibility_of_element_located((By.CSS_SELECTOR, ".fc-dialog-container")))
        reject_button = popup.find_element(By.CSS_SELECTOR, "button[aria-label='Nicht einwilligen']")
        reject_button.click()

        # wait for page to load
        self.wait(EC.visibility_of_element_located((By.CSS_SELECTOR, "div[id='center-col'] h2")))

        # get content container
        content_container = self.wait(EC.presence_of_element_located((By.CSS_SELECTOR, ".schnellzugriff-links")))
        brand_elements = content_container.find_elements(By.CLASS_NAME, 'schnellzugriff-hersteller')
        product_elements = content_container.find_elements(By.CLASS_NAME, 'schnellzugriff-produkt')

        self.brand_link_dict = {}

        # If the brand_elements and product_elements have the same length
        if len(brand_elements) == len(product_elements):
            for i in range(len(brand_elements)):
                camera_elements = product_elements[i]
                camera_link_elements = camera_elements.find_elements(By.TAG_NAME, 'a')

                links = [element.get_attribute('href') for element in camera_link_elements]
                self.brand_link_dict[brand_elements[i].text] = links
        else:
            print("Error: Mismatch in the length of brand and product elements.")

        for brand, links in self.brand_link_dict.items():
            print(f"Brand: {brand}\nLinks: {list(links)}\n\n")

    def process_links(self, brands):
        """
        :param brands: List of brand names to filter the links
        :return: List of links associated with the input brand names
        """
        links = []
        for key, values in self.brand_link_dict.items():
            if key in brands:
                links.extend(values)
        return links

    def process_cameras(self):
        """
        :return: None
        """
        # Process the cameras based on the links
        for link in self.process_links(self.selected_brands):
            self.driver.get(link)

            # wait for page to load and get parent element
            parent_element = self.wait(EC.visibility_of_element_located((By.CSS_SELECTOR, ".dkDataSheet")))

            datasheet = parent_element.find_element(By.TAG_NAME, 'tbody')

            data_rows = datasheet.find_elements(By.TAG_NAME, 'tr')

            brand_model = data_rows[0].find_element(By.CLASS_NAME, 'colData1').text

            brand_model_split = brand_model.split(' ', 1)

            brand = brand_model_split[0]
            model = brand_model_split[1]

            print(f"-----------------\n"
                  f"Brand: {brand}"
                  f"\nModel: {model}"
                  f"\n-----------------")

            info = {}

            for row in data_rows[1:]:
                try:
                    elements = row.find_elements(By.TAG_NAME, 'td')
                    legend = elements[0].text
                    # Check if there's a nested table within the td tag
                    nested_table = elements[1].find_elements(By.TAG_NAME, 'table')
                    if nested_table:
                        # If there's a nested table, iterate through its tds and concatenate results
                        sub_table_rows = nested_table[0].find_elements(By.TAG_NAME, 'tr')
                        data = [', '.join([col.text for col in sub_row.find_elements(By.TAG_NAME, 'td')]) for sub_row in
                                sub_table_rows]
                    else:
                        # If there's no nested table, just retrieve the corresponding text
                        data = elements[1].text

                    if legend is not None and data is not None and not legend[0].isdigit():
                        info[legend] = data
                    else:
                        print("Couldn't populate info")
                        continue
                except Exception as e:
                    print(f"An error occurred trying to get legend/data pairs: {e}")
                    continue

            print(info)

            self.insert_product_specs(brand, model, info)

    def wait(self, condition):
        """
        :param condition: The condition to wait for
        :return: The result of WebDriverWait's 'until' method
        """
        return WebDriverWait(self.driver, 10).until(condition)

    def transform_column_names(self, column_names):
        def transform(column_name):
            column_name = unidecode(column_name).replace(' ', '_').replace('(', '').replace(')', '').replace(
                '.',
                '_') \
                .replace('*', '').replace('-', '_').replace(',', '_')
            # if column_name and column_name[0].isdigit():
            #     column_name = f"c{column_name}"

            return column_name

        return {ori: transform(ori) for ori in column_names}

    def add_column_if_not_exists(self, column_name):
        """
        Helper method to add a new column to the SQLite3 DB.
        Look ahead method that checks if a column exists.
        :param column_name: column name
        """

        column_name = self.transform_column_names([column_name])[column_name]

        if not column_name:
            return

        self.c.execute("PRAGMA table_info('camerAarchive')")
        columns = [tup[1] for tup in self.c.fetchall()]
        if column_name not in columns:
            print(f"Adding column '{column_name}'")
            self.c.execute(f"ALTER TABLE camerAarchive ADD COLUMN {column_name} TEXT")
            self.conn.commit()

    def insert_product_specs(self, brand, name, specs):
        transformed_columns = self.transform_column_names(specs.keys())
        specs = {k: ' '.join(v) if isinstance(v, list) else v for k, v in specs.items() if
                 transformed_columns.get(k, '').strip()}

        for ori_key, new_key in transformed_columns.items():
            if new_key.strip():
                self.add_column_if_not_exists(new_key)

        placeholder_and_value_pairs = [
            (col, '?', str(v).strip()) for col, v in zip(transformed_columns.values(), specs.values())
            if col.strip() and v and str(v).strip()
        ]
        columns = ', '.join([col for col, ph, val in placeholder_and_value_pairs])
        placeholders = ', '.join([ph for col, ph, val in placeholder_and_value_pairs])
        values = [val for col, ph, val in placeholder_and_value_pairs]

        update_statements = ', '.join([f"{col} = ?" for col, ph, val in placeholder_and_value_pairs])

        sql_query = f'''INSERT INTO camerAarchive (brand, model, {columns})
                        VALUES (?, ?, {placeholders})
                        ON CONFLICT(model) DO UPDATE SET {update_statements}'''

        combined_values = [brand, name] + 2 * values

        self.c.execute(sql_query, combined_values)
        self.conn.commit()


if __name__ == '__main__':
    scrape = Scrape()
    scrape.main()
    time.sleep(2)
