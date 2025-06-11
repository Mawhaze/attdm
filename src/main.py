import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from src.modules.dbManager import DatabaseManager, TableInitializer
from src.modules.lootGen import LootManager, LootGenerator
from src.modules.dmNotes import NotesManager
from src.modules.playerCharacter import PCManager


# Load environment variables
load_dotenv()
db_params = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

# Initialize managers
dbm = DatabaseManager(db_params)
pcm = PCManager(dbm)
lm = LootManager(dbm)
lg = LootGenerator(dbm)
nm = NotesManager(dbm)
ti = TableInitializer(dbm)

# # Validate tables, create if necessary
ti.create_campaigns_table()
ti.create_player_character_table()
ti.create_loot_options_table()
ti.create_npc_table()
ti.create_locations_table()

# Configure Logging
logging.basicConfig(
    filename=os.getenv("LOG_FILE", "/tmp/logs/attdm.log"),
    level=logging.DEBUG,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

app = FastAPI()

# Models for request/response validation
class Campaign(BaseModel):
    name: str
    dm: str
    loot_books: Optional[List[str]] = []

class PlayerCharacter(BaseModel):
    character_id: str
    campaign_id: int

class NPC(BaseModel):
    name: str
    species: str
    location: Optional[List[str]] = []
    pc_known_info: Optional[dict] = None
    dm_notes: Optional[List[str]] = []

class Location(BaseModel):
    name: str
    description: str
    npcs: Optional[List[str]] = []
    pc_known_info: Optional[dict] = None
    dm_notes: Optional[List[str]] = []

# Campaign Endpoints
@app.post("/campaigns/")
def create_campaign(campaign: Campaign):
    data = campaign.dict()
    campaign_id = dbm.insert_data("campaigns", data)
    if campaign_id:
        logging.info(f"Campaign created: {data['name']} with ID {campaign_id}")
        return {"message": "Campaign created successfully", "campaign_id": campaign_id}
    logging.error("Failed to create campaign")
    raise HTTPException(status_code=400, detail="Failed to create campaign")

@app.get("/campaigns/")
def list_campaigns():
    campaigns = dbm.fetch_data("campaigns")
    if campaigns:
        return campaigns
    return {"message": "No campaigns found"}

# Player Character Endpoints
@app.post("/players/")
def add_player_character(player: PlayerCharacter):
    player_json = pcm.pull_pc_ddbsheet(player.character_id)
    if player_json:
        pcm.add_pc_to_campaign(player.campaign_id, player.character_id, player_json)
        logging.info(f"{player.character_id} added to campaign {player.campaign_id}")
        return {"message": f"Player character {player.character_id} added to campaign {player.campaign_id}"}
    logging.error(f"Failed to add {player.character_id} to campaign {player.campaign_id}")
    raise HTTPException(status_code=400, detail="Failed to retrieve character data")

@app.get("/players/{campaign_id}/")
def list_campaign_pcs(campaign_id: int):
    players = pcm.list_pc_per_campaign(campaign_id)
    if players:
        return players
    logging.warning(f"No players found in campaign {campaign_id}")
    raise HTTPException(status_code=404, detail=f"No players found in campaign {campaign_id}")

@app.put("/players/{campaign_id}/update/")
def update_player_characters(campaign_id: int):
    player_list = pcm.list_pc_per_campaign(campaign_id)
    if not player_list:
        logging.warning(f"No player characters found in campaign {campaign_id}")
        raise HTTPException(status_code=404, detail="No player characters found in this campaign")
    for player in player_list:
        character_id = player[1]
        logging.info(f"Updating player: {player}, {character_id}")
        pcm.update_pc_sheet(character_id)
    logging.info(f"Player character sheets updated for campaign {campaign_id}")
    return {"message": "Player character sheets updated successfully"}

@app.delete("/players/{campaign_id}/delete")
def delete_player_character(character_id: str):
    deleted_pc = pcm.delete_pc(character_id)
    if deleted_pc is True:
        logging.info(f"Deleted character: {character_id}")
        return {"message": f"{character_id} successfully deleted."}
    logging.warning(f"Character ID: {character_id} is invalid, please select an active ID.")
    raise HTTPException(status_code=404, detail=f"Character ID {character_id} does not exist to delete")

@app.get("/players/{campaign_id}/passive-stats/")
def list_passive_stats(campaign_id: int):
    player_list = pcm.list_pc_per_campaign(campaign_id)
    if not player_list:
        logging.warning(f"No player characters found in campaign {campaign_id}")
        raise HTTPException(status_code=404, detail="No player characters found in this campaign")
    stats = pcm.list_passive_stats(player_list)
    return stats

@app.post("/players/{campaign_id}/notes/")
def edit_player_notes(pc_name: str, notes: List[str]):
    nm.update_lore_notes(pc_name, "dm_notes", notes, "player_characters")
    logging.info(f"Player character notes updated for {pc_name}")
    return {"message": "Player character notes updated successfully"}

@app.get("/players/{campaign_id}/notes/")
def list_player_notes(campaign_id: int, name: str):
    notes = nm.list_lore_notes(campaign_id, name, "player_characters")
    if not notes:
        logging.warning(f"No notes found for player character {name} in campaign {campaign_id}")
        raise HTTPException(status_code=404, detail="No notes found for this player character")
    return notes

# NPC Endpoints
@app.post("/npcs/")
def create_npc(npc: NPC, campaign_id: int):
    npc_data = npc.dict()
    npc_data["campaign_id"] = [campaign_id]
    if dbm.insert_data("npcs", npc_data):
        logging.info(f"NPC created: {npc.name} in campaign {campaign_id}")
        return {"message": f"NPC '{npc.name}' created successfully"}
    logging.error(f"Failed to create NPC {npc.name} in campaign {campaign_id}")
    raise HTTPException(status_code=400, detail="Failed to create NPC")

@app.get("/npcs/{campaign_id}/")
def list_npcs(campaign_id: int, field: str = "pc_known_info"):
    npc_list = nm.list_lore_notes(campaign_id, field, "npcs")
    if not npc_list:
        logging.warning(f"No NPCs found in campaign {campaign_id}")
        raise HTTPException(status_code=404, detail="No NPCs found in this campaign")
    return npc_list

@app.put("/npcs/{npc_name}/notes/")
def edit_npc_notes(npc_name: str, field: str, notes: List[str]):
    nm.update_lore_notes(npc_name, field, notes, "npcs")
    logging.info(f"NPC notes updated for {npc_name}")
    return {"message": f"NPC '{npc_name}' notes updated successfully"}

# Location Endpoints
@app.post("/locations/")
def create_location(location: Location, campaign_id: int):
    location_data = location.dict()
    location_data["campaign_id"] = [campaign_id]
    if dbm.insert_data("locations", location_data):
        logging.info(f"Location created: {location.name} in campaign {campaign_id}")
        return {"message": f"Location '{location.name}' created successfully"}
    logging.error(f"Failed to create location {location.name} in campaign {campaign_id}")
    raise HTTPException(status_code=400, detail="Failed to create location")

@app.get("/locations/{campaign_id}/")
def list_locations(campaign_id: int, field: str = "pc_known_info"):
    location_list = nm.list_lore_notes(campaign_id, field, "locations")
    if not location_list:
        logging.warning(f"No locations found in campaign {campaign_id}")
        raise HTTPException(status_code=404, detail="No locations found in this campaign")
    return location_list

@app.put("/locations/{location_name}/notes/")
def edit_location_notes(location_name: str, field: str, notes: List[str]):
    nm.update_lore_notes(location_name, field, notes, "locations")
    logging.info(f"Location notes updated for {location_name}")
    return {"message": f"Location '{location_name}' notes updated successfully"}

# Loot Endpoints
@app.post("/loot/{campaign_id}/roll/")
def roll_loot(campaign_id: int, character_name: str):
    loot = lg.roll_loot(character_name, campaign_id)
    if loot:
        item_url = [lg.get_item_link(item) for item in loot]
        logging.info(f"Loot rolled for {character_name} in campaign {campaign_id}: {loot}")
        return loot, item_url
    logging.error(f"Failed to roll loot for {character_name} in campaign {campaign_id}")
    raise HTTPException(status_code=400, detail="Failed to roll loot")

@app.get("/loot/{campaign_id}/sources/")
def list_loot_sources(campaign_id: int):
    sources = lm.list_current_sources(campaign_id)
    if not sources:
        logging.warning(f"No loot sources found for campaign {campaign_id}")
        raise HTTPException(status_code=404, detail="No loot sources found")
    unique_sources = set(source for _, source in sources)
    return unique_sources

@app.post("/loot/{campaign_id}/sources/")
def add_loot_sources(campaign_id: int, sources: List[str]):
    lm.add_source_loot(sources, campaign_id)
    logging.info(f"Loot sources added for campaign {campaign_id}: {sources}")
    return {"message": "Loot sources added successfully"}