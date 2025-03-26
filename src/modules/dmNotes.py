import json
from prompt_toolkit import prompt
from .playerCharacter import PCManager


class NotesManager:
    """
    Manages basic note functions for player characters.
    """
    def __init__(self, dbm):
        self.dbm = dbm
        self.pcm = PCManager(dbm)
        self.table_name = "player_characters"

    def add_new_note(self, notes):
        """
        Adds a new note to the player character's notes.
        """
        new_note = prompt("Enter the new note: ")
        notes.append(new_note)
        print("Note added.")
        return True  # Indicates that changes were made

    def edit_existing_note(self, notes):
        """
        Edits an existing note in the player character's notes.
        """
        if not notes:
            print("No notes to edit.")
            return False

        try:
            note_idx = int(input("Enter the number of the note to edit: ")) - 1
            if 0 <= note_idx < len(notes):
                print(f"Current note: {notes[note_idx]}")
                updated_note = prompt("Enter the updated note: ", default=notes[note_idx])
                notes[note_idx] = updated_note
                print("Note updated.")
                return True  # Indicates that changes were made
            else:
                print("Invalid note number.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")
        return False

    def delete_note(self, notes):
        """
        Deletes a note from the player character's notes.
        """
        if not notes:
            print("No notes to delete.")
            return False

        try:
            note_idx = int(input("Enter the number of the note to delete: ")) - 1
            if 0 <= note_idx < len(notes):
                deleted_note = notes.pop(note_idx)
                print(f"Deleted note: {deleted_note}")
                return True  # Indicates that changes were made
            else:
                print("Invalid note number.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")
        return False


class PlayerNotes:
    """
    Manages notes for player characters.
    """
    def __init__(self, dbm):
        self.dbm = dbm
        self.pcm = PCManager(dbm)
        self.notes_manager = NotesManager(dbm)
        self.table_name = "player_characters"

    def player_notes_menu(self, player_list):
        """
        Displays the player notes menu.
        """
        print("Select a player character to manage notes for.")
        character_id = self.pcm.select_pc(player_list)
        current_notes = self.pcm.get_pc_stat(character_id, "dm_notes")

        # Ensure current_notes is a list
        if current_notes and isinstance(current_notes, list):
            notes = current_notes[0][0] if current_notes[0][0] is not None else []
        elif isinstance(current_notes, str):
            try:
                notes = json.loads(current_notes)  # Parse JSON string if stored as such
            except json.JSONDecodeError:
                notes = []
        else:
            notes = []

        # Ensure notes is a list
        if not isinstance(notes, list):
            notes = []

        # Track whether changes were made
        notes_changed = False

        while True:
            print("\nCurrent Notes:")
            if notes:
                for idx, note in enumerate(notes, start=1):
                    print(f"{idx}. {note}")
            else:
                print("No notes available.")

            print("\nOptions:")
            print("0. Back to Player Options")
            print("1. Add a new note")
            print("2. Edit an existing note")
            print("3. Delete a note")
            note_choice = input("Enter your choice: ")

            if note_choice == '0':
                # Exit without saving if no changes were made
                if not notes_changed:
                    print("No changes made. Exiting without saving.")
                    break
                else:
                    # Save and exit
                    print("Saving notes...")
                    self.update_pc_notes(character_id, notes)
                    print(f"Notes updated for {character_id}.")
                    break

            elif note_choice == '1':
                # Add a new note
                notes_changed |= self.notes_manager.add_new_note(notes)

            elif note_choice == '2':
                # Edit an existing note
                notes_changed |= self.notes_manager.edit_existing_note(notes)

            elif note_choice == '3':
                # Delete a note
                notes_changed |= self.notes_manager.delete_note(notes)

            else:
                print("Invalid choice. Please try again.")

    def update_pc_notes(self, character_id, notes):
        """
        Updates a player character's DM notes in the database.
        """
        serialized_notes = json.dumps(notes)
        condition = {"character_id": character_id}
        data = {"dm_notes": serialized_notes}
        return self.dbm.update_data(self.table_name, data, condition)

class LoreNotes:
    """
    Manages notes for NPCs in the campaign.
    """
    def __init__(self, dbm):
        """
        Initializes the NPCNotes class.
        """
        self.dbm = dbm
        self.notes_manager = NotesManager(dbm)

    def create_new_npc(self, campaign_id, table_name):
        """
        Creates a new NPC in the campaign.
        """
        print("\nCreating a New NPC")

        # Prompt the user for NPC details
        name = input("Enter the NPC's name: ").strip()
        if not name:
            print("NPC name cannot be empty.")
            return

        species = input("Enter the NPC's species (e.g., Human, Elf): ").strip()
        
        # Prompt for location (comma-separated list)
        location_input = input("Enter the NPC's locations (comma-separated, e.g., Market Square, Town Hall): ").strip()
        if location_input:
            # Split the input into a list of locations
            location = [loc.strip() for loc in location_input.split(",")]
        else:
            location = []

        # Prompt for PC-known information (optional)
        pc_known_info = input("Enter any PC-known information (leave blank if none): ").strip()
        if pc_known_info:
            try:
                pc_known_info = json.loads(pc_known_info)  # Parse as JSON if provided
            except json.JSONDecodeError:
                print("Invalid JSON format for PC-known information. Storing as plain text.")
                pc_known_info = {"info": pc_known_info}  # Wrap in a dictionary

        # Prompt for DM notes (optional)
        dm_notes = input("Enter any DM notes (leave blank if none): ").strip()
        if dm_notes:
            dm_notes = [dm_notes]  # Store as a list for consistency
        else:
            dm_notes = []

        # Prepare the NPC data for insertion
        npc_data = {
            "campaign_id": [campaign_id],  # Store campaign_id as an array
            "name": name,
            "species": species,
            "location": location if location else None,
            "pc_known_info": pc_known_info if pc_known_info else None,
            "dm_notes": dm_notes
        }

        # Insert the NPC into the database
        if self.dbm.insert_data(table_name, npc_data):
            print(f"NPC '{name}' successfully created and added to the campaign.")
        else:
            print(f"Failed to create NPC '{name}'.")

    def create_new_location(self, campaign_id, table_name):
        """
        Creates a new location in the campaign.
        """
        print("\nCreating a New Location")

        # Prompt the user for location details
        name = input("Enter the location's name: ").strip()
        if not name:
            print("Location name cannot be empty.")
            return

        description = input("Enter a description for the location: ").strip()

        # Prompt for NPCs (comma-separated list)
        npcs_input = input("Enter the NPCs associated with this location (comma-separated, leave blank if none): ").strip()
        if npcs_input:
            npcs = [npc.strip() for npc in npcs_input.split(",")]
        else:
            npcs = []

        # Prompt for PC-known information (optional)
        pc_known_info = input("Enter any PC-known information (as JSON or plain text, leave blank if none): ").strip()
        if pc_known_info:
            try:
                pc_known_info = json.loads(pc_known_info)  # Parse as JSON if provided
            except json.JSONDecodeError:
                print("Invalid JSON format for PC-known information. Storing as plain text.")
                pc_known_info = {"info": pc_known_info}  # Wrap in a dictionary

        # Prompt for DM notes (optional)
        dm_notes = input("Enter any DM notes (leave blank if none): ").strip()
        if dm_notes:
            dm_notes = [dm_notes]  # Store as a list for consistency
        else:
            dm_notes = []

        # Prepare the location data for insertion
        location_data = {
            "campaign_id": [campaign_id],  # Store campaign_id as an array
            "name": name,
            "description": description,
            "npcs": npcs if npcs else None,
            "pc_known_info": pc_known_info if pc_known_info else None,
            "dm_notes": dm_notes
        }

        # Insert the location into the database
        if self.dbm.insert_data(table_name, location_data):
            print(f"Location '{name}' successfully created and added to the campaign.")
        else:
            print(f"Failed to create location '{name}'.")
    
    def list_lore_notes(self, campaign_id, lore_field, table_name):
        """
        Lists all player characters in a campaign.
        """
        if table_name == "npcs":
            columns = f"name, location, {lore_field}"
        elif table_name == "locations":
            columns = f"name, description, npcs, {lore_field}"
        condition = "campaign_id @> %s"
        result = self.dbm.fetch_data(table_name, columns=columns, condition=condition, params=([campaign_id],))
        return result if result else []
    
    def edit_lore_notes(self, lore_name, lore_field, table_name):
        """
        Edits notes for an NPC in the campaign. 
        npc_field is either "pc_known_info" or "dm_notes"
        """
        columns = lore_field
        condition = f"name = '{lore_name}'"
        lore_data = self.dbm.fetch_data(table_name, columns=columns, condition=condition)
        if not lore_data:
            print(f"'{lore_name}' not found.")
            return

        # Ensure the notes are stored as a list
        notes = lore_data[0][0] if lore_data[0][0] is not None else []
        # Track whether changes were made
        notes_changed = False

        while True:
            print("\nCurrent Notes:")
            if notes:
                for idx, note in enumerate(notes, start=1):
                    print(f"{idx}. {note}")
            else:
                print("No notes available.")

            print("\nOptions:")
            print("0. Back to Notes Menu")
            print("1. Add a new note")
            print("2. Edit an existing note")
            print("3. Delete a note")
            note_choice = input("Enter your choice: ")

            if note_choice == '0':
                # Exit without saving if no changes were made
                if not notes_changed:
                    print("No changes made")
                    break
                else:
                    # Save and exit
                    print("Saving notes...")
                    self.update_lore_notes(lore_name, lore_field, notes, table_name)
                    print(f"Notes updated for {lore_name}.")
                    break
            elif note_choice == '1':
                notes_changed |= self.notes_manager.add_new_note(notes)
            elif note_choice == '2':
                notes_changed |= self.notes_manager.edit_existing_note(notes)
            elif note_choice == '3':
                notes_changed |= self.notes_manager.delete_note(notes)
            else:
                print("Invalid choice. Please try again.")

    def update_lore_notes(self, lore_name, lore_field, notes, table_name):
        """
        Updates notes for an NPC in the database.
        npc_field is either "pc_known_info" or "dm_notes"
        """
        serialized_notes = json.dumps(notes)
        condition = {"name": lore_name}
        data = {lore_field: serialized_notes}
        return self.dbm.update_data(table_name, data, condition)