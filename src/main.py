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
    # Required data for a creating a test campaign
    # data = {
    #     "name": "Test Campaign",
    #     "dm": "Test DM",
    #     "loot_books": [],
    #     "data": {}
    # }
    dbm = DatabaseManager(db_params)
    pcm = PCManager(dbm)
    cm = CampaignManager(dbm)
    lm = LootManager(dbm)
    sm = SessionManager(dbm)

    # character_id = os.getenv("CHARACTER_ID")
    # campaign_id = os.getenv("CAMPAIGN_ID")
    source_book = "TCE"

    # Select a campaign for the session
    campaign_id = sm.select_campaign()
    sm.session_menu(campaign_id)

    # # Create the tables
    # TableInitializer.create_campaigns_table(dbm)
    # TableInitializer.create_player_character_table(dbm)
    # TableInitializer.create_loot_options_table(dbm)
    
    # # Create a campaign
    # campaign_id = cm.create_campaign(data)
    # print(f"Created campaign {campaign_id}")

    # # Add Character to campaign
    # player_json = pcm.pull_pc_ddbsheet(character_id)
    # if player_json:
    #   pcm.add_pc_to_campaign(campaign_id, character_id, player_json)
    #   print(f"{character_id} added to campaign {campaign_id}")

    # # List characters in a campaign
    # player_list = pcm.list_pc_per_campaign(campaign_id)
    # print(f"List of player characters in campaign {campaign_id}:")
    # for player in player_list:
    #     print(player)

    # # Delete a character
    # pcm.delete_pc(character_id)

    # # Update a characters sheet data
    # pcm.update_pc(character_id)

    # # Retrieve player inventory
    # player_inventory = pcm.get_pc_inventory(character_id)
    # print(f"Inventory for {character_id}:")
    # for item in player_inventory:
    #     print(item)

    # Loot table generation
    # loot_table = lm.add_source_loot(source_book, campaign_id)


    # with open("/home/mawhaze/code/project_ender/attdm/debug/processed_loot.json", "w") as f:
    #     json.dump(loot_table, f, indent=4)
  