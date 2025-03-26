import json
from src.modules.playerCharacter import PCManager


class NotesManager:
    """
    Manages basic note functions for player characters.
    """
    def __init__(self, dbm):
        self.dbm = dbm
        self.pcm = PCManager(dbm)
        self.table_name = "player_characters"

    def list_lore_notes(self, campaign_id, lore_field, table_name):
        """
        Lists all player characters, NPCs, or locations in a campaign.
        For player characters, lore_field is the character name.
        """
        if table_name == "npcs":
            columns = ["name", "location", lore_field]
        elif table_name == "locations":
            columns = ["name", "description", "npcs", lore_field]
        elif table_name == "player_characters":
            columns = ["name", "class_level", "dm_notes"]
        else:
            return []

        # Fetch data from the database
        result = self.dbm.fetch_data(table_name, columns=", ".join(columns), condition="campaign_id @> %s", params=([campaign_id],))

        # Convert tuples to dictionaries
        result_as_dicts = [dict(zip(columns, row)) for row in result]

        if table_name == "player_characters":
            return [pc for pc in result_as_dicts if pc["name"] == lore_field] if result_as_dicts else []
        else:
            return result_as_dicts if result_as_dicts else []
    
    def update_lore_notes(self, lore_name, lore_field, notes, table_name):
        """
        Updates notes for an NPC in the database.
        npc_field is either "pc_known_info" or "dm_notes"
        """
        serialized_notes = json.dumps(notes)
        condition = {"name": lore_name}
        data = {lore_field: serialized_notes}
        return self.dbm.update_data(table_name, data, condition)