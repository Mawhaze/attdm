# # PDF to JSON conversion
# # Uncomment to test new character data
# # character_id = "mawhaze_140320411"
# # character_id = "mawhaze_138436365"
# # character_id = "mawhaze_133064992"
# pdfp = PDFProcessor()
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
# lm = LootManager(dbm)
# lm.get_base_loot_table()
# loot_table = lm.csv_to_json()
# filtered_loot = lm.add_source_loot(source_books, campaign_id)
# with open("/mnt/c/Documents and Settings/evanc/code/project_ender/attdm/debug/processed_loot.json", "w") as f:
#     json.dump(filtered_loot, f, indent=4)   sm = SessionManager(dbm)