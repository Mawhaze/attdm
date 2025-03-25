import json
import psycopg2

class DatabaseManager:
    """
    Manages PostgreSQL database connections and CRUD operations.
    """
    def __init__(self, db_params):
        """
        Initializes the DatabaseManager with connection parameters.

        Args:
            db_params (dict): Dictionary containing database connection parameters.
        """
        self.db_params = db_params

    def connect(self):
        """
        Establishes a connection to the PostgreSQL database.

        Returns:
            psycopg2.connection: A connection object.
        """
        try:
            self.conn = psycopg2.connect(**self.db_params)
            self.cur = self.conn.cursor()
            return self.conn, self.cur
        except psycopg2.Error as e:
            print(f"Error connecting to the database: {e}")
            return None, None

    def close(self):
        """
        Closes the database connection.
        """
        if hasattr(self, 'cur') and self.cur:
            self.cur.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

    def create_table(self, table_name, columns):
        """
        Creates a table in the PostgreSQL database.

        Args:
            table_name (str): Name of the table to create.
            columns (dict): Dictionary defining the table columns.

        Returns:
            bool: True if the table was created successfully, False otherwise.
        """
        try:
            conn, cur = self.connect()
            if not conn:
                return False

            column_definitions = ", ".join(f"{col} {col_type}" for col, col_type in columns.items())
            create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({column_definitions});"

            cur.execute(create_table_query)
            conn.commit()

            print(f"Table '{table_name}' created successfully.")
            return True

        except psycopg2.Error as e:
            print(f"Error creating table '{table_name}': {e}")
            return False
        finally:
            self.close()
    
    def insert_data(self, table_name, data):
        """
        Inserts data into a PostgreSQL database table.
        
        Args:
            table_name (str): Name of the table to insert data into.
            data (dict): Dictionary where keys are column names and values are the data to insert.

        Returns:
            bool: True if the insertion was successful, False otherwise.
        """
        try:
            conn, cur = self.connect()
            if not conn:
                return False

            # Convert JSONB columns to JSON strings
            for key, value in data.items():
                if isinstance(value, (dict, list)) and key != "campaign_id":
                    data[key] = json.dumps(value)  # Convert to JSON string

            columns = ", ".join(data.keys())
            values = ", ".join(["%s"] * len(data))  # Use placeholders for parameterized query
            insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({values})"

            cur.execute(insert_query, tuple(data.values()))

            conn.commit()

            print(f"Data inserted successfully into table '{table_name}'.")
            return True

        except psycopg2.Error as e:
            print(f"Error inserting data: {e}")
            return False
        finally:
            self.close()
    
    def fetch_data(self, table_name, columns="*", condition=None, params=None):
        """
        Fetches data from a PostgreSQL database table.

        Args:
            table_name (str): Name of the table to fetch data from.
            columns (str): Columns to select.
            condition (str or dict, optional): WHERE clause condition (string or dictionary).
            params (tuple, optional): Parameters for the WHERE clause.

        Returns:
            list: List of rows matching the conditions.
        """
        try:
            conn, cur = self.connect()
            if not conn:
                return None

            query = f"SELECT {columns} FROM {table_name}"
            if condition:
                if isinstance(condition, str):
                    # Use the string condition directly
                    query += f" WHERE {condition}"
                elif isinstance(condition, dict):
                    # Process dictionary conditions
                    where_clauses = []
                    values = []
                    for key, value in condition.items():
                        if isinstance(value, list):  # Handle array conditions
                            where_clauses.append(f"{key} @> %s")
                            values.append(value)
                        else:
                            where_clauses.append(f"{key} = %s")
                            values.append(value)
                    where_clause = " AND ".join(where_clauses)
                    query += f" WHERE {where_clause}"
                    params = tuple(values)  # Update params with processed values

            cur.execute(query, params)

            rows = cur.fetchall()
            return rows

        except psycopg2.Error as e:
            print(f"Error fetching data: {e}")
            return None
        finally:
            self.close()

    def update_data(self, table_name, data, condition):
        """
        Updates data in a PostgreSQL database table.

        Args:
            table_name (str): Name of the table to update data in.
            data (dict): Dictionary of columns and their new values.
            condition (dict): Dictionary of conditions for the WHERE clause.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        try:
            conn, cur = self.connect()
            if not conn:
                return False

            # Build the SET clause
            set_clause = ", ".join([f"{key} = %s" for key in data.keys()])
            set_values = list(data.values())

            # Build the WHERE clause
            where_clause = " AND ".join([f"{key} = %s" for key in condition.keys()])
            where_values = list(condition.values())

            # Combine the query
            query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"

            # Execute the query
            cur.execute(query, set_values + where_values)
            conn.commit()

            print(f"Data updated successfully in table '{table_name}'.")
            return True

        except psycopg2.Error as e:
            print(f"Error updating data: {e}")
            return False
        finally:
            self.close()

    def delete_data(self, table_name, condition):
        """
        Deletes data from a PostgreSQL database table.

        Args:
            table_name (str): Name of the table to delete data from.
            condition (str): WHERE clause to identify the rows to delete.

        Returns:
            bool: True if the deletion was successful, False otherwise.
        """
        try:
            conn, cur = self.connect()
            if not conn:
                return False

            delete_query = f"DELETE FROM {table_name} WHERE {condition}"

            cur.execute(delete_query)

            conn.commit()

            print(f"Data '{condition}' successfully from table '{table_name}'.")
            return True

        except psycopg2.Error as e:
            print(f"Error deleting data: {e}")
            return False
        finally:
            self.close()

class TableInitializer:
    """
    Initializes the database tables for the application.

    Args:
        dbm (DatabaseManager): An instance of the DatabaseManager class.
        table_name (str): The name of the table to create.  Defaults to "player_characters".
    """
    def __init__(self, dbm):
        self.dbm = dbm

    # Create the campaigns table
    def create_campaigns_table(dbm):
        """
        Creates the campaigns table in the PostgreSQL database.
        """
        table_name="campaigns"
        columns = {
            "id": "SERIAL PRIMARY KEY",
            "name": "TEXT NOT NULL",
            "dm": "TEXT NOT NULL",
            "loot_books": "JSONB",  
            "data": "JSONB"
        }
        return dbm.create_table(table_name, columns)

    # Create the player_characters table
    def create_player_character_table(dbm):
        """
        Creates the player_characters table in the PostgreSQL database.
        """
        table_name="player_characters"
        columns = {
            "id": "SERIAL PRIMARY KEY",
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
            "dm_notes": "JSONB"        }
        return dbm.create_table(table_name, columns)

        # Create the loot table
    def create_loot_options_table(dbm):
        """
        Creates the loot_options table in the PostgreSQL database.
        """
        table_name="loot_options"
        columns = {
            "id": "SERIAL PRIMARY KEY",
            "campaign_id": "INTEGER[]",
            "name": "TEXT NOT NULL",
            "rarity": "TEXT",
            "type": "TEXT",
            "source": "TEXT",
            "attunement": "TEXT",
            "text": "TEXT"
        }
        return dbm.create_table(table_name, columns)