"""
Tool Scrapes digitalkamera.com and creates a Database from the information gathered
Currently Console Controlled
GUI planned in the future
various interactions via console for control over the process
"""

import os
import sqlite3
import sys
import time

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from unidecode import unidecode


class UserInteraction:
    """
    Facilitates user interaction for selecting camera brands and configuring scraping options.

    This class provides methods for users to select camera brands, enable headless mode, skip camera scraping,
    and enable console feedback. It ensures that user inputs are validated and processed correctly.

    """

    def brand_selection():
        """
        Allows the user to select from a list of camera brands.

        The user can choose from a list of available camera brands by entering the corresponding number next to the
        brand. The user can continue selecting brands until they decide to proceed by typing 'y'. The selected brands
        are stored in a list and returned once the selection process is completed.

        Returns:
            tuple: A tuple containing a list of selected camera brands and a boolean indicating whether to scrape
            lenses.
        """
        brands = ['Nikon', 'Sony', 'Canon', 'Leica', 'Fujifilm']
        selected_brands = []
        scrape_lenses = False

        while brands:
            print("________________________________________________________________"
                  "\nSelect Brands to Scrape by typing the Number and hitting 'Enter'"
                  "\n\nAvailable Brands to Scrape:")
            for idx, brand in enumerate(brands, 1):
                print(f"{idx}: {brand}")
            print("________________________________________________________________")

            print("\nOnce you're done with your selection, type 'y' to continue.")
            user_input = input("\nAnswer: ")

            if user_input == 'y' and not selected_brands:
                print("\n!!!!!!!!!!!!!!!!!!"
                      "\nNo Brands selected"
                      "\nPlease select at least one Brand to scrape."
                      "\n!!!!!!!!!!!!!!!!!!")

            elif user_input.lower() == 'y':
                break  # Exit the selection loop if the user confirms with 'y' and has selected brands

            if user_input.isdigit() and 1 <= int(user_input) <= len(brands):
                selected_brand = brands.pop(int(user_input) - 1)
                selected_brands.append(selected_brand)
                print(f"\nYou've selected: {selected_brands}")
            else:
                print("\nWrong Input! Please try again.")

        # Ask if the user wants to scrape lenses after brand selection or if no brands are left to select
        print("_______________"
              "\nSelection made!"
              "\n\nScrape lenses as well?"
              "\n"
              "\nType 'y' to scrape lenses"
              "\nType 'n' to skip lenses\n")
        while True:
            user_lens_decision = input("Answer ('y'/'n'): ")
            if user_lens_decision.lower() == 'y':
                print("Scraping lenses...")
                scrape_lenses = True
                break
            elif user_lens_decision == 'n':
                print("________________"
                      "\nSkipping lenses."
                      "\n________________")
                break
            print("Invalid input, please try again")

        return selected_brands, scrape_lenses

    def enable_headless():
        """
        Prompts the user to enable headless mode for the web scraping process.

        This method asks the user if they want to run the scraper in headless mode, which allows the scraping to
        occur without opening a browser window. It returns a boolean value based on the user's input.

        Returns:
            bool: True if headless mode is enabled, False otherwise.
        """

        print("_____________________"
              "\nRun in Headless Mode?"
              "\n- Headless Mode doesn't open a browser window while scraping"
              "\n- This enables running in Background and safes resources"
              "\n_____________________")
        while True:
            user_input = input("\nAnswer ('y'/'n'): ")

            if user_input.lower() == 'y':
                return True
            elif user_input.lower() == 'n':
                return False
            else:
                print("\nInvalid input, please try again\n")

    def skip_camera_scraping():
        """
        Prompts the user to decide whether to skip camera scraping.

        This method asks the user if they want to skip the camera scraping process and only scrape lens data.
        It returns a boolean value based on the user's input.

        Returns:
            bool: True if camera scraping is skipped, False otherwise.
        """
        print(UserInteraction.format_print("SKIP CAMS?", "Skip Camera Scraping and Scrape lenses only?"))
        while True:
            user_input = input("\nAnswer ('y'/'n'): ")

            if user_input.lower() == 'y':
                return True
            elif user_input.lower() == 'n':
                return False
            else:
                print("\nInvalid input, please try again\n")

    def enable_feedback():
        """
        Prompts the user to enable console logs during the scraping process.

        This method asks the user if they want to see console logs that provide updates about the scraping process.
        It returns a boolean value based on the user's input.

        Returns:
            bool: True if console logs are enabled, False otherwise.
        """
        print("\n____________________"
              "\nEnable Console Logs?"
              "\n- Displays Updates about the running process in the console"
              "\n- Mainly useful for Headless mode"
              "\n____________________"
              "\n\nType '1': No Logs"
              "\n\nType '2': Only Show Progress Updates"
              "\n\nType '3': Full Log, including Debug Logs")
        while True:
            user_input = input("\nAnswer: ")

            if user_input == '1':
                return False, False
            elif user_input == '2':
                return True, False
            elif user_input == '3':
                return True, True
            else:
                print("\nInvalid input, please try again\n")

    def format_print(title, text):
        # sourcery skip: instance-method-first-arg-name
        """
        Formats and centers the provided title and text for console output.

        This method creates a formatted string that centers the title and text within a line of underscores for
        better readability in the console output.

        Args:
            title (str): The title to be displayed.
            text (str): The text to be displayed.

        Returns:
            str: A formatted string with centered title and text.
        """
        line_length = len(text)  # Match the length of the second line

        # Center the text within a line of underscores
        top_line = title.center(line_length, '_')
        bottom_line = '_' * line_length

        return (f"\n{top_line}"
                f"\n{text}"
                f"\n{bottom_line}")

    def progress_bar(progress, total, bar_length=50):
        # sourcery skip: instance-method-first-arg-name
        """
        Displays or updates a console progress bar.

        Args:
            progress (int): The current progress (e.g., an iteration number).
            total (int): The total amount of progress (e.g., total iterations).
            bar_length (int): The length of the progress bar in characters (default 50).
        """
        # Calculate progress percentage and fill length
        percentage = progress / total
        fill_length = int(bar_length * percentage)

        # Create the bar
        bar = '█' * fill_length + '-' * (bar_length - fill_length)

        # Print the bar with the percentage, updating in place
        print(f'\r|{bar}| {percentage:.2%}', end='\r')

        # Ensure the bar is complete when the task is done
        if progress == total:
            print()


class Scrape:
    """
    Manages the web scraping process for camera and lens data.

    This class orchestrates the entire scraping workflow, including user interaction for brand selection,
    configuring the web driver, and processing the scraped data. It handles the storage of scraped data in a
    SQLite database.

    """

    def __init__(self):
        """
        Initializes the Scrape instance.
        """
        return

    def main(self):
        """
        Executes the main scraping process.

        This method coordinates the brand selection, user preferences, database setup, web driver configuration,
        and the scraping of camera and lens data.
        """
        self.selected_brands, self.scrape_lenses = UserInteraction.brand_selection()
        print(f"Brands selected for scraping: {self.selected_brands}")
        self.headless_mode = UserInteraction.enable_headless()
        self.skip_cameras = UserInteraction.skip_camera_scraping()
        self.progress_log_enabled, self.debug_log_enabled = UserInteraction.enable_feedback()
        self.setup_db()
        self.driver = self.setup_driver(self.headless_mode)
        self.scrape_for_links()
        self.process_cameras(self.skip_cameras)
        # self.driver.quit()

    def setup_driver(self, headless):
        """
        Configures the web driver for the scraping application.

        This method sets up the Chrome web driver with the specified options, including headless mode if enabled.
        It returns the configured web driver instance.

        Args:
            headless (bool): Indicates whether to run the web driver in headless mode.

        Returns:
            webdriver.Chrome: Configured Chrome webdriver instance.
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
        if headless:
            if self.progress_log_enabled:
                print(UserInteraction.format_print("ENABLED", "Headless Mode Enabled"))
            # Enable headless mode
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")  # Optional: speeds up headless mode on Windows
            chrome_options.add_argument("--no-sandbox")  # Recommended for certain environments
            chrome_options.add_argument("--disable-dev-shm-usage")  # Recommended for memory efficiency
        elif self.progress_log_enabled:
            print(UserInteraction.format_print("DISABLED", "Headless Mode Disabled"))

        if self.progress_log_enabled and self.debug_log_enabled:
            print(UserInteraction.format_print("ENABLED", "Progress and Debug Log Enabled"))
        elif self.progress_log_enabled:
            print(UserInteraction.format_print("ENABLED", "Progress Log Enabled"))
        else:
            print(UserInteraction.format_print("DISABLED", "All Logs Disabled"))

        service = Service(chromedriver_path)

        try:
            return webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            if self.progress_log_enabled and self.debug_log_enabled:
                print(f"An error occurred: {e}")

    def setup_db(self):
        """
        Sets up the SQLite database for storing camera and lens data.

        This method creates a connection to a SQLite database named "CameraArchive.db" and creates the necessary
        tables if they do not already exist.
        """
        self.conn = sqlite3.connect("CamerAarchive.db")
        self.c = self.conn.cursor()

        self.c.execute("""
            CREATE TABLE IF NOT EXISTS camerAarchive (
            brand TEXT,
            model TEXT PRIMARY KEY
            )
        """)
        self.conn.commit()

        self.c.execute("""
            CREATE TABLE IF NOT EXISTS lensAarchive (
            brand TEXT,
            model TEXT PRIMARY KEY
            )
        """)

        self.conn.commit()

    def scrape_for_links(self):
        """
        Scrapes camera and/or lens links from digitalkamera.de based on user selection.
        """
        if not self.skip_cameras:
            if self.progress_log_enabled:
                print(UserInteraction.format_print("GATHERING CAMERA LINKS",
                                                   "Getting page: "
                                                   "https://www.digitalkamera.de/Kamera/Schnellzugriff.aspx"))

            self.driver.get("https://www.digitalkamera.de/Kamera/Schnellzugriff.aspx")

            # Handle cookie popup if present
            try:
                popup = self.wait(EC.visibility_of_element_located((By.CSS_SELECTOR, ".fc-dialog-container")))
                reject_button = popup.find_element(By.CSS_SELECTOR, "button[aria-label='Nicht einwilligen']")
                reject_button.click()
                if self.progress_log_enabled:
                    print(UserInteraction.format_print("UPDATE", "Pop Up Cookie Window closed"))
            except Exception as e:
                if self.progress_log_enabled and self.debug_log_enabled:
                    print(f"Cookie Popup didn't show: {e}")

            # Wait for page to load
            self.wait(EC.visibility_of_element_located((By.CSS_SELECTOR, "div[id='center-col'] h2")))

            # Get content container
            content_container = self.wait(EC.presence_of_element_located((By.CSS_SELECTOR, ".schnellzugriff-links")))
            brand_elements = content_container.find_elements(By.CLASS_NAME, 'schnellzugriff-hersteller')
            product_elements = content_container.find_elements(By.CLASS_NAME, 'schnellzugriff-produkt')

            self.brand_link_dict = {}

            total_brands = len(brand_elements)

            if total_brands == len(product_elements):
                for i in range(total_brands):
                    camera_elements = product_elements[i]
                    camera_link_elements = camera_elements.find_elements(By.TAG_NAME, 'a')

                    links = [element.get_attribute('href') for element in camera_link_elements]
                    self.brand_link_dict[brand_elements[i].text] = links

                    # update progress bar
                    if self.progress_log_enabled:
                        UserInteraction.progress_bar(i + 1, total_brands)
            elif self.progress_log_enabled and self.debug_log_enabled:
                print("Error: Mismatch in the length of brand and product elements.")

            if self.progress_log_enabled and self.debug_log_enabled:
                for brand, links in self.brand_link_dict.items():
                    print(f"Brand: {brand}\nLinks: {list(links)}\n\n")

        if self.scrape_lenses:
            self.scrape_for_lens_links()

    def scrape_for_lens_links(self):  # sourcery skip: move-assign
        """
        Scrapes lens links from the digitalkamera.de website.

        This method retrieves links for lenses based on the selected brands and stores them in a dictionary for
        further processing.
        """
        if self.progress_log_enabled:
            print(UserInteraction.format_print("GATHERING LINKS",
                                               "Getting page: "
                                               "https://www.digitalkamera.de/Objektiv/Schnellzugriff.aspx"))

        self.driver.get("https://www.digitalkamera.de/Objektiv/Schnellzugriff.aspx")

        # Handle cookie popup if present
        try:
            popup = self.wait(EC.visibility_of_element_located((By.CSS_SELECTOR, ".fc-dialog-container")))
            reject_button = popup.find_element(By.CSS_SELECTOR, "button[aria-label='Nicht einwilligen']")
            reject_button.click()
            if self.progress_log_enabled:
                print(UserInteraction.format_print("UPDATE", "Pop Up Cookie Window closed"))
        except Exception as e:
            if self.progress_log_enabled and self.debug_log_enabled:
                print(f"Cookie Popup didn't show: {e}")

        try:
            lens_content_container = self.wait(EC.visibility_of_element_located(
                (By.CSS_SELECTOR, ".schnellzugriff-links")))
        except TimeoutException as e:
            print(f"Timed out trying to locate lens container: {e}")

        lens_brand_elements = lens_content_container.find_elements(By.TAG_NAME, "h3")
        lens_link_list_element = lens_content_container.find_elements(By.TAG_NAME, "div")

        self.lens_brand_link_dict = {}

        total_brands = len(lens_brand_elements)

        if len(lens_brand_elements) == len(lens_link_list_element):
            for i in range(total_brands):
                selected_brand_link_element = lens_link_list_element[i]
                selected_brand_links = selected_brand_link_element.find_elements(By.TAG_NAME, 'a')

                links = [element.get_attribute('href') for element in selected_brand_links]
                self.lens_brand_link_dict[lens_brand_elements[i].text] = links

                # update progress bar
                if self.progress_log_enabled:
                    UserInteraction.progress_bar(i + 1, total_brands)
        elif self.progress_log_enabled and self.debug_log_enabled:
            print("Error: Mismatch in the length of brand and product elements.")

        if self.progress_log_enabled:
            for brand, links in self.lens_brand_link_dict.items():
                print(f"LENS Brand: {brand}\nLinks: {list(links)}\n\n")

    def process_links(self, brands):
        """
        Filters and retrieves links associated with the specified brand names.

        Args:
            brands (list): List of brand names to filter the links.

        Returns:
            tuple: A tuple containing two lists - links for cameras and links for lenses.
        """
        camera_links = []
        lens_links = []

        if not self.skip_cameras:
            # Collect camera links only from brand_link_dict
            for brand, values in self.brand_link_dict.items():
                if brand in brands:
                    camera_links.extend(values)

        # Collect lens links only from lens_brand_link_dict
        if self.scrape_lenses:
            for brand, values in self.lens_brand_link_dict.items():
                if brand in brands:
                    lens_links.extend(values)

        return camera_links, lens_links

    def process_cameras(self, skip_cameras):
        """
        Processes the camera links and extracts specifications.

        This method navigates to each camera link, retrieves the relevant data, and stores it in the database.
        It can skip the camera scraping process based on user preference.

        Args:
            skip_cameras (bool): Indicates whether to skip camera scraping.
        """

        # Process the cameras based on the links
        camera_links, lens_links = self.process_links(self.selected_brands)

        if skip_cameras:
            if self.progress_log_enabled:
                print(UserInteraction.format_print("SKIPPING", "Skipping Cameras and proceeding with Lenses"))
            self.process_lenses(lens_links)
            return

        total_links = len(camera_links)

        for i, link in enumerate(camera_links):
            self.driver.get(link)

            # wait for page to load and get parent element
            parent_element = self.wait(EC.visibility_of_element_located((By.CSS_SELECTOR, ".dkDataSheet")))

            datasheet = parent_element.find_element(By.TAG_NAME, 'tbody')

            data_rows = datasheet.find_elements(By.TAG_NAME, 'tr')

            brand_model = data_rows[0].find_element(By.CLASS_NAME, 'colData1').text

            brand_model_split = brand_model.split(' ', 1)

            brand = brand_model_split[0]
            model = brand_model_split[1]

            if self.progress_log_enabled:
                print(UserInteraction.format_print("UPDATE", f"Processing: {brand} {model}"))
                UserInteraction.progress_bar(i + 1, total_links)

            info = {}

            for row in data_rows[1:]:
                try:
                    elements = row.find_elements(By.TAG_NAME, 'td')
                    legend = elements[0].text
                    if nested_table := elements[1].find_elements(
                            By.TAG_NAME, 'table'
                    ):
                        # If there's a nested table, iterate through its tds and concatenate results
                        sub_table_rows = nested_table[0].find_elements(By.TAG_NAME, 'tr')
                        data = [', '.join([col.text for col in sub_row.find_elements(By.TAG_NAME, 'td')]) for sub_row in
                                sub_table_rows]
                    else:
                        # If there's no nested table, just retrieve the corresponding text
                        data = elements[1].text
                    if self.progress_log_enabled and self.debug_log_enabled:
                        print(UserInteraction.format_print("UPDATE", f"{legend} = {data}"))
                    if legend is not None and data is not None and not legend[0].isdigit():
                        info[legend] = data
                    else:
                        if self.progress_log_enabled and self.debug_log_enabled:
                            print("Couldn't populate info")
                        continue
                except Exception as e:
                    if self.progress_log_enabled and self.debug_log_enabled:
                        print(f"An error occurred trying to get legend/data pairs: {e}")
                    continue

            if self.progress_log_enabled and self.debug_log_enabled:
                print(info)

            self.insert_product_specs(brand, model, info)

        if self.scrape_lenses:
            if self.progress_log_enabled:
                print(UserInteraction.format_print("UPDATE", "Proceeding with Lenses"))
            self.process_lenses(lens_links)

    def process_lenses(self, lens_links):
        """
        Processes the lens links and extracts specifications.

        This method navigates to each lens link, retrieves the relevant data, and stores it in the database.

        Args:
            lens_links (list): List of lens links to process.
        """
        for link in lens_links:
            self.driver.get(link)

            # wait for page to load and get parent element
            parent_element = self.wait(EC.visibility_of_element_located((By.CSS_SELECTOR, ".dkDataSheet")))

            datasheet = parent_element.find_element(By.TAG_NAME, 'tbody')

            data_rows = datasheet.find_elements(By.TAG_NAME, 'tr')

            brand = data_rows[0].find_element(By.CLASS_NAME, 'colData1').text

            model = data_rows[1].find_element(By.CLASS_NAME, 'colData1').text

            if self.progress_log_enabled:
                print(UserInteraction.format_print("UPDATE", f"Processing: {brand} {model}"))

            info = {}

            for index, row in enumerate(data_rows[2:]):
                try:
                    elements = row.find_elements(By.TAG_NAME, 'td')
                    if len(elements) > 1:
                        legend = elements[0].text

                        # If there's a nested table, extract and concatenate its tds
                        if nested_table := elements[1].find_elements(By.TAG_NAME, 'table'):
                            sub_table_rows = nested_table[0].find_elements(By.TAG_NAME, 'tr')
                            data = ', '.join(
                                [col.text for sub_row in sub_table_rows for col in
                                 sub_row.find_elements(By.TAG_NAME, 'td')])
                        # If there are multiple direct elements (links, br-separated text), concatenate them
                        elif len(children := elements[1].find_elements(By.XPATH, './*')) > 1:
                            data = ', '.join(child.text for child in children)
                        else:
                            # Otherwise, just retrieve the corresponding text
                            data = elements[1].text
                        if self.progress_log_enabled and self.debug_log_enabled:
                            print(UserInteraction.format_print("UPDATE", f"{legend} = {data}"))

                        if legend and data and not legend[0].isdigit():
                            info[legend] = data
                        else:
                            if self.progress_log_enabled and self.debug_log_enabled:
                                print("Couldn't populate info")
                            continue
                    elif self.progress_log_enabled and self.debug_log_enabled:
                        print(f"\nError Trace-> Row HTML: {row.get_attribute('outerHTML')}")
                        print(f"Elements: {elements} doesn't have at least 2 elements.")
                        print(f"Text: {[element.text for element in elements]}")
                        continue
                    else:
                        continue
                except Exception as e:
                    if self.progress_log_enabled and self.debug_log_enabled:
                        print(f"Error occurred in row {index + 2} trying to get legend/data pairs: {e}")
                    continue

            if self.progress_log_enabled and self.debug_log_enabled:
                print(info)
            elif self.progress_log_enabled:
                print(UserInteraction.format_print("UPDATE", f"Processed: {brand} {model}"))
            self.insert_lens_product_specs(brand, model, info)

    def wait(self, condition):
        """
        Waits for a specified condition to be met.

        This method uses WebDriverWait to pause execution until the specified condition is satisfied.

        Args:
            condition: The condition to wait for.

        Returns:
            The result of WebDriverWait's 'until' method.
        """
        return WebDriverWait(self.driver, 10).until(condition)

    def transform_column_names(self, column_names):
        """
        Transforms column names to a standardized format.

        This method modifies column names to ensure they are suitable for database storage by replacing spaces and
        special characters.

        Args:
            column_names (list): List of column names to transform.

        Returns:
            dict: A dictionary mapping original column names to transformed names.
        """

        def transform(column_name):
            """
            :param column_name:
            :return:
            """
            column_name = unidecode(column_name).replace(' ', '_').replace('(', '').replace(')', '').replace(
                '.',
                '_') \
                .replace('*', '').replace('-', '_').replace(',', '_').replace('/', '_').replace('"', '')
            # if column_name and column_name[0].isdigit():
            #     column_name = f"c{column_name}"
            if self.progress_log_enabled and self.debug_log_enabled:
                print(UserInteraction.format_print("FORMAT", f"Transformed Column Name, returning: {column_name}"))
            return column_name

        return {ori: transform(ori) for ori in column_names}

    def add_column_if_not_exists(self, column_name):
        """
        Adds a new column to the SQLite3 database if it does not already exist.

        This method checks if a specified column exists in the database table and adds it if it does not.

        Args:
            column_name (str): The name of the column to add.
        """

        column_name = self.transform_column_names([column_name])[column_name]

        if not column_name:
            return

        self.c.execute("PRAGMA table_info('camerAarchive')")
        columns = [tup[1] for tup in self.c.fetchall()]
        if column_name not in columns:
            if self.progress_log_enabled:
                print(UserInteraction.format_print("ADD", f"Adding new Column: {column_name}"))
            self.c.execute(f"ALTER TABLE camerAarchive ADD COLUMN {column_name} TEXT")
            self.conn.commit()

    def lens_add_column_if_not_exists(self, column_name):
        """
        Adds a new column to the lens SQLite3 database if it does not already exist.

        This method checks if a specified column exists in the lens database table and adds it if it does not.

        Args:
            column_name (str): The name of the column to add.
        """

        column_name = self.transform_column_names([column_name])[column_name]

        if not column_name:
            return

        self.c.execute("PRAGMA table_info('lensAarchive')")
        columns = [tup[1] for tup in self.c.fetchall()]
        if column_name not in columns:
            if self.progress_log_enabled:
                print(UserInteraction.format_print("ADD", f"Adding new Column: {column_name}"))
            self.c.execute(f"ALTER TABLE lensAarchive ADD COLUMN {column_name} TEXT")
            self.conn.commit()

    def insert_product_specs(self, brand, name, specs):
        """
        Inserts or updates camera specifications in the database.

        This method takes the brand, model name, and specifications of a camera and inserts them into the database,
        updating existing records if necessary.

        Args:
            brand (str): The brand of the camera.
            name (str): The model name of the camera.
            specs (dict): A dictionary of specifications to insert.
        """
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

        if self.progress_log_enabled:
            print(UserInteraction.format_print("INSERTING", f"Inserting Product Specs for: {brand} {name}"))

        self.c.execute(sql_query, combined_values)
        self.conn.commit()

    def insert_lens_product_specs(self, brand, name, specs):
        """
        Inserts or updates lens specifications in the database.

        This method takes the brand, model name, and specifications of a lens and inserts them into the database,
        updating existing records if necessary.

        Args:
            brand (str): The brand of the lens.
            name (str): The model name of the lens.
            specs (dict): A dictionary of specifications to insert.
        """
        transformed_columns = self.transform_column_names(specs.keys())
        specs = {k: ' '.join(v) if isinstance(v, list) else v for k, v in specs.items() if
                 transformed_columns.get(k, '').strip()}

        for ori_key, new_key in transformed_columns.items():
            if new_key.strip():
                self.lens_add_column_if_not_exists(new_key)

        placeholder_and_value_pairs = [
            (col, '?', str(v).strip()) for col, v in zip(transformed_columns.values(), specs.values())
            if col.strip() and v and str(v).strip()
        ]
        columns = ', '.join([col for col, ph, val in placeholder_and_value_pairs])
        placeholders = ', '.join([ph for col, ph, val in placeholder_and_value_pairs])
        values = [val for col, ph, val in placeholder_and_value_pairs]

        update_statements = ', '.join([f"{col} = ?" for col, ph, val in placeholder_and_value_pairs])

        sql_query = f'''INSERT INTO lensAarchive (brand, model, {columns})
                        VALUES (?, ?, {placeholders})
                        ON CONFLICT(model) DO UPDATE SET {update_statements}'''

        combined_values = [brand, name] + 2 * values

        if self.progress_log_enabled:
            print(UserInteraction.format_print("INSERTING", f"Inserting Product Specs for: {brand} {name}"))

        self.c.execute(sql_query, combined_values)
        self.conn.commit()


if __name__ == '__main__':
    scrape = Scrape()
    scrape.main()
    time.sleep(2)
