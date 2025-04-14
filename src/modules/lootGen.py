import csv
import json
import time
import os
import logging

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.modules.playerCharacter import PCManager

# Configure logging
logging.basicConfig(
    filename=os.getenv("LOG_FILE", "/tmp/logs/attdm.log"),
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class LootManager:
    """
    Manages loot for a campaign including loot table generation.
    Validates player character specific loot options.
    """
    def __init__(self, dbm):
        self.dbm = dbm
        self.pcm = PCManager(dbm)
        self.table_name = "loot_options"
        self.download_file_path = "/tmp/loot_table"
        self.csv_file_name = "Items.csv"
        self.csv_file_path = os.path.join(self.download_file_path, self.csv_file_name)

    def get_base_loot_table(self):
        """
        Downloads the base loot table from the specified URL using Selenium.
        """
        url = os.getenv("BASE_LOOT_TABLE_URL")
        if not url:
            logging.error("BASE_LOOT_TABLE_URL environment variable is not set.")
            return False

        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_experimental_option("prefs", {
                "download.default_directory": self.download_file_path,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": False
            })

            logging.info("Initializing ChromeDriver...")
            driver = webdriver.Chrome(options=chrome_options)
            logging.info("ChromeDriver initialized successfully.")

            logging.info(f"Navigating to URL: {url}")
            driver.get(url)

            if "5etools" in driver.title:
                logging.info("Page loaded successfully.")
            else:
                logging.warning(f"Page did not load successfully. Title: {driver.title}")

            logging.info("Waiting for table view button...")
            table_view_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='btn-show-table']"))
            )
            table_view_button.click()
            logging.info("Table view button clicked successfully.")

            logging.info("Waiting for download button...")
            download_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[4]/div/div[1]/div[4]/button[1]"))
            )
            download_button.click()
            logging.info("Download button clicked successfully.")

            # Wait for the download to complete
            logging.info("Waiting for the download to complete...")
            time.sleep(5)

            # Check if the file exists
            if os.path.isfile(self.csv_file_path):
                logging.info(f"File downloaded successfully: {self.csv_file_path}")
                return True
            else:
                logging.error(f"File not found after download attempt: {self.csv_file_path}")
                return False

        except Exception as e:
            logging.error(f"Error during download: {e}")
            return False

        finally:
            if 'driver' in locals():
                driver.quit()

    def csv_to_json(self):
        """
        Converts a CSV file to a JSON object.
        """
        if not os.path.isfile(self.csv_file_path):
            logging.error(f"File not found: {self.csv_file_path}")
            return None

        data = []
        try:
            with open(self.csv_file_path, 'r') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                for row in csv_reader:
                    data.append(row)

            if not data:
                logging.warning("CSV file is empty or contains no valid rows.")
                return None

            json_data = json.dumps(data, indent=4)
            logging.info("JSON data converted successfully.")
            return json_data

        except Exception as e:
            logging.error(f"Error reading CSV file: {e}")
            return None

    def add_source_loot(self, source_books, campaign_id):
        """
        Add a source book's magic items to the loot table.
        Cleans up the item entries.
        """
        if not os.path.isfile(self.csv_file_path):
            logging.warning("File not found. Recreating loot table...")
            self.get_base_loot_table()

        target_key = "Source"
        keys_to_keep = ["Name", "Type", "Rarity", "Attunement", "Source", "Text"]
        filtered_items = []

        json_data = self.csv_to_json()
        if not json_data:
            logging.error("Failed to convert CSV to JSON. Aborting.")
            return []

        def search(data):
            if isinstance(data, dict):
                if data.get(target_key) in source_books:
                    filtered_item = {k: data.get(k, '') for k in keys_to_keep}
                    filtered_item['campaign_id'] = [campaign_id]
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
                if key != "campaign_id" and isinstance(value, (dict, list)):
                    lowercase_item[key] = json.dumps(value)

            # Check if the item already exists in the database
            existing_item = self.dbm.fetch_data(
                self.table_name,
                columns="campaign_id",
                condition="name = %s AND source = %s",
                params=(lowercase_item["name"], lowercase_item["source"])
            )

            if existing_item:
                # Item exists, update the campaign_id array
                existing_campaign_ids = existing_item[0][0]  # Access the first row and the first column (campaign_id)
                if campaign_id not in existing_campaign_ids:
                    existing_campaign_ids.append(campaign_id)
                    self.dbm.update_data(
                        self.table_name,
                        condition={"name": lowercase_item["name"], "source": lowercase_item["source"]},
                        data={"campaign_id": existing_campaign_ids}
                    )
            else:
                # Item does not exist, insert it as a new entry
                self.dbm.insert_data(self.table_name, lowercase_item)

        logging.info("Loot table generated successfully and added to the database.")
        return filtered_items

    def list_current_sources(self, campaign_id):
        """
        Lists the source books for a campaign.
        """
        columns = "name, source"
        condition = "campaign_id @> %s"
        result = self.dbm.fetch_data(self.table_name, columns=columns, condition=condition, params=([campaign_id],))
        if result:
            logging.info(f"Sources for campaign {campaign_id}: {result}")
        else:
            logging.warning(f"No sources found for campaign {campaign_id}.")
        return result if result else []
