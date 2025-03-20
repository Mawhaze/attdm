import csv
import json
import io
import time
import requests
import os 

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class LootManager:
    """
    Manages loot for a campaign including loot table generation.
    Validates player character specific loot options.

    Args:
        csv_file_path (str, optional): The directory to save the downloaded file. Defaults to the current directory.
    """
    def __init__(self, dbm):
        self.dbm = dbm
        self.table_name = "loot_options"
        self.download_file_path = "/home/mawhaze/code/project_ender/attdm/tmp/loot_table"
        self.csv_file_name = "Items.csv"
        self.csv_file_path = os.path.join(self.download_file_path, self.csv_file_name)

    def get_base_loot_table(self):
        """
        Simulates a user clicking a download button on a webpage using Selenium,
        """
        url = "http://localhost:5000/items.html"
        chrome_driver_path = os.getenv("CHROME_DRIVER_PATH")

        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_experimental_option("prefs", {
                "download.default_directory": self.csv_file_path,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": False
            })

            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)
            if "5etools" in driver.title: 
                print("Page loaded successfully.")
            else:
                print("Page did not load successfully.")

            table_view_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='btn-show-table']"))
            )
            table_view_button.click()
            print("Table view button clicked successfully.")

            download_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[4]/div/div[1]/div[4]/button[1]"))
            )
            download_button.click()
            print("Download button clicked successfully.")

            # Wait for the download to complete
            time.sleep(5)

            return True

        except Exception as e:
            print(f"Error during download: {e}")
            return False

        finally:
            if driver:
                driver.quit()
            
    def csv_to_json(self):
        """
        Converts a CSV file to a JSON object.
        """
        if not os.path.isfile(self.csv_file_path):
            print("File not found, or is not a valid file.")
            print(self.csv_file_path)
            return

        data = []
        with open(self.csv_file_path, 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                data.append(row)
        
        json_data = json.dumps(data, indent=4)
        print("JSON data converted successfully.")
        return json_data

    def add_source_loot(self, source_book, campaign_id):
        """
        Add a source book's magic items to the loot table.
        Cleans up the item entries.
        """
        target_key = "Source"
        keys_to_keep = ["Name", "Type", "Rarity", "Attunement", "Source", "Text"]
        filtered_items = []

        json_data = self.csv_to_json()

        def search(data):
            if isinstance(data, dict):
                if data.get(target_key) == source_book:
                    filtered_item = {k: data.get(k, '') for k in keys_to_keep}
                    filtered_items.append(filtered_item)
                else:
                    for v in data.values():
                        search(v)
            elif isinstance(data, list):
                for item in data:
                    search(item)

        if isinstance(json_data, str):
            json_data = json.loads(json_data)

        search(json_data)

        for item in filtered_items:
            lowercase_item = {k.lower(): v for k, v in item.items()}

            # Convert any JSON fields to strings
            for key, value in lowercase_item.items():
                if isinstance(value, (dict, list)):
                    lowercase_item[key] = json.dumps(value)

            self.dbm.insert_data(self.table_name, lowercase_item)

        print("Loot table generated successfully and added to the database.")
        return filtered_items 

# class LootGenerator:
#     """
#     Generates loot for a player character and validates the loot options against 
#     Type, Rarity, and player inventory.
#     """
#     def __init__(self, dbm):
#         self.dbm = dbm
#         self.table_name = "loot_options"
        