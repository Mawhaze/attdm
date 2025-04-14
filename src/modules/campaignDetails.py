import logging
import os
from src.modules.playerCharacter import PCManager
from src.modules.lootGen import LootManager, LootGenerator

# Configure logging
logging.basicConfig(
    filename=os.getenv("LOG_FILE", "/tmp/logs/attdm.log"),
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class CampaignManager:
    """
    Manages campaign operations including creation and listing.
    
    Args:
        dbm (DatabaseManager): An instance of the DatabaseManager class.
        campaign_id (int): The ID of the campaign to select.
        data (dict): A dictionary containing the campaign data.
    """
    def __init__(self, dbm):
        """
        Initializes the CampaignManager with a database manager.
        """
        self.dbm = dbm
        self.table_name = "campaigns"

    def create_campaign(self, data):
        """
        Inserts a new campaign into the campaigns table.
        """
        logging.info(f"Creating a new campaign: {data}")
        return self.dbm.insert_data(self.table_name, data)

    def list_campaigns(self):
        """
        List campaigns from the campaigns table.
        """
        logging.info("Fetching list of campaigns.")
        return self.dbm.fetch_data(self.table_name)

    def update_campaign(self, campaign_id, data):
        """
        Updates a campaign in the campaigns table.
        """
        logging.info(f"Updating campaign ID {campaign_id} with data: {data}")
        return self.dbm.update_data(self.table_name, campaign_id, data)

class SessionManager:
    """
    Manages the sessions of a campaign.

    Args:
        dbm (DatabaseManager): An instance of the DatabaseManager class.
        campaign_id (int): The ID of the campaign to select.
    """
    def __init__(self, dbm):
        """
        Initializes the SessionManager with a database manager and campaign ID.
        """
        self.dbm = dbm
        self.lm = LootManager(dbm)
        self.pcm = PCManager(dbm)
        self.lg = LootGenerator(dbm)

    def select_campaign(self):
        """
        Selects a campaign from the database, setting it as the current campaign for the rest
        of the session.
        """
        self.table_name = "campaigns"
        logging.info("Selecting a campaign...")
        campaign_list = CampaignManager.list_campaigns(self)
        
        # If no campaigns exist, create a new one
        if not campaign_list:
            logging.warning("No campaigns available. Creating a new campaign...")
            data = {
                "name": input("Enter the campaign name: "),
                "dm": input("Enter the DM name: "),
                "loot_books": [],
            }
            CampaignManager.create_campaign(self, data)
            selected_campaign_id = CampaignManager.list_campaigns(self)[-1][0]
            logging.info(f"New campaign created with ID {selected_campaign_id}.")
            return selected_campaign_id
        
        campaign_output = []
        for campaign in campaign_list:
            if len(campaign) >= 2:
                campaign_id, campaign_name = campaign[0], campaign[1]
                campaign_output.append(f"ID: {campaign_id} | Name: {campaign_name}")
        
        while True:
            try:
                logging.info("Displaying campaign list for selection.")
                print("ID: 0 | Name: Create New Campaign")
                print("\n".join(campaign_output))
                campaign_id = int(input("Enter the ID of the campaign you want to select: "))
                # Check if the selected ID exists in the campaign list
                if any(campaign_id == campaign[0] for campaign in campaign_list):
                    logging.info(f"Campaign {campaign_id} selected.")
                    return campaign_id
                elif campaign_id == 0:
                    logging.info("Creating a new campaign...")
                    # Prompt for new campaign details
                    data = {
                        "name": input("Enter the campaign name: "),
                        "dm": input("Enter the DM name: "),
                        "loot_books": [],
                        "data": {}
                    }
                    CampaignManager.create_campaign(self, data)
                    selected_campaign_id = CampaignManager.list_campaigns(self)[-1][0]
                    logging.info(f"New campaign created with ID {selected_campaign_id}.")
                    campaign_id = selected_campaign_id
                    return campaign_id
                else:
                    logging.warning("Invalid campaign ID entered.")
                    print("Invalid campaign ID. Please try again.")
            except ValueError:
                logging.error("Invalid input. Expected a number.")
                print("Please enter a valid number.")

    def session_menu(self, campaign_id):
        """
        Displays the session menu for the selected campaign.
        """
        while True:
            self.table_name = "player_characters"
            logging.info(f"Updating character sheets for campaign ID {campaign_id}.")
            player_list = self.pcm.list_pc_per_campaign(campaign_id)
            if player_list:
                for player in player_list:
                    character_id = player[1]
                    self.pcm.update_pc_sheet(character_id)
                for player in player_list:
                    name, _, class_level = player
                    logging.info(f"Current party for campaign {campaign_id}: {name} - {class_level}")
                    print(f"Current party for campaign {campaign_id}")
                    print(f"{name} - {class_level}\n")
            else:
                logging.warning(f"No player characters found in campaign {campaign_id}.")
                print("No player characters found in this campaign.")
            
            print("Session Menu:")
            print("0. Exit")
            print("1. Loot Options")
            print("2. Player Characters")
            print("3. NPC Notes")
            print("4. Location Notes")
        
            choice = input("Enter your choice: ")
            if choice == '0':
                logging.info("Exiting session menu.")
                break
            elif choice == '1':
                self.handle_loot_options(campaign_id, player_list)
            elif choice == '2':
                self.handle_player_characters(campaign_id, player_list)
            elif choice == '3':
                self.handle_npc_notes(campaign_id)
            elif choice == '4':
                self.handle_location_notes(campaign_id)
            else:
                logging.warning(f"Invalid choice entered: {choice}")
                print("Invalid choice. Please try again.")

    def handle_loot_options(self, campaign_id, player_list):
        """
        Handles the loot options menu.
        """
        while True:
            self.table_name = "loot_options"
            print("Loot Options:")
            print("0. Back")
            print("1. Roll Loot")
            print("2. List Current Loot Sources")
            print("3. Add Loot Source")

            loot_choice = input("Enter your choice: ")
            if loot_choice == '0':
                break
            elif loot_choice == '1':
                logging.info("Rolling loot for a player character.")
                print("Select a player character to roll loot for.")
                character_id = self.pcm.select_pc(player_list)
                loot = self.lg.roll_loot(character_id, campaign_id)
                print(loot)
                for item in loot:
                    item_url = self.lg.get_item_link(item)
                    print(f"{item} - {item_url}")
            elif loot_choice == '2':
                logging.info("Listing current loot sources.")
                print("Current loot sources:")
                current_sources = self.lm.list_current_sources(campaign_id)
                unique_sources = set(source for _, source in current_sources)
                for source in unique_sources:
                    print(source)
            elif loot_choice == '3':
                logging.info("Adding new loot sources.")
                print("Choose a source book to add, separated by commas.")
                print("DMG'24, ERLW, PHB'24, TCE, XGE")
                source_books = input("Enter source books: ").split(",")
                self.lm.add_source_loot(source_books, campaign_id)
            else:
                logging.warning(f"Invalid loot choice entered: {loot_choice}")
                print("Invalid choice. Please try again.")