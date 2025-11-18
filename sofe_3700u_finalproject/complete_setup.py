"""
Complete database setup: Create missing ArtworkArtist table and recreate all views
"""
import pymysql

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'softEng@2028',
    'database': 'art_museum_db'
}

connection = pymysql.connect(**DB_CONFIG)
cursor = connection.cursor()

print("Step 1: Creating ArtworkArtist junction table...")
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ArtworkArtist (
            ObjectID INT,
            ArtistID INT,
            PRIMARY KEY (ObjectID, ArtistID),
            FOREIGN KEY (ObjectID) REFERENCES ObjectDetails(ObjectID) ON DELETE CASCADE,
            FOREIGN KEY (ArtistID) REFERENCES Artist(ArtistID) ON DELETE CASCADE
        )
    """)
    connection.commit()
    print("✓ ArtworkArtist table created")
except Exception as e:
    print(f"✗ Error creating table: {e}")

print("\nStep 2: Inserting sample artwork-artist relationships...")
sample_data = [
    (1, 1),  # Starry Night -> Van Gogh
    (2, 2),  # The Persistence of Memory -> Dalí  
    (3, 3),  # The Two Fridas -> Kahlo
    (4, 4),  # Mona Lisa -> da Vinci
    (5, 5),  # Red Canna -> O'Keeffe
    (6, 6),  # The Great Wave -> Hokusai
]

for obj_id, art_id in sample_data:
    try:
        cursor.execute("INSERT IGNORE INTO ArtworkArtist (ObjectID, ArtistID) VALUES (%s, %s)", (obj_id, art_id))
        connection.commit()
        print(f"✓ Linked artwork {obj_id} to artist {art_id}")
    except Exception as e:
        print(f"✗ Could not link {obj_id}-{art_id}: {e}")

print("\nStep 3: Recreating all SQL views...")
with open('recreate_views.sql', 'r', encoding='utf-8') as f:
    statements = [s.strip() for s in f.read().split(';') if s.strip()]

success = 0
failed = 0

for i, stmt in enumerate(statements, 1):
    try:
        cursor.execute(stmt)
        connection.commit()
        success += 1
        print(f"✓ Statement {i}/{len(statements)}")
    except Exception as e:
        failed += 1
        print(f"✗ Statement {i}: {e}")

cursor.close()
connection.close()

print(f"\n{'='*60}")
print(f"✓ Table creation: Success")
print(f"✓ Views created: {success}/{len(statements)}")
if failed > 0:
    print(f"✗ Failed: {failed}")
print(f"{'='*60}")
print("\n🎉 Database ready! Restart Flask and test /views.html")
