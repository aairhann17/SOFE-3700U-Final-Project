SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS ArtworkArtist;
DROP TABLE IF EXISTS ObjectGalleryData;
DROP TABLE IF EXISTS ObjectOrigins;
DROP TABLE IF EXISTS ObjectDetails;
DROP TABLE IF EXISTS Artist;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE Artist (
    ArtistID INT AUTO_INCREMENT PRIMARY KEY,
    ArtistName VARCHAR(255),
    Nationality VARCHAR(100),
    BirthYear INT,
    DeathYear INT,
    ArtistBio VARCHAR(500)
);

CREATE TABLE ObjectOrigins (
    OriginID INT AUTO_INCREMENT PRIMARY KEY,
    Country VARCHAR(100),
    City VARCHAR(100),
    Culture VARCHAR(100)
);

CREATE TABLE ObjectGalleryData (
    GalleryID INT AUTO_INCREMENT PRIMARY KEY,
    GalleryName VARCHAR(150),
    GalleryNumber INT,
    Department VARCHAR(150)
);

CREATE TABLE ObjectDetails (
    ObjectID INT AUTO_INCREMENT PRIMARY KEY,
    Title VARCHAR(255),
    ObjectType VARCHAR(100),
    Medium VARCHAR(100),
    YearCreated INT,
    OriginID INT,
    GalleryID INT,
    FOREIGN KEY (OriginID) REFERENCES ObjectOrigins(OriginID),
    FOREIGN KEY (GalleryID) REFERENCES ObjectGalleryData(GalleryID)
);

CREATE TABLE ArtworkArtist (
    ObjectID INT,
    ArtistID INT,
    PRIMARY KEY (ObjectID, ArtistID),
    FOREIGN KEY (ObjectID) REFERENCES ObjectDetails(ObjectID),
    FOREIGN KEY (ArtistID) REFERENCES Artist(ArtistID)
);

-- User authentication tables
CREATE TABLE IF NOT EXISTS AppUser (
    ID INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(64) UNIQUE NOT NULL,
    username VARCHAR(32) UNIQUE NOT NULL,
    user_password VARCHAR(255) NOT NULL,
    role BOOL NOT NULL
);

INSERT INTO Artist (ArtistName, Nationality, BirthYear, DeathYear, ArtistBio) VALUES
('Claude Monet', 'French', 1840, 1926, 'Founder of French Impressionist painting.'),
('Vincent van Gogh', 'Dutch', 1853, 1890, 'Dutch Post-Impressionist painter.'),
('Frida Kahlo', 'Mexican', 1907, 1954, 'Mexican painter known for self-portraits.'),
('Leonardo da Vinci', 'Italian', 1452, 1519, 'Renaissance polymath.'),
('Georgia O’Keeffe', 'American', 1887, 1986, 'Mother of American modernism.'),
('Hokusai', 'Japanese', 1760, 1849, 'Master of ukiyo-e woodblock prints.');

INSERT INTO ObjectOrigins (Country, City, Culture) VALUES
('France', 'Paris', 'European'),
('Netherlands', 'Amsterdam', 'European'),
('Mexico', 'Coyoacán', 'Latin American'),
('Italy', 'Florence', 'European'),
('USA', 'New York', 'North American'),
('Japan', 'Tokyo', 'Asian');

INSERT INTO ObjectGalleryData (GalleryName, GalleryNumber, Department) VALUES
('Impressionist Art', 201, 'European Paintings'),
('Modern Art', 301, 'Modern and Contemporary Art'),
('Renaissance Hall', 101, 'European Sculpture'),
('Asian Art Wing', 401, 'Asian Art'),
('American Paintings', 205, 'American Art'),
('Global Exhibit', 999, 'World Art Collection');

INSERT INTO ObjectDetails (Title, ObjectType, Medium, YearCreated, OriginID, GalleryID) VALUES
('Water Lilies', 'Painting', 'Oil on Canvas', 1916, 1, 1),
('Starry Night', 'Painting', 'Oil on Canvas', 1889, 2, 1),
('The Two Fridas', 'Painting', 'Oil on Canvas', 1939, 3, 2),
('Mona Lisa', 'Painting', 'Oil on Wood', 1503, 4, 3),
('Red Canna', 'Painting', 'Oil on Canvas', 1924, 5, 5),
('The Great Wave off Kanagawa', 'Print', 'Woodblock Print', 1831, 6, 4);


-- View 1: Artwork Summary (Title + Artist + Gallery)
CREATE VIEW ArtworkSummary AS
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


-- View 2: Artists Whose Artwork Count Is Greater Than ALL Artists from the Same Nationality
CREATE OR REPLACE VIEW v_artists_dominant_in_nationality AS
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


-- View 3: Artwork Origin + Department
CREATE VIEW ArtworkOrigins AS
SELECT 
    o.Title,
    oo.Country,
    oo.City,
    g.Department
FROM ObjectDetails o
JOIN ObjectOrigins oo ON o.OriginID = oo.OriginID
JOIN ObjectGalleryData g ON o.GalleryID = g.GalleryID;


-- View 4: Artworks created after 1900 + Department
CREATE OR REPLACE VIEW v_recent_artworks AS
SELECT 
  o.ObjectID, o.Title, o.YearCreated,
  g.GalleryName, g.Department
FROM ObjectDetails o
JOIN ObjectGalleryData g ON o.GalleryID = g.GalleryID
WHERE o.YearCreated > 1900;


-- View 5: All Artists Who Either (1) Have No Artworks OR (2) Have More Than 1 Artwork
CREATE OR REPLACE VIEW v_artists_zero_or_multiple AS
(
    -- Artists with zero artworks
    SELECT a.ArtistID, a.ArtistName, 0 AS TotalWorks
    FROM Artist a
    WHERE a.ArtistID NOT IN (
        SELECT aa.ArtistID FROM ArtworkArtist aa
    )
)
UNION
(
    -- Artists with more than one artwork
    SELECT a.ArtistID, a.ArtistName, COUNT(aa.ObjectID) AS TotalWorks
    FROM Artist a
    JOIN ArtworkArtist aa ON a.ArtistID = aa.ArtistID
    GROUP BY a.ArtistID, a.ArtistName
    HAVING COUNT(aa.ObjectID) > 1
);


-- View 6: Artworks matched to Origin and those without Origin, Origins without Artwork
CREATE OR REPLACE VIEW v_full_objects_origins AS
SELECT o.ObjectID, o.Title, oo.OriginID, oo.Country, oo.City, oo.Culture
FROM ObjectDetails o
LEFT JOIN ObjectOrigins oo ON o.OriginID = oo.OriginID
UNION
SELECT o.ObjectID, o.Title, oo.OriginID, oo.Country, oo.City, oo.Culture
FROM ObjectDetails o
RIGHT JOIN ObjectOrigins oo ON o.OriginID = oo.OriginID;


-- View 7: Artworks of Artists with (>1) works in Database (Correlated Nested Query)
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
);


 -- View 8: Gallery Artwork Counts (How many artworks per gallery)
CREATE OR REPLACE VIEW v_gallery_artwork_counts AS
SELECT 
    g.GalleryID,
    g.GalleryName,
    g.Department,
    COUNT(o.ObjectID) AS TotalArtworks
FROM ObjectGalleryData g
LEFT JOIN ObjectDetails o ON g.GalleryID = o.GalleryID
GROUP BY g.GalleryID, g.GalleryName, g.Department
ORDER BY TotalArtworks DESC;

-- View 9: Artists With Their Artwork Titles (Flattened list)
CREATE OR REPLACE VIEW v_artist_artwork_titles AS
SELECT 
    a.ArtistID,
    a.ArtistName,
    o.ObjectID,
    o.Title AS ArtworkTitle
FROM Artist a
LEFT JOIN ArtworkArtist aa ON a.ArtistID = aa.ArtistID
LEFT JOIN ObjectDetails o ON aa.ObjectID = o.ObjectID
ORDER BY a.ArtistName, o.Title;


-- View 10: Artworks With Multiple Artists (Collaboration detection)
CREATE OR REPLACE VIEW v_multi_artist_artworks AS
SELECT 
    o.ObjectID,
    o.Title,
    COUNT(aa.ArtistID) AS NumArtists
FROM ObjectDetails o
JOIN ArtworkArtist aa ON o.ObjectID = aa.ObjectID
GROUP BY o.ObjectID, o.Title
HAVING COUNT(aa.ArtistID) > 1
ORDER BY NumArtists DESC;