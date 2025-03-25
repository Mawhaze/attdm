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
                print(player_json)

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

    def update_pc(self, character_id):
        """
        Updates a player characters sheet information
        """

        condition = "character_id = %s"
        params = (character_id,)
        data = PCManager.pull_pc_ddbsheet(self, character_id)
        if data and 'inventory' in data:
            data['inventory'] = json.dumps(data['inventory'])

        return self.dbm.update_data(self.table_name, data, condition=condition, params=params)

    def get_pc_stat(self, character_id, column):
        """
        Retrieves the inventory of a player character.
        """

        condition = f"character_id = '{character_id}'"
        columns = column
        return self.dbm.fetch_data(self.table_name, columns=columns, condition=condition)
    
    def get_player_class_and_level(self, character_id):
        """
        Retrieves the class_level of a player character and separates it into player_class and player_level.

        Args:
            character_id (str): The ID of the character.

        Returns:
            dict: A dictionary containing the total level and a breakdown of classes and levels.
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
        # print(f"Raw class_level for character ID {character_id}: {repr(class_level)}")

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