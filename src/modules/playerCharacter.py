import json
import logging
import os
from src.modules.pdfUtils import PDFProcessor

# Configure logging
logging.basicConfig(
    filename=os.getenv("LOG_FILE", "/tmp/logs/attdm.log"),
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class PCManager:
    """
    Manages player character operations including campaign association,
    data retrieval, and updates.
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
        logging.info(f"Retrieving PDF for character ID: {character_id}")
        pdf_data = self.pdfp.get_pdf_from_url(character_id)

        if pdf_data:
            logging.info(f"PDF retrieved successfully for character ID: {character_id}")
            json_data = self.pdfp.convert_pdf_to_json(pdf_data)

            if json_data:
                logging.info(f"PDF converted to JSON successfully for character ID: {character_id}")
                player_json = self.pdfp.process_json_document(json_data)
                return player_json
            else:
                logging.error(f"Failed to convert PDF to JSON for character ID: {character_id}")
        else:
            logging.error(f"Failed to retrieve PDF from URL for character ID: {character_id}")

    def add_pc_to_campaign(self, campaign_id, character_id, player_json):
        """
        Adds a player character to a campaign.
        """
        logging.info(f"Adding character ID {character_id} to campaign ID {campaign_id}")
        player_json["campaign_id"] = [campaign_id]
        player_json["character_id"] = character_id
        return self.dbm.insert_data(self.table_name, player_json)

    def list_pc_per_campaign(self, campaign_id):
        """
        Lists all player characters in a campaign.
        """
        logging.info(f"Listing player characters for campaign ID {campaign_id}")
        columns = "name, character_id, class_level"
        condition = "campaign_id @> %s"
        result = self.dbm.fetch_data(self.table_name, columns=columns, condition=condition, params=([campaign_id],))
        if result:
            logging.info(f"Found {len(result)} player characters for campaign ID {campaign_id}")
        else:
            logging.warning(f"No player characters found for campaign ID {campaign_id}")
        return result if result else []

    def delete_pc(self, character_id):
        """
        Deletes a player character from the database.
        """
        logging.info(f"Deleting player character with ID: {character_id}")
        condition = f"character_id = '{character_id}'"
        return self.dbm.delete_data(self.table_name, condition=condition)

    def update_pc_sheet(self, character_id):
        """
        Updates a player character's sheet information.
        """
        logging.info(f"Updating sheet for character ID: {character_id}")
        data = self.pull_pc_ddbsheet(character_id)
        if not data:
            logging.error(f"Failed to retrieve updated data for character ID: {character_id}")
            return False

        if 'inventory' in data:
            data['inventory'] = json.dumps(data['inventory'])

        condition = {"character_id": character_id}
        return self.dbm.update_data(self.table_name, data, condition)

    def get_pc_stat(self, character_id, column):
        """
        Retrieves a specific stat of a player character.
        """
        logging.info(f"Retrieving {column} for character ID: {character_id}")
        condition = "character_id = %s"
        columns = column
        return self.dbm.fetch_data(self.table_name, columns=columns, condition=condition, params=(character_id,))

    def select_pc(self, player_list):
        """
        Selects a player character from a list of characters in a campaign.
        """
        if not player_list:
            logging.warning("No player characters found in this campaign.")
            return None

        while True:
            for idx, player in enumerate(player_list, start=1):
                name, _, class_level = player
                logging.info(f"{idx}. {name} - {class_level}")
                print(f"{idx}. {name} - {class_level}")

            try:
                selected_idx = int(input("Enter the number of the character: ")) - 1
                if 0 <= selected_idx < len(player_list):
                    selected_player = player_list[selected_idx]
                    logging.info(f"Selected Player: {selected_player}")
                    return selected_player[1]
                else:
                    logging.warning("Invalid selection. Please try again.")
                    print("Invalid selection. Please try again.")
            except ValueError:
                logging.error("Invalid input. Expected a number.")
                print("Invalid input. Please enter a number.")

    def get_player_class_and_level(self, name):
        """
        Retrieves the class_level of a player character and separates it into player_class and player_level.
        """
        logging.info(f"Retrieving class and level for character: {name}")
        result = self.dbm.fetch_data(
            self.table_name,
            columns="class_level",
            condition="name = %s",
            params=(name,)
        )

        if not result or not result[0][0]:
            logging.warning(f"No class_level data found for character: {name}")
            return None

        class_level = result[0][0].strip()
        logging.info(f"Raw class_level for character {name}: {repr(class_level)}")

        class_level_parts = class_level.split(" / ")
        class_breakdown = {}
        total_level = 0

        for part in class_level_parts:
            try:
                class_name, level = part.rsplit(" ", 1)
                class_name = class_name.strip()
                level = int(level.strip())
                class_breakdown[class_name] = level
                total_level += level
            except ValueError:
                logging.warning(f"Invalid format for class/level pair: {repr(part)}. Skipping.")
                continue

        if not class_breakdown:
            logging.error(f"Failed to parse any valid class/level pairs from class_level: {repr(class_level)}.")
            return None

        return {
            "total_level": total_level,
            "classes": class_breakdown
        }

    def list_passive_stats(self, player_list, stat_name):
        """
        Lists player characters sorted by passive stats (perception, investigation, insight).
        """
        logging.info("Listing passive stats for player characters.")
        valid_stats = {
            "perception": "passive_perception",
            "investigation": "passive_investigation",
            "insight": "passive_insight"
        }
        if stat_name not in valid_stats:
            logging.error(f"Invalid stat section, {stat_name}. Must be one of: {list(valid_stats.keys())}")
            return []
        stat_column = valid_stats[stat_name]
        stat_list = []
        
        for player_name, character_id, _ in player_list:
            try:
                stat_value = self.get_pc_stat(character_id, stat_column)[0][0]
                if stat_value is None:
                    logging.warning(f"{player_name} has no value for {stat_column}")
                stat_list.append((player_name, stat_value))
            except Exception as e:
                logging.error(f"Error retrieving {stat_column} for {player_name} (ID: {character_id}): {e}")

        stat_list.sort(key=lambda x: (x[1] is not None, x[1]), reverse=True)
        logging.info(f"Passive stat {stat_name} listed successfully.")
        return stat_list