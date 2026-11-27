import os
import psycopg

# Connect to the Supabase database. The goal is to check for the number of rows in the database
# to make sure everything can be accessed. Then, each goal id completed by a player will correspond
# to increased preference in that goal's category in the database.

# After this, we can run visualization of a player's preference for each category of goal

def main():
    database_url = os.environ.get("DATABASE_URL")

    with psycopg.connect(database_url, connect_timeout=10) as connection:
        with connection.cursor() as cursor:
            cursor.execute("select current_database()")
            print(f"Connected to database: {cursor.fetchone()[0]}")

            cursor.execute("select to_regclass('public.goals')")
            goals_table = cursor.fetchone()[0]

            cursor.execute("select count(*) from public.goals")
            print(f"Rows in public.goals: {cursor.fetchone()[0]}")


if __name__ == "__main__":
    main()