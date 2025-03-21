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

    # # Select a campaign for the session
    # campaign_id = sm.select_campaign()

    # def session_menu(self, campaign_id):
    #     """
    #     Displays the session menu for the selected campaign.
    #     """
    #     while True:
    #         self.table_name = "player_characters"
    #         print(f"Player Characters for campaign {campaign_id}:")
    #         player_list = pcm.list_pc_per_campaign(self, campaign_id)
    #         if player_list:
    #             for player in player_list:
    #                 print(player)
    #         else:
    #             print("No player characters found in this campaign.")
            
    #         print("Session Menu:")
    #         print("1. Loot Options")
    #         print("2. Player Characters")
    #         print("3. Session Notes")
    #         print("4. Exit")
        
    #         choice = input("Enter your choice: ")
    #         if  choice == '1':
    #             while True:
    #                 print("Loot Options:")
    #                 print("0. Back")
    #                 print("1. Roll Loot")
    #                 print("2. List Current Loot Sources")
    #                 print("3. Add Loot Source")

    #                 loot_choice = input("Enter your choice: ")
    #                 if loot_choice == '0':
    #                     break
    #                 if loot_choice == '1':
    #                     print("Rolling loot...")
    #                 if loot_choice == '2':
    #                     print("Listing current loot sources...")
    #                 if loot_choice == '3':
    #                     print("Choose a source book to add, separated by commas.")
    #                     print("")
    #         elif choice == '2':
    #             while True:
    #                 print("Player Options:")
    #                 print("0. Back")
    #                 print("1. Add Character")
    #                 print("2. Update Character Sheets")

    #                 pc_choice = input("Enter your choice: ")
    #                 if pc_choice == '0':
    #                     break
    #                 elif pc_choice == '1':
    #                     character_id = input("Enter the character ID: ")
    #                     player_json = pcm.pull_pc_ddbsheet(self, character_id)
    #                     if player_json:
    #                         pcm.add_pc_to_campaign(self, campaign_id, character_id, player_json)
    #                         print(f"{character_id} added to campaign {campaign_id}")
    #                     else:
    #                         print("Failed to retrieve character data.")
    #                 elif pc_choice == '2':
    #                     print("Updating character sheets...")
    #                     for player in player_list:
    #                         character_id = player[1]
    #                         pcm.update_pc(self, character_id)
    #         elif choice == '3':
    #             print(f"Session Notes for campaign {campaign_id}:")
    #             # TODO: Placeholder for session notes functionality
    #             print("to be built")

    #         elif choice == '4':
    #             break
    #         else:
    #             print("Invalid choice. Please try again.")

    # # Create the tables
    # TableInitializer.create_campaigns_table(dbm)
    # TableInitializer.create_player_character_table(dbm)
    # TableInitializer.create_loot_options_table(dbm)
    
    # # Create a campaign
    # campaign_id = cm.create_campaign(data)
    # print(f"Created campaign {campaign_id}")

    # # Delete a character
    # pcm.delete_pc(character_id)

    # # Retrieve player inventory
    # player_inventory = pcm.get_pc_inventory(character_id)
    # print(f"Inventory for {character_id}:")
    # for item in player_inventory:
    #     print(item)

    # Loot table generation
    lm.get_base_loot_table()
    loot_table = lm.csv_to_json()


    with open("/home/mawhaze/code/project_ender/attdm/debug/processed_loot.json", "w") as f:
        json.dump(loot_table, f, indent=4)
  