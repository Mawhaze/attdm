import os

from .dmNotes import PlayerNotes, LoreNotes
from .playerCharacter import PCManager
from .lootGen import LootManager, LootGenerator

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
        self.lm = LootManager(dbm)
        self.pcm = PCManager(dbm)
        self.lg = LootGenerator(dbm)
        self.pcnt = PlayerNotes(dbm)
        self.ln = LoreNotes(dbm)

    def select_campaign(self):
        """
        Selects a campaign from the database.Setting it as the current campaign for the rest
        of the session.
        """
        self.table_name = "campaigns"
        print("Select a Campaign...")
        campaign_list = CampaignManager.list_campaigns(self)
        
        # If no campaigns exist, create a new one
        if not campaign_list:
            print("No campaigns available. Creating a new campaign...")
            data = {
                "name": input("Enter the campaign name: "),
                "dm": input("Enter the DM name: "),
                "loot_books": [],
            }
            CampaignManager.create_campaign(self, data)
            selected_campaign_id = CampaignManager.list_campaigns(self)[-1][0]
            print(f"New campaign created with ID {selected_campaign_id}.")
            return selected_campaign_id
        
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
            print("Updating character sheets...")
            player_list = self.pcm.list_pc_per_campaign(campaign_id)
            if player_list:
                for player in player_list:
                    character_id = player[1]
                    self.pcm.update_pc_sheet(character_id)
                for player in player_list:
                    name, _, class_level = player
                    print(f"Current part for campaign {campaign_id}")
                    print(f"{name} - {class_level}\n")
            else:
                print("No player characters found in this campaign.")
            
            print("Session Menu:")
            print("0. Exit")
            print("1. Loot Options")
            print("2. Player Characters")
            print("3. NPC Notes")
            print("4. Location Notes")
        
            choice = input("Enter your choice: ")
            if choice == '0':
                break
            elif  choice == '1':
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
                        print("Select a player character to roll loot for.")
                        character_id = self.pcm.select_pc(player_list)
                        loot = self.lg.roll_loot(character_id, campaign_id)
                        print(loot)
                        for item in loot:
                            item_url = self.lg.get_item_link(item)
                            print(f"{item} - {item_url}")
                    if loot_choice == '2':
                        print("Current loot sources:")
                        current_sources = self.lm.list_current_sources(campaign_id)
                        unique_sources = set(source for _, source in current_sources)
                        for source in unique_sources:
                            print(source)
                    if loot_choice == '3':
                        print("Choose a source book to add, separated by commas.")
                        print("DMG'24, ERLW, PHB'24, TCE, XGE")
                        source_books = input("Enter source books: ").split(",")
                        self.lm.add_source_loot(source_books, campaign_id)

            elif choice == '2':
                while True:
                    self.table_name = "player_characters"
                    print("Player Options:")
                    print("0. Back")
                    print("1. Add Character")
                    print("2. Update Character Sheets")
                    print("3. List Passive Stats")
                    print("4. Add Character Notes")

                    pc_choice = input("Enter your choice: ")
                    if pc_choice == '0':
                        break
                    elif pc_choice == '1':
                        character_id = input("Enter the character ID: ")
                        player_json = self.pcm.pull_pc_ddbsheet(character_id)
                        if player_json:
                            self.pcm.add_pc_to_campaign(campaign_id, character_id, player_json)
                            print(f"{character_id} added to campaign {campaign_id}")
                        else:
                            print("Failed to retrieve character data.")
                    elif pc_choice == '2':
                        print("Updating character sheets...")
                        for player in player_list:
                            character_id = player[1]
                            self.pcm.update_pc_sheet(character_id)
                    elif pc_choice == '3':
                        print("Listing passive stats for all players in the campaign...")
                        self.pcm.list_passive_stats(player_list)
                    elif pc_choice == '4':
                        print("Select a player character to manage notes for.")
                        self.pcnt.player_notes_menu(player_list)
            elif choice == '3':
                while True:
                    self.table_name = "npcs"
                    print("\nOptions:")
                    print("0. Back to Session Menu")
                    print("1. Add a new NPC")
                    print("2. List existing NPC, public notes")
                    print("3. List existing NPC, DM notes")
                    print("4. Edit NPC public notes")
                    print("5. Edit NPC DM notes")
                    note_choice = input("Enter your choice: ")

                    if note_choice == '0':
                        break    
                    elif note_choice == '1':
                        self.ln.create_new_npc(campaign_id, self.table_name)
                    elif note_choice == '2':
                        lore_field = "pc_known_info"
                        npc_list = self.ln.list_lore_notes(campaign_id, lore_field, self.table_name)
                        if npc_list:
                            for npc in npc_list:
                                name, location, pc_known_info = npc
                                print(f"{name} - {location}\n{pc_known_info}")
                        else:
                            print("No NPCs found in this campaign.")
                    elif note_choice == '3':
                        lore_field = "dm_notes"
                        npc_list = self.ln.list_lore_notes(campaign_id, lore_field, self.table_name)
                        if npc_list:
                            for npc in npc_list:
                                name, location, dm_notes = npc
                                print(f"{name} - {location}\nDM notes: {dm_notes}")
                        else:
                            print("No NPCs found in this campaign.")
                    elif note_choice == '4':
                        lore_name = input("Enter the NPC's name: ")
                        lore_field = "pc_known_info"
                        self.ln.edit_lore_notes(lore_name, lore_field, self.table_name)
                    elif note_choice == '5':
                        lore_name = input("Enter the NPC's name: ")
                        lore_field = "dm_notes"
                        self.ln.edit_lore_notes(lore_name, lore_field, self.table_name)
                    else:
                        print("Invalid choice. Please try again.")
            elif choice == '4':
                while True:
                    self.table_name = "locations"
                    print("\nOptions:")
                    print("0. Back to Session Menu")
                    print("1. Add a new Location")
                    print("2. List existing Locations, public notes")
                    print("3. List existing Locations, DM notes")
                    print("4. Edit Location public notes")
                    print("5. Edit Location DM notes")
                    note_choice = input("Enter your choice: ")

                    if note_choice == '0':
                        break    
                    elif note_choice == '1':
                        self.ln.create_new_location(campaign_id, self.table_name)
                    elif note_choice == '2':
                        lore_field = "pc_known_info"
                        location_list = self.ln.list_lore_notes(campaign_id, lore_field, self.table_name)
                        if location_list:
                            for location in location_list:
                                name, description, npcs, pc_known_info = location
                                print(f"{name}\n{description}\n{npcs}\n{pc_known_info}")
                        else:
                            print("No Locations found in this campaign.")
                    elif note_choice == '3':
                        lore_field = "dm_notes"
                        location_list = self.ln.list_lore_notes(campaign_id, lore_field, self.table_name)
                        if location_list:
                            for location in location_list:
                                name, description, npcs, dm_notes = location
                                print(f"{name}\n{description}\n{npcs}\nDM notes:{dm_notes}")
                        else:
                            print("No Locations found in this campaign.")
                    elif note_choice == '4':
                        lore_name = input("Enter the Location's name: ")
                        lore_field = "pc_known_info"
                        self.ln.edit_lore_notes(lore_name, lore_field, self.table_name)
                    elif note_choice == '5':
                        lore_name = input("Enter the Location's name: ")
                        lore_field = "dm_notes"
                        self.ln.edit_lore_notes(lore_name, lore_field, self.table_name)
                    else:
                        print("Invalid choice. Please try again.")