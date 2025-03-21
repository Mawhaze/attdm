import os

from .playerCharacter import PCManager as pcm
from .lootGen import LootManager as lm

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

    def session_menu(self, campaign_id):
        """
        Displays the session menu for the selected campaign.
        """
        while True:
            self.table_name = "player_characters"
            print(f"Player Characters for campaign {campaign_id}:")
            player_list = pcm.list_pc_per_campaign(self, campaign_id)
            if player_list:
                for player in player_list:
                    print(player)
            else:
                print("No player characters found in this campaign.")
            
            print("Session Menu:")
            print("1. Loot Options")
            print("2. Player Characters")
            print("3. Session Notes")
            print("4. Exit")
        
            choice = input("Enter your choice: ")
            if  choice == '1':
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
                    if loot_choice == '1':
                        print("Rolling loot...")
                    if loot_choice == '2':
                        print("Listing current loot sources...")
                    if loot_choice == '3':
                        print("Choose a source book to add, separated by commas.")
                        print("DMG'24, ERLW, PHB'24, TCE, XGE")
                        source_books = input("Enter source books: ").split(",")
                        lm.add_source_loot(self, source_books, campaign_id)

            elif choice == '2':
                while True:
                    self.table_name = "player_characters"
                    print("Player Options:")
                    print("0. Back")
                    print("1. Add Character")
                    print("2. Update Character Sheets")

                    pc_choice = input("Enter your choice: ")
                    if pc_choice == '0':
                        break
                    elif pc_choice == '1':
                        character_id = input("Enter the character ID: ")
                        player_json = pcm.pull_pc_ddbsheet(self, character_id)
                        if player_json:
                            pcm.add_pc_to_campaign(self, campaign_id, character_id, player_json)
                            print(f"{character_id} added to campaign {campaign_id}")
                        else:
                            print("Failed to retrieve character data.")
                    elif pc_choice == '2':
                        print("Updating character sheets...")
                        for player in player_list:
                            character_id = player[1]
                            pcm.update_pc(self, character_id)
            elif choice == '3':
                print(f"Session Notes for campaign {campaign_id}:")
                # TODO: Placeholder for session notes functionality
                print("to be built")

            elif choice == '4':
                break
            else:
                print("Invalid choice. Please try again.")
