import json
import os
from dotenv import load_dotenv
from src.modules.campaignDetails import CampaignManager, SessionManager
from src.modules.dbManager import DatabaseManager, TableInitializer
from src.modules.lootGen import LootManager
from src.modules.pdfUtils import PDFProcessor
from src.modules.playerCharacter import PCManager


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    db_params = {
        "host": os.getenv("DB_HOST"),
        "database": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD")
    }
    
    dbm = DatabaseManager(db_params)
    pcm = PCManager(dbm)
    cm = CampaignManager(dbm)
    lm = LootManager(dbm)
    sm = SessionManager(dbm)

    # Select a campaign for the session
    campaign_id = sm.select_campaign()
    sm.session_menu(campaign_id)

    # # Create the tables
    # TableInitializer.create_campaigns_table(dbm)
    # TableInitializer.create_player_character_table(dbm)
    # TableInitializer.create_loot_options_table(dbm)
    
    # # Delete a character
    # pcm.delete_pc(character_id)

    # # Retrieve player inventory
    # player_inventory = pcm.get_pc_inventory(character_id)
    # print(f"Inventory for {character_id}:")
    # for item in player_inventory:
    #     print(item)

    # # Loot table generation
    # # Uncomment to generate loot table for debugging
    # lm.get_base_loot_table()
    # loot_table = lm.csv_to_json()
    # with open("/mnt/c/Documents and Settings/evanc/code/project_ender/attdm/debug/processed_loot.json", "w") as f:
    #     json.dump(loot_table, f, indent=4)
  