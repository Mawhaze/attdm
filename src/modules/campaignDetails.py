import os

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
        self.table_name = "campaigns"
        # self.campaign_id = campaign_id

    def select_campaign(self):
        """
        Selects a campaign from the database.Setting it as the current campaign for the rest
        of the session.
        """
        print("Select a Campaign...")
        campaign_list = CampaignManager.list_campaigns(self)
        if not campaign_list:
            return "No campaigns available"
        
        campaign_output =[]
        for campaign in campaign_list:
            if len(campaign) >= 2:
                campaign_id, campaign_name = campaign[0], campaign[1]
                campaign_output.append(f"ID: {campaign_id} | Name: {campaign_name}")

        # return "\n".join(output) if output else "No valid campaign data found"
        print(campaign_output)
