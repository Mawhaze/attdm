import json
import os

from .dbManager import DatabaseManager
from .pdfUtils import PDFProcessor


class PCManager:
    """
    Manages player character operations including campaign association,
    data retrieval, and updates.
        
    Args:
        dbm (DatabaseManager): An instance of the DatabaseManager class.
        campaign_id (int): The ID of the campaign to add the character to.
        character_id (str): The ID of the character to add to the campaign.
        data (dict): A dictionary containing the updated character data.
    """

    def __init__(self, dbm):
        """
        Initializes the PlayerCharacterManager with a database manager.
        """
        self.dbm = dbm
        self.table_name = "player_characters"
        self.pdfp = PDFProcessor()

    def pull_pc_ddbsheet(self, character_id):
        """
        Takes a character ID and retrieves relevant data from a character sheet PDF.
        """
        # Get PDF data from URL
        pdf_data = self.pdfp.get_pdf_from_url(character_id)

        if pdf_data:
            # Convert PDF data to JSON
            json_data = self.pdfp.convert_pdf_to_json(pdf_data)

            if json_data:
                # Process JSON and create PlayerCharacter object
                player_json = self.pdfp.process_json_document(json_data)
                # print(player_json)
                return player_json
            else:
                print("Failed to convert PDF to JSON.")
        else:
            print("Failed to retrieve PDF from URL.")

    def add_pc_to_campaign(self, campaign_id, character_id, player_json):
        """
        Adds a player character to a campaign.
        """
        
        player_json["campaign_id"] = [campaign_id]
        player_json["character_id"] = character_id
        return self.dbm.insert_data(self.table_name, player_json)

    def list_pc_per_campaign(self, campaign_id):
        """
        Lists all player characters in a campaign.
        """
        columns = "name, character_id, class_level"
        condition = "campaign_id @> %s"
        result = self.dbm.fetch_data(self.table_name, columns=columns, condition=condition, params=([campaign_id],))
        return result if result else []

    def delete_pc(self, character_id):
        """
        Deletes a player character from the database.
        """

        condition = f"character_id = '{character_id}'"
        return self.dbm.delete_data(self.table_name, condition=condition)

    def update_pc_sheet(self, character_id):
        """
        Updates a player character's sheet information.
        """
        # Retrieve the updated data for the character
        data = self.pull_pc_ddbsheet(character_id)
        if not data:
            print(f"Failed to retrieve updated data for character ID '{character_id}'.")
            return False

        # Ensure the inventory is properly formatted as JSON
        if 'inventory' in data:
            data['inventory'] = json.dumps(data['inventory'])

        # Define the condition as a dictionary
        condition = {"character_id": character_id}

        # Perform the update
        return self.dbm.update_data(self.table_name, data, condition)

    def get_pc_stat(self, character_id, column):
        """
        Retrieves the inventory of a player character.
        """
        condition = f"character_id = '{character_id}'"
        columns = column
        return self.dbm.fetch_data(self.table_name, columns=columns, condition=condition)
    
    def select_pc(self, player_list):
        """
        Selects a player character from a list of characters in a campaign.
        """
        if not player_list:
            print("No player characters found in this campaign.")
            return None

        while True:
            # Display a numbered list of character names
            for idx, player in enumerate(player_list, start=1):
                name, _, class_level = player
                print(f"{idx}. {name} - {class_level}")

            # Prompt the user to select a character by number
            try:
                selected_idx = int(input("Enter the number of the character: ")) - 1
                if 0 <= selected_idx < len(player_list):
                    # Get the character_id of the selected character
                    selected_player = player_list[selected_idx]
                    print(f"Selected Player: {selected_player}")  # Debugging: Verify selected player
                    return selected_player[1]  # Return the character_id
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")
    
    def get_player_class_and_level(self, character_id):
        """
        Retrieves the class_level of a player character and separates it into player_class and player_level.
        """
         # Fetch the class_level from the database
        result = self.dbm.fetch_data(
            self.table_name,
            columns="class_level",
            condition="character_id = %s",
            params=(character_id,)
        )

        if not result or not result[0][0]:
            print(f"No class_level data found for character ID {character_id}.")
            return None

        class_level = result[0][0].strip()
        print(f"Raw class_level for character ID {character_id}: {repr(class_level)}")

        # Split the class_level into individual class/level pairs
        class_level_parts = class_level.split(" / ")
        class_breakdown = {}
        total_level = 0

        for part in class_level_parts:
            try:
                # Split each part into class and level
                class_name, level = part.rsplit(" ", 1)
                class_name = class_name.strip()
                level = int(level.strip())
                class_breakdown[class_name] = level
                total_level += level
            except ValueError:
                print(f"Invalid format for class/level pair: {repr(part)}. Skipping.")
                continue

        if not class_breakdown:
            print(f"Failed to parse any valid class/level pairs from class_level: {repr(class_level)}.")
            return None

        return {
            "total_level": total_level,
            "classes": class_breakdown
        }
    
    def list_passive_stats(self, player_list):
        """
        Lists player characters sorted by passive stats (perception, investigation, insight).
        """
        # Initialize dictionaries to store stats
        passive_perception = []
        passive_investigation = []
        passive_insight = []

        # Loop through each player and fetch their stats
        for player_name, character_id, _ in player_list:
            try:
                perception = self.get_pc_stat(character_id, "passive_perception")[0][0]
                investigation = self.get_pc_stat(character_id, "passive_investigation")[0][0]
                insight = self.get_pc_stat(character_id, "passive_insight")[0][0]

                # Append stats to respective lists
                passive_perception.append((player_name, perception))
                passive_investigation.append((player_name, investigation))
                passive_insight.append((player_name, insight))
            except Exception as e:
                print(f"Error retrieving stats for {player_name} (ID: {character_id}): {e}")

        # Sort each list by the stat value in descending order
        passive_perception.sort(key=lambda x: x[1], reverse=True)
        passive_investigation.sort(key=lambda x: x[1], reverse=True)
        passive_insight.sort(key=lambda x: x[1], reverse=True)

        # Print the results
        print("\nPassive Perception (Highest to Lowest):")
        for player_name, value in passive_perception:
            print(f"{player_name}: {value}")

        print("\nPassive Investigation (Highest to Lowest):")
        for player_name, value in passive_investigation:
            print(f"{player_name}: {value}")

        print("\nPassive Insight (Highest to Lowest):")
        for player_name, value in passive_insight:
            print(f"{player_name}: {value}")