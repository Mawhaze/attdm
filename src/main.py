import os
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
dbm = DatabaseManager(db_params)  # Replace with your DatabaseManager instance
pcm = PCManager(dbm)
lm = LootManager(dbm)
lg = LootGenerator(dbm)
nm = NotesManager(dbm)

# # Validate tables, create if necessary
TableInitializer.create_campaigns_table(dbm)
TableInitializer.create_player_character_table(dbm)
TableInitializer.create_loot_options_table(dbm)
TableInitializer.create_npc_table(dbm)
TableInitializer.create_locations_table(dbm)

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
        return {"message": "Campaign created successfully", "campaign_id": campaign_id}
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
        return {"message": f"Player character {player.character_id} added to campaign {player.campaign_id}"}
    raise HTTPException(status_code=400, detail="Failed to retrieve character data")

@app.get("/players/{campaign_id}/")
def list_campaign_pcs(campaign_id: int):
    players = pcm.list_pc_per_campaign(campaign_id)
    if players:
        return players
    raise HTTPException(status_code=404, detail=f"No players found in campaign {campaign_id}")

@app.put("/players/{campaign_id}/update/")
def update_player_characters(campaign_id: int):
    player_list = pcm.list_pc_per_campaign(campaign_id)
    if not player_list:
        raise HTTPException(status_code=404, detail="No player characters found in this campaign")
    for player in player_list:
        character_id = player[1]
        pcm.update_pc_sheet(character_id)
    return {"message": "Player character sheets updated successfully"}

@app.get("/players/{campaign_id}/passive-stats/")
def list_passive_stats(campaign_id: int):
    player_list = pcm.list_pc_per_campaign(campaign_id)
    if not player_list:
        raise HTTPException(status_code=404, detail="No player characters found in this campaign")
    stats = pcm.list_passive_stats(player_list)
    return stats

@app.post("/players/{campaign_id}/notes/")
def edit_player_notes(pc_name: str, notes: List[str]):
    nm.update_lore_notes(pc_name, "dm_notes", notes, "player_characters")
    return {"message": "Player character notes updated successfully"}

@app.get("/players/{campaign_id}/notes/")
def list_player_notes(campaign_id: int, name: str):
    notes = nm.list_lore_notes(campaign_id, name, "player_characters")
    if not notes:
        raise HTTPException(status_code=404, detail="No notes found for this player character")
    return notes

# NPC Endpoints
@app.post("/npcs/")
def create_npc(npc: NPC, campaign_id: int):
    npc_data = npc.dict()
    npc_data["campaign_id"] = [campaign_id]
    if dbm.insert_data("npcs", npc_data):
        return {"message": f"NPC '{npc.name}' created successfully"}
    raise HTTPException(status_code=400, detail="Failed to create NPC")

@app.get("/npcs/{campaign_id}/")
def list_npcs(campaign_id: int, field: str = "pc_known_info"):
    npc_list = nm.list_lore_notes(campaign_id, field, "npcs")
    if not npc_list:
        raise HTTPException(status_code=404, detail="No NPCs found in this campaign")
    return npc_list

@app.put("/npcs/{npc_name}/notes/")
def edit_npc_notes(npc_name: str, field: str, notes: List[str]):
    nm.update_lore_notes(npc_name, field, notes, "npcs")
    return {"message": f"NPC '{npc_name}' notes updated successfully"}

# Location Endpoints
@app.post("/locations/")
def create_location(location: Location, campaign_id: int):
    location_data = location.dict()
    location_data["campaign_id"] = [campaign_id]
    if dbm.insert_data("locations", location_data):
        return {"message": f"Location '{location.name}' created successfully"}
    raise HTTPException(status_code=400, detail="Failed to create location")

@app.get("/locations/{campaign_id}/")
def list_locations(campaign_id: int, field: str = "pc_known_info"):
    location_list = nm.list_lore_notes(campaign_id, field, "locations")
    if not location_list:
        raise HTTPException(status_code=404, detail="No locations found in this campaign")
    return location_list

@app.put("/locations/{location_name}/notes/")
def edit_location_notes(location_name: str, field: str, notes: List[str]):
    nm.update_lore_notes(location_name, field, notes, "locations")
    return {"message": f"Location '{location_name}' notes updated successfully"}

# Loot Endpoints
@app.post("/loot/{campaign_id}/roll/")
def roll_loot(campaign_id: int, character_name: str):
    loot = lg.roll_loot(character_name, campaign_id)
    if loot:
        item_url = [lg.get_item_link(item) for item in loot]
        return loot, item_url
    raise HTTPException(status_code=400, detail="Failed to roll loot")

@app.get("/loot/{campaign_id}/sources/")
def list_loot_sources(campaign_id: int):
    sources = lm.list_current_sources(campaign_id)
    if not sources:
        raise HTTPException(status_code=404, detail="No loot sources found")
    unique_sources = set(source for _, source in sources)
    return unique_sources

@app.post("/loot/{campaign_id}/sources/")
def add_loot_sources(campaign_id: int, sources: List[str]):
    lm.add_source_loot(sources, campaign_id)
    return {"message": "Loot sources added successfully"}