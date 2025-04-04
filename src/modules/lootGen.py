import csv
import json
import random
import time
import re
import os 

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.modules.playerCharacter import PCManager


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
        Simulates a user clicking a download button on a webpage using Selenium,
        """
        url = "http://localhost:5050/items.html"

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

    def add_source_loot(self, source_books, campaign_id):
        """
        Add a source book's magic items to the loot table.
        Cleans up the item entries.
        """
        if not os.path.isfile(self.csv_file_path):
            print("File not found, or is not a valid file.")
            print("Recreating loot table...")
            self.get_base_loot_table()

        target_key = "Source"
        keys_to_keep = ["Name", "Type", "Rarity", "Attunement", "Source", "Text"]
        filtered_items = []

        json_data = self.csv_to_json()

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

        print("Loot table generated successfully and added to the database.")
        return filtered_items
    
    def list_current_sources(self, campaign_id):
        """
        Lists the source books for a campaign.
        """
        columns = "name, source"
        condition = "campaign_id @> %s"
        result = self.dbm.fetch_data(self.table_name, columns=columns, condition=condition, params=([campaign_id],))
        return result if result else []


class LootGenerator:
    """
    Containes the functions needed for generating loot for a campaign.
    Player loot roll and level will affect rairity of loot generated.
    Validate that the player character can use the loot and does not already have it.
    Provides DNDB item links for player reference.
    """
    def __init__(self, dbm):
        self.dbm = dbm
        self.pcm = PCManager(dbm)
        self.table_name = "loot_options"

    def player_validation(self, name):
        """
        Checks the required data for the player character.
        Takes the character_id and retrieves level and inventory data. 
        """
        # Get the player class and level
        pcl = self.pcm.get_player_class_and_level(name)
        player_class = pcl["classes"]
        player_level = pcl["total_level"]
        # Get the player inventory
        player_inventory = self.pcm.get_pc_stat(name, "inventory") 
        return player_class, player_level, player_inventory

    def roll_loot(self, name, campaign_id):
        """
        Rolls loot for a player character based on their level, class compatibility, and campaign association.
        Determines the rarity of loot based on the player's level range.
        Ensures the item is compatible with the player's class for attunement and belongs to the campaign.
        Returns a list of item names.
        """
        # Load the player character data
        validation_check = self.player_validation(name)
        pl = validation_check[1]  # Player level
        pc = validation_check[0]  # Player class (dictionary of classes and levels)
        pi = validation_check[2]  # Player inventory

        # Determine rarities based on player level
        if 1 <= pl <= 5:
            rarities = ["common", "uncommon"]
            loot_distribution = {"common": 3, "uncommon": 2}
        elif 6 <= pl <= 10:
            rarities = ["uncommon", "rare"]
            loot_distribution = {"uncommon": 3, "rare": 2}
        elif 11 <= pl <= 15:
            rarities = ["rare", "very rare"]
            loot_distribution = {"rare": 3, "very rare": 2}
        elif 16 <= pl <= 20:
            rarities = ["very rare", "legendary"]
            loot_distribution = {"very rare": 3, "legendary": 2}
        else:
            print(f"Invalid player level: {pl}")
            return None

        print(f"Player level: {pl}, Rarities: {rarities}")

        # Fetch loot for each rarity and roll items
        rolled_loot = []
        for rarity, count in loot_distribution.items():
            entries = self.dbm.fetch_data(
                self.table_name,
                columns="name, type, rarity, attunement, source, text, campaign_id",
                condition="rarity = %s AND %s = ANY(campaign_id)",
                params=(rarity, campaign_id)
            )

            if not entries:
                print(f"No entries found with rarity '{rarity}' for campaign ID '{campaign_id}' in table '{self.table_name}'.")
                continue

            # Roll random items for the specified count
            for _ in range(count):
                max_attempts = 50  # Limit the number of reroll attempts to avoid infinite loops
                attempts = 0
                while attempts < max_attempts:
                    random_entry = random.choice(entries)

                    # Check if the item is compatible with the player's class
                    attunement = random_entry[3].lower()
                    if (
                        not attunement  # No attunement required
                        or "requires attunement" in attunement and "by" not in attunement  # General attunement
                        or any(player_class.lower() in attunement for player_class in pc.keys())  # Class-specific attunement
                    ):
                        if random_entry[0] not in pi:
                            rolled_loot.append(random_entry[0])  # Append only the item name
                        break  # Exit the reroll loop if the item is valid
                    else:
                        # print(f"Item '{random_entry[0]}' is not compatible with the player's class. Rerolling...")
                        attempts += 1

                    if attempts == max_attempts:
                        print(f"Failed to find a compatible item for rarity '{rarity}' after {max_attempts} attempts.")

        return rolled_loot
    
    def get_item_link(self, item_name):
        """
        Generates a link to the D&D Beyond page for a specific item.
        """
        # Format item name for the URL
        item_name = re.sub(r"\s*\(.*?\)", "", item_name).strip()
        item_name = item_name.replace(" ", "-").replace("'", "").split(",", 1)[0].lower()

        # Check if the item starts with a "+" followed by a number
        if item_name.startswith("+") and item_name[1].isdigit():
            # Move the "+number" to the end without the "+" sign
            parts = item_name.split("-", 1)
            item_name = f"{parts[1]}-{parts[0][1:]}"

        url = f"https://www.dndbeyond.com/magic-items/{item_name}"
        return url