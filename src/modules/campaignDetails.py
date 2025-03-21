import os

from .playerCharacter import PCManager

# from .dbManager import DatabaseManager

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
        return self.dbm.insert_data(self.table_name, data)

    def list_campaigns(self):
        """
        List campaigns from the campaigns table.
        """
        return self.dbm.fetch_data(self.table_name)

    def update_campaign(self, campaign_id, data):
        """
        Updates a campaign in the campaigns table.
        """
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
        # self.campaign_id = campaign_id

    def select_campaign(self):
        """
        Selects a campaign from the database.Setting it as the current campaign for the rest
        of the session.
        """
        self.table_name = "campaigns"
        print("Select a Campaign...")
        campaign_list = CampaignManager.list_campaigns(self)
        if not campaign_list:
            return "No campaigns available"
        
        campaign_output =[]
        for campaign in campaign_list:
            if len(campaign) >= 2:
                campaign_id, campaign_name = campaign[0], campaign[1]
                campaign_output.append(f"ID: {campaign_id} | Name: {campaign_name}")
        
        while True:
            try:
                print("ID: 0 | Name: Create New Campaign")
                print("\n".join(campaign_output))
                campaign_id = int(input("Enter the ID of the campaign you want to select: "))
                # Check if the selected ID exists in the campaign list
                if any(campaign_id == campaign[0] for campaign in campaign_list):
                    print(f"Campaign {campaign_id} selected.")
                    return campaign_id
                elif campaign_id == 0:
                    print("Creating a new campaign...")
                    # Prompt for new campaign details
                    data = {
                        "name": input("Enter the campaign name: "),
                        "dm": input("Enter the DM name: "),
                        "loot_books": [],
                        "data": {}
                    }
                    CampaignManager.create_campaign(self, data)
                    selected_campaign_id = CampaignManager.list_campaigns(self)[-1][0]
                    print(f"New campaign created with ID {selected_campaign_id}.")
                    campaign_id = selected_campaign_id
                    return campaign_id
                else:
                    print("Invalid campaign ID. Please try again.")
            except ValueError:
                print("Please enter a valid number.")
