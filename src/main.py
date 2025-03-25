import json
import os
from dotenv import load_dotenv
from src.modules.campaignDetails import CampaignManager, SessionManager
from src.modules.dbManager import DatabaseManager, TableInitializer
from src.modules.lootGen import LootManager
from src.modules.playerCharacter import PCManager
from src.modules.pdfUtils import PDFProcessor


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    db_params = {
        "host": os.getenv("DB_HOST"),
        "database": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD")
    }


    dbm = DatabaseManager(db_params)
    pcm = PCManager(dbm)
    cm = CampaignManager(dbm)
    lm = LootManager(dbm)
    sm = SessionManager(dbm)
    pdfp = PDFProcessor()

    # # PDF to JSON conversion
    # # Uncomment to test new character data
    # # character_id = "mawhaze_140320411"
    # # character_id = "mawhaze_138436365"
    # # character_id = "mawhaze_133064992"
    # pdf_data = pdfp.get_pdf_from_url(character_id)
    # pdf2json = pdfp.convert_pdf_to_json(pdf_data)
    # with open("/mnt/c/Documents and Settings/evanc/code/project_ender/attdm/debug/character.json", "w") as f:
    #     json.dump(pdf2json, f, indent=4)
    # processed_data = pdfp.process_json_document(pdf2json)
    # with open("/mnt/c/Documents and Settings/evanc/code/project_ender/attdm/debug/processed_character.json", "w") as f:
    #     json.dump(processed_data, f, indent=4)

    # # Loot table generation
    # # Uncomment to generate loot table for debugging
    # # test vars for loot table generation, update as needed
    # source_books = "TCE"
    # campaign_id = 1
    
    # lm.get_base_loot_table()
    # loot_table = lm.csv_to_json()
    # filtered_loot = lm.add_source_loot(source_books, campaign_id)
    # with open("/mnt/c/Documents and Settings/evanc/code/project_ender/attdm/debug/processed_loot.json", "w") as f:
    #     json.dump(filtered_loot, f, indent=4)   sm = SessionManager(dbm)

    # # Validate tables, create if necessary
    TableInitializer.create_campaigns_table(dbm)
    TableInitializer.create_player_character_table(dbm)
    TableInitializer.create_loot_options_table(dbm)

    # Select a campaign for the session
    campaign_id = sm.select_campaign()
    sm.session_menu(campaign_id)

    # # Delete a character
    # pcm.delete_pc(character_id)


  