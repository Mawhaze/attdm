# Assistant to the Dungeon Master

## Python project to handel some DM activities

> This requires a local postgreSQL container and a 5e.tools container until initial testing is complete.
> After initial testing, app/db/5e.tools/discord_bot will be moved to k8s

### Where i left off

- building a basic CLI to test functionality and trial out during a dnd campaign prior to the api being built.
- need to add loot tables to the campaign and build out pc loot selection function

### Stack

- PostgreSQL for datastore
- Python for data manipulation and FastAPI frontend
- UI will be a discord bot

### Planned Features

- Pull party member info from dndbeyond by character ID
- DB with searchable info on characters/locations/lore/etc.
    1. Quick search for PC passive perception
    2. pull up details on locations and NPCs
    3. Updatable with details as the campaign goes on
- Generate loot for a player
    1. based on parameters from their character sheet
        > class, level, desired equipment types, not currently in inventory
    2. takes into account which books loot is pulled from
    3. loot quality/value dependent on the players roll and level
- potentially add a 'previously on...' recap that pulls a summary from a transcription of the video
    > stich together all the previously on into a lore book/backstory

### Order of Operations

- Select a campaign or create a new one
    > Select a campaign and set it as the current active for campaign_id
    > Create new campaign, set as active campaign_id
- Maintenance actions:
    1. list, add, delete characters in a campaign
        > pull player characters at the start of each session for updates
        > manual option to pull player updates
    2. Create, Edit and Delete loot tables
    3. Create, Edit and Delete NPCs/locations/lore/etc
- In game actions:
    1. Roll loot for a character
        > needs d20 roll input
        > checks character details for loot parameters
        > applies parameters to and generates loot
        > provides multiple output with item_name:description with DM selecting one item
        > pull dndbeyond link for the loot
        > provide hyperlinked item name, X amount gold, random items
    2. Check group passive perception
        > listing name:score in descending order
    3. Info Cheat Sheet
        > Pull up NPC by location, affiliation, etc.
        > NPC connection web
        > Pull up details on a spell/item/etc

## General notes

- Organized by campaign
- dndbeyond can pull up characters based on the number id in the url 
    > https://character-service.dndbeyond.com/character/v5/character/5242429
- csv export from 5e.tool, python hackery to sql, creates links to dndbeyond item based on item name
- Validate books to be used in the campaign upon campaign creation and generate loot table
- provide loot, X  amount of gold and/or gems, custom item upgrade mat/part 
    > player specific loot table + money/upgrade items based on player roll
- On start up, validate table structure exists

### Loot tables function

- Need to set custom loot tables per campaign
- scripts/etc to create the loot entries
  > Need fields for item name, type, rarity, description
- generate loot based on character and loot roll, filters for appropriate loot
- provide DM with 3-5 options for loot and has the dm make a selection
- sends dndbeyond link to character of dm selected loot

### Character functions

- who has the highest passive stat and what
- Add, delete, select characters in a campaign
- update character info at the start of a session

### Lore Database

- Track details about NPCs, world events, locations, etc
- For certain bigger bads/boss fights have a specific loot table to pull in addition to the the campaign table
- 

### Database Structure

- Player Character table
    - Name
    - Passive Stats
    - Inventory
    - Loot preferences
        > armor type, weapon type, offhand type
    - Class
    - Level
    - DndBeyond character IDs
    - Death Recap
    - DM only fields
        > Arc notes, backstory details
- Lore
    -NPC
        - Name
        - Location
        - Factions
        - DM only fields
            > Arc notes, story details, quests
    - Location
        - Name
        - Notable characters
            > pull from the locations field of NPC
        - Methods of travel
            > Inter-area travel, major ports/zone travel
        - DM only fields
            > Location importance, optional story point
    - Faction
        - Name
        - Notable characters
            > pull from the locations field of NPC
        - Description
        - DM only fields
            > story details, etc. 
- Loot
    - Name
    - Type
        > light, med, or heavy armor
        > weapon type
        > Item type
    - Description
    - Rarity
    - Attunement Class
- Campaign
    - Name
    - DM
    - Books to use for loot tables