-- Drop all existing views to clear any corrupt/stale definitions
DROP VIEW IF EXISTS ArtworkSummary;
DROP VIEW IF EXISTS v_artists_dominant_in_nationality;
DROP VIEW IF EXISTS ArtworkOrigins;
DROP VIEW IF EXISTS v_recent_artworks;
DROP VIEW IF EXISTS v_artists_zero_or_multiple;
DROP VIEW IF EXISTS v_full_objects_origins;
DROP VIEW IF EXISTS v_artworks_by_prolific_artists;
DROP VIEW IF EXISTS v_gallery_artwork_counts;
DROP VIEW IF EXISTS v_artist_artwork_titles;
DROP VIEW IF EXISTS v_multi_artist_artworks;

-- Recreate View 1: Artwork Summary (Title + Artist + Gallery)
CREATE OR REPLACE VIEW ArtworkSummary SQL SECURITY INVOKER AS
SELECT 
    o.ObjectID,
    o.Title,
    o.ObjectType,
    o.Medium,
    o.YearCreated,
    a.ArtistName,
    g.GalleryName
FROM ObjectDetails o
JOIN ArtworkArtist aa ON o.ObjectID = aa.ObjectID
JOIN Artist a ON aa.ArtistID = a.ArtistID
JOIN ObjectGalleryData g ON o.GalleryID = g.GalleryID;

-- Recreate View 2: Artists Whose Artwork Count Is Greater Than ALL Artists from the Same Nationality
CREATE OR REPLACE VIEW v_artists_dominant_in_nationality SQL SECURITY INVOKER AS
SELECT 
    a.ArtistID,
    a.ArtistName,
    a.Nationality,
    COUNT(aa.ObjectID) AS TotalWorks
FROM Artist a
LEFT JOIN ArtworkArtist aa ON a.ArtistID = aa.ArtistID
GROUP BY a.ArtistID, a.ArtistName, a.Nationality
HAVING COUNT(aa.ObjectID) > ALL (
    SELECT COUNT(aa2.ObjectID)
    FROM Artist a2
    LEFT JOIN ArtworkArtist aa2 ON a2.ArtistID = aa2.ArtistID
    WHERE a2.Nationality = a.Nationality
      AND a2.ArtistID != a.ArtistID
    GROUP BY a2.ArtistID
);

-- Recreate View 3: Artwork Origin + Department
CREATE OR REPLACE VIEW ArtworkOrigins SQL SECURITY INVOKER AS
SELECT 
    o.Title,
    oo.Country,
    oo.City,
    g.Department
FROM ObjectDetails o
JOIN ObjectOrigins oo ON o.OriginID = oo.OriginID
JOIN ObjectGalleryData g ON o.GalleryID = g.GalleryID;

-- Recreate View 4: Artworks created after 1900 + Department
CREATE OR REPLACE VIEW v_recent_artworks SQL SECURITY INVOKER AS
SELECT 
  o.ObjectID, o.Title, o.YearCreated,
  g.GalleryName, g.Department
FROM ObjectDetails o
JOIN ObjectGalleryData g ON o.GalleryID = g.GalleryID
WHERE o.YearCreated > 1900;

-- Recreate View 5: All Artists Who Either (1) Have No Artworks OR (2) Have More Than 1 Artwork
CREATE OR REPLACE VIEW v_artists_zero_or_multiple SQL SECURITY INVOKER AS
SELECT a.ArtistID, a.ArtistName, 0 AS TotalWorks
FROM Artist a
WHERE a.ArtistID NOT IN (
    SELECT aa.ArtistID FROM ArtworkArtist aa
)
UNION
SELECT a.ArtistID, a.ArtistName, COUNT(aa.ObjectID) AS TotalWorks
FROM Artist a
JOIN ArtworkArtist aa ON a.ArtistID = aa.ArtistID
GROUP BY a.ArtistID, a.ArtistName
HAVING COUNT(aa.ObjectID) > 1;

-- Recreate View 6: Artworks matched to Origin and those without Origin, Origins without Artwork
CREATE OR REPLACE VIEW v_full_objects_origins SQL SECURITY INVOKER AS
SELECT o.ObjectID, o.Title, oo.OriginID, oo.Country, oo.City, oo.Culture
FROM ObjectDetails o
LEFT JOIN ObjectOrigins oo ON o.OriginID = oo.OriginID
UNION
SELECT o.ObjectID, o.Title, oo.OriginID, oo.Country, oo.City, oo.Culture
FROM ObjectDetails o
RIGHT JOIN ObjectOrigins oo ON o.OriginID = oo.OriginID;

-- Recreate View 7: Artworks of Artists with (>1) works in Database (Correlated Nested Query)
CREATE OR REPLACE VIEW v_artworks_by_prolific_artists SQL SECURITY INVOKER AS
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
);

-- Recreate View 8: Gallery Artwork Counts (How many artworks per gallery)
CREATE OR REPLACE VIEW v_gallery_artwork_counts SQL SECURITY INVOKER AS
SELECT 
    g.GalleryID,
    g.GalleryName,
    g.Department,
    COUNT(o.ObjectID) AS TotalArtworks
FROM ObjectGalleryData g
LEFT JOIN ObjectDetails o ON g.GalleryID = o.GalleryID
GROUP BY g.GalleryID, g.GalleryName, g.Department;

-- Recreate View 9: Artists With Their Artwork Titles (Flattened list)
CREATE OR REPLACE VIEW v_artist_artwork_titles SQL SECURITY INVOKER AS
SELECT 
    a.ArtistID,
    a.ArtistName,
    o.ObjectID,
    o.Title AS ArtworkTitle
FROM Artist a
LEFT JOIN ArtworkArtist aa ON a.ArtistID = aa.ArtistID
LEFT JOIN ObjectDetails o ON aa.ObjectID = o.ObjectID;

-- Recreate View 10: Artworks With Multiple Artists (Collaboration detection)
CREATE OR REPLACE VIEW v_multi_artist_artworks SQL SECURITY INVOKER AS
SELECT 
    o.ObjectID,
    o.Title,
    COUNT(aa.ArtistID) AS NumArtists
FROM ObjectDetails o
JOIN ArtworkArtist aa ON o.ObjectID = aa.ObjectID
GROUP BY o.ObjectID, o.Title
HAVING COUNT(aa.ArtistID) > 1;
