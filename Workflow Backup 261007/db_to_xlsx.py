import sqlite3
import pandas as pd


def db_to_excel(db_file, excel_file):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_file)

    # Get a list of all tables in the database
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    # Create an Excel writer object
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        for table_name in tables:
            name = table_name[0]
            # Read the table into a pandas DataFrame
            df = pd.read_sql_query(f"SELECT * FROM {name}", conn)

            # Write the DataFrame to a sheet
            df.to_excel(writer, sheet_name=name, index=False)
            print(f"Table '{name}' added to {excel_file}")

    conn.close()
    print("Conversion complete!")


# Usage
db_file = 'slab_properties.db'
excel_file = '260617_slab_properties.xlsx'
db_to_excel(db_file, excel_file)