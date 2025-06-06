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
