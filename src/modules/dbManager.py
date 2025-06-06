import json
import psycopg2
import logging
import os

# Configure logging
logging.basicConfig(
    filename=os.getenv("LOG_FILE", "/tmp/logs/attdm.log"),
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DatabaseManager:
    """
    Manages PostgreSQL database connections and CRUD operations.
    """
    def __init__(self, db_params):
        """
        Initializes the DatabaseManager with connection parameters.
        """
        self.db_params = db_params

    def connect(self):
        """
        Establishes a connection to the PostgreSQL database.
        """
        try:
            self.conn = psycopg2.connect(**self.db_params)
            self.cur = self.conn.cursor()
            logging.info("Database connection established successfully.")
            return self.conn, self.cur
        except psycopg2.Error as e:
            logging.error(f"Error connecting to the database: {e}")
            return None, None

    def close(self):
        """
        Closes the database connection.
        """
        if hasattr(self, 'cur') and self.cur:
            self.cur.close()
            logging.info("Database cursor closed.")
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            logging.info("Database connection closed.")

    def create_table(self, table_name, columns):
        """
        Creates a table in the PostgreSQL database.
        """
        try:
            conn, cur = self.connect()
            if not conn:
                return False

            column_definitions = ", ".join(f"{col} {col_type}" for col, col_type in columns.items())
            create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({column_definitions});"

            cur.execute(create_table_query)
            conn.commit()

            logging.info(f"Table '{table_name}' created successfully.")
            return True

        except psycopg2.Error as e:
            logging.error(f"Error creating table '{table_name}': {e}")
            return False
        finally:
            self.close()

    def insert_data(self, table_name, data):
        """
        Inserts data into a PostgreSQL database table.
        """
        try:
            conn, cur = self.connect()
            if not conn:
                return False

            # Convert JSONB columns to JSON strings
            for key, value in data.items():
                if isinstance(value, (dict, list)) and key != "campaign_id":
                    data[key] = json.dumps(value)

            columns = ", ".join(data.keys())
            values = ", ".join(["%s"] * len(data))
            insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({values})"

            cur.execute(insert_query, tuple(data.values()))
            conn.commit()

            logging.info(f"Data inserted successfully into table '{table_name}'.")
            return True

        except psycopg2.Error as e:
            logging.error(f"Error inserting data into table '{table_name}': {e}")
            return False
        finally:
            self.close()

    def fetch_data(self, table_name, columns="*", condition=None, params=None):
        """
        Fetches data from a PostgreSQL database table.
        """
        try:
            conn, cur = self.connect()
            if not conn:
                return None

            query = f"SELECT {columns} FROM {table_name}"
            if condition:
                if isinstance(condition, str):
                    query += f" WHERE {condition}"
                elif isinstance(condition, dict):
                    where_clauses = []
                    values = []
                    for key, value in condition.items():
                        if isinstance(value, list):
                            where_clauses.append(f"{key} @> %s")
                            values.append(value)
                        else:
                            where_clauses.append(f"{key} = %s")
                            values.append(value)
                    where_clause = " AND ".join(where_clauses)
                    query += f" WHERE {where_clause}"
                    params = tuple(values)

            cur.execute(query, params)
            rows = cur.fetchall()

            logging.info(f"Data fetched successfully from table '{table_name}'.")
            return rows

        except psycopg2.Error as e:
            logging.error(f"Error fetching data from table '{table_name}': {e}")
            return None
        finally:
            self.close()

    def update_data(self, table_name, data, condition):
        """
        Updates data in a PostgreSQL database table.
        """
        try:
            conn, cur = self.connect()
            if not conn:
                return False

            set_clause = ", ".join([f"{key} = %s" for key in data.keys()])
            set_values = list(data.values())

            where_clause = " AND ".join([f"{key} = %s" for key in condition.keys()])
            where_values = list(condition.values())

            query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"

            cur.execute(query, set_values + where_values)
            conn.commit()

            logging.info(f"Data updated successfully in table '{table_name}'.")
            return True

        except psycopg2.Error as e:
            logging.error(f"Error updating data in table '{table_name}': {e}")
            return False
        finally:
            self.close()

    def delete_data(self, table_name, condition):
        """
        Deletes data from a PostgreSQL database table.
        """
        try:
            conn, cur = self.connect()
            if not conn:
                return False

            delete_query = f"DELETE FROM {table_name} WHERE {condition}"

            cur.execute(delete_query)
            conn.commit()

            logging.info(f"Data deleted successfully from table '{table_name}' with condition: {condition}.")
            return True

        except psycopg2.Error as e:
            logging.error(f"Error deleting data from table '{table_name}': {e}")
            return False
        finally:
            self.close()

class TableInitializer:
    """
    Initializes the database tables for the application.
    """
    def __init__(self, dbm):
        self.dbm = dbm

    # Create the campaigns table
    def create_campaigns_table(self):
        """
        Creates the campaigns table in the PostgreSQL database.
        """
        table_name = "campaigns"
        columns = {
            "id": "SERIAL PRIMARY KEY",
            "name": "TEXT NOT NULL",
            "dm": "TEXT NOT NULL",
            "loot_books": "JSONB",
        }
        logging.info(f"Creating table '{table_name}'.")
        return self.dbm.create_table(table_name, columns)

    # Create the player_characters table
    def create_player_character_table(self):
        """
        Creates the player_characters table in the PostgreSQL database.
        """
        table_name = "player_characters"
        columns = {
            "campaign_id": "INTEGER[]",
            "character_id": "VARCHAR(50) UNIQUE NOT NULL",
            "name": "TEXT NOT NULL",
            "class_level": "TEXT",
            "passive_perception": "INTEGER",
            "passive_investigation": "INTEGER",
            "passive_insight": "INTEGER",
            "species": "VARCHAR(50)",
            "death_recap": "TEXT",
            "inventory": "JSONB",
            "dm_notes": "JSONB"
        }
        logging.info(f"Creating table '{table_name}'.")
        return self.dbm.create_table(table_name, columns)

    # Create the loot table
    def create_loot_options_table(self):
        """
        Creates the loot_options table in the PostgreSQL database.
        """
        table_name = "loot_options"
        columns = {
            "campaign_id": "INTEGER[]",
            "name": "TEXT NOT NULL",
            "rarity": "TEXT",
            "type": "TEXT",
            "source": "TEXT",
            "attunement": "TEXT",
            "text": "TEXT"
        }
        logging.info(f"Creating table '{table_name}'.")
        return self.dbm.create_table(table_name, columns)

    # Create the NPC table
    def create_npc_table(self):
        """
        Creates the npc table in the PostgreSQL database.
        """
        table_name = "npcs"
        columns = {
            "campaign_id": "INTEGER[]",
            "name": "TEXT UNIQUE NOT NULL",
            "species": "TEXT",
            "location": "JSONB",
            "pc_known_info": "JSONB",
            "dm_notes": "JSONB"
        }
        logging.info(f"Creating table '{table_name}'.")
        return self.dbm.create_table(table_name, columns)

    def create_locations_table(self):
        """
        Creates the locations table in the PostgreSQL database.
        """
        table_name = "locations"
        columns = {
            "campaign_id": "INTEGER[]",
            "name": "TEXT UNIQUE NOT NULL",
            "description": "TEXT",
            "npcs": "JSONB",
            "pc_known_info": "JSONB",
            "dm_notes": "JSONB"
        }
        logging.info(f"Creating table '{table_name}'.")
        return self.dbm.create_table(table_name, columns)