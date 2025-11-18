"""Recreate required table (ArtworkArtist) if missing and rebuild all 10 views.
Run: python fix_views.py
"""
import pymysql

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'softEng@2028',
    'database': 'art_museum_db'
}

VIEW_DEFS = {
    'ArtworkSummary': """
        CREATE OR REPLACE VIEW ArtworkSummary AS
        SELECT o.ObjectID, o.Title, o.ObjectType, o.Medium, o.YearCreated,
               a.ArtistName, g.GalleryName
        FROM ObjectDetails o
        JOIN ArtworkArtist aa ON o.ObjectID = aa.ObjectID
        JOIN Artist a ON aa.ArtistID = a.ArtistID
        JOIN ObjectGalleryData g ON o.GalleryID = g.GalleryID
    """,
    'v_artists_dominant_in_nationality': """
        CREATE OR REPLACE VIEW v_artists_dominant_in_nationality AS
        SELECT a.ArtistID, a.ArtistName, a.Nationality, COUNT(aa.ObjectID) AS TotalWorks
        FROM Artist a
        LEFT JOIN ArtworkArtist aa ON a.ArtistID = aa.ArtistID
        GROUP BY a.ArtistID, a.ArtistName, a.Nationality
        HAVING COUNT(aa.ObjectID) > ALL (
            SELECT COUNT(aa2.ObjectID)
            FROM Artist a2
            LEFT JOIN ArtworkArtist aa2 ON a2.ArtistID = aa2.ArtistID
            WHERE a2.Nationality = a.Nationality AND a2.ArtistID != a.ArtistID
            GROUP BY a2.ArtistID
        )
    """,
    'ArtworkOrigins': """
        CREATE OR REPLACE VIEW ArtworkOrigins AS
        SELECT o.Title, oo.Country, oo.City, g.Department
        FROM ObjectDetails o
        JOIN ObjectOrigins oo ON o.OriginID = oo.OriginID
        JOIN ObjectGalleryData g ON o.GalleryID = g.GalleryID
    """,
    'v_recent_artworks': """
        CREATE OR REPLACE VIEW v_recent_artworks AS
        SELECT o.ObjectID, o.Title, o.YearCreated, g.GalleryName, g.Department
        FROM ObjectDetails o
        JOIN ObjectGalleryData g ON o.GalleryID = g.GalleryID
        WHERE o.YearCreated > 1900
    """,
    'v_artists_zero_or_multiple': """
        CREATE OR REPLACE VIEW v_artists_zero_or_multiple AS
        SELECT a.ArtistID, a.ArtistName, 0 AS TotalWorks
        FROM Artist a
        WHERE a.ArtistID NOT IN (SELECT aa.ArtistID FROM ArtworkArtist aa)
        UNION
        SELECT a.ArtistID, a.ArtistName, COUNT(aa.ObjectID) AS TotalWorks
        FROM Artist a
        JOIN ArtworkArtist aa ON a.ArtistID = aa.ArtistID
        GROUP BY a.ArtistID, a.ArtistName
        HAVING COUNT(aa.ObjectID) > 1
    """,
    'v_full_objects_origins': """
        CREATE OR REPLACE VIEW v_full_objects_origins AS
        SELECT o.ObjectID, o.Title, oo.OriginID, oo.Country, oo.City, oo.Culture
        FROM ObjectDetails o
        LEFT JOIN ObjectOrigins oo ON o.OriginID = oo.OriginID
        UNION
        SELECT o.ObjectID, o.Title, oo.OriginID, oo.Country, oo.City, oo.Culture
        FROM ObjectDetails o
        RIGHT JOIN ObjectOrigins oo ON o.OriginID = oo.OriginID
    """,
    'v_artworks_by_prolific_artists': """
        CREATE OR REPLACE VIEW v_artworks_by_prolific_artists AS
        SELECT DISTINCT o.*
        FROM ObjectDetails o
        WHERE EXISTS (
          SELECT 1
          FROM ArtworkArtist aa_outer
          WHERE aa_outer.ObjectID = o.ObjectID
            AND 1 < (
              SELECT COUNT(*)
              FROM ArtworkArtist aa_inner
              WHERE aa_inner.ArtistID = aa_outer.ArtistID
            )
        )
    """,
    'v_gallery_artwork_counts': """
        CREATE OR REPLACE VIEW v_gallery_artwork_counts AS
        SELECT g.GalleryID, g.GalleryName, g.Department, COUNT(o.ObjectID) AS TotalArtworks
        FROM ObjectGalleryData g
        LEFT JOIN ObjectDetails o ON g.GalleryID = o.GalleryID
        GROUP BY g.GalleryID, g.GalleryName, g.Department
    """,
    'v_artist_artwork_titles': """
        CREATE OR REPLACE VIEW v_artist_artwork_titles AS
        SELECT a.ArtistID, a.ArtistName, o.ObjectID, o.Title AS ArtworkTitle
        FROM Artist a
        LEFT JOIN ArtworkArtist aa ON a.ArtistID = aa.ArtistID
        LEFT JOIN ObjectDetails o ON aa.ObjectID = o.ObjectID
    """,
    'v_multi_artist_artworks': """
        CREATE OR REPLACE VIEW v_multi_artist_artworks AS
        SELECT o.ObjectID, o.Title, COUNT(aa.ArtistID) AS NumArtists
        FROM ObjectDetails o
        JOIN ArtworkArtist aa ON o.ObjectID = aa.ObjectID
        GROUP BY o.ObjectID, o.Title
        HAVING COUNT(aa.ArtistID) > 1
    """
}

def ensure_artwork_artist(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ArtworkArtist (
            ObjectID INT NOT NULL,
            ArtistID INT NOT NULL,
            PRIMARY KEY (ObjectID, ArtistID),
            FOREIGN KEY (ObjectID) REFERENCES ObjectDetails(ObjectID) ON DELETE CASCADE,
            FOREIGN KEY (ArtistID) REFERENCES Artist(ArtistID) ON DELETE CASCADE
        )
    """)
    # Seed basic links if table empty
    cursor.execute("SELECT COUNT(*) FROM ArtworkArtist")
    count = cursor.fetchone()[0]
    if count == 0:
        # Simple 1:1 mapping plus one multi-artist example for testing
        seed = [
            (1,1),(2,2),(3,3),(4,4),(5,5),(6,6), # base mappings
            (4,2)  # make Mona Lisa (ObjectID 4) have second artist to demonstrate multi-artist
        ]
        cursor.executemany("INSERT IGNORE INTO ArtworkArtist (ObjectID, ArtistID) VALUES (%s,%s)", seed)

def main():
    print("Connecting to database...")
    conn = pymysql.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        ensure_artwork_artist(cur)
        # Drop existing views
        for v in VIEW_DEFS.keys():
            cur.execute(f"DROP VIEW IF EXISTS {v}")
        conn.commit()
        print("Dropped existing views (if any).")
        # Create views
        failures = {}
        for name, sql in VIEW_DEFS.items():
            try:
                cur.execute(sql)
                print(f"✓ Created view {name}")
            except Exception as e:
                failures[name] = str(e)
                print(f"✗ Failed view {name}: {e}")
        conn.commit()
        # Summary
        print("\nSummary:")
        if failures:
            for k,v in failures.items():
                print(f"  - {k}: {v}")
        else:
            print("  All views created successfully.")
        # Verify
        cur.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_SCHEMA=%s", (DB_CONFIG['database'],))
        existing = {r[0] for r in cur.fetchall()}
        missing = [v for v in VIEW_DEFS.keys() if v not in existing]
        print(f"\nViews present: {sorted(existing)}")
        if missing:
            print(f"Missing: {missing}")
        else:
            print("All expected views exist.")
    finally:
        cur.close()
        conn.close()
    print("\nDone. Refresh /views.html.")

if __name__ == '__main__':
    main()
