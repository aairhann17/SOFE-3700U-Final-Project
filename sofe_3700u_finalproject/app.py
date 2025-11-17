from flask import Flask, render_template, request, jsonify, session, redirect
from flask_cors import CORS
from functools import wraps
import pymysql
from pymysql import MySQLError
import os
from datetime import datetime
import secrets
import requests  # For external API calls

app = Flask(__name__)
app.secret_key = 'art_museum_secret_key_2025'  # Fixed secret key for session sharing
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = False  # Allow JavaScript access for debugging
app.config['SESSION_COOKIE_DOMAIN'] = 'localhost'  # Share cookies across localhost
CORS(app, supports_credentials=True, origins=['http://localhost', 'http://localhost:5000'])

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'softEng@2028',
    'database': 'art_museum_db'
}

# =====================================
# Authentication & Authorization
# =====================================

def get_user_from_session():
    """Get user info from database based on session"""
    # Check Flask session first
    user_id = session.get('loggedInUser')
    
    # If not in Flask session, check request cookies for PHP session
    if not user_id and 'PHPSESSID' in request.cookies:
        # Try to read user from query param (PHP can pass it)
        user_id = request.args.get('user_id')
    
    if not user_id:
        return None
    
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        cursor.execute('SELECT ID, username, role FROM user WHERE ID = %s', (user_id,))
        user = cursor.fetchone()
        # Store in Flask session for future requests
        if user:
            session['loggedInUser'] = user['ID']
        return user
    except MySQLError:
        return None
    finally:
        if connection:
            cursor.close()
            connection.close()

def login_required(f):
    """Decorator to require login for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_user_from_session()
        if not user:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect('http://localhost/art_museum/signin.php')
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_user_from_session()
        if not user:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect('http://localhost/art_museum/signin.php')
        if user['role'] != 1:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Admin access required'}), 403
            # For HTML pages, redirect to home with error message
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function

# Create database connection using PyMySQL
def get_db_connection():
    try:
        return pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False
        )
    except MySQLError as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# Initialize database
def init_db():
    try:
        connection = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        print(f"Database '{DB_CONFIG['database']}' created or already exists.")
        cursor.close()
        connection.close()
    except MySQLError as e:
        print(f"Error creating database: {e}")

# =====================================
# Routes - HTML Pages
# =====================================

@app.route('/test')
def test():
    """Test endpoint to verify server is working"""
    return jsonify({
        'status': 'Server is running',
        'session_keys': list(session.keys()) if session else [],
        'has_user': 'loggedInUser' in session
    })

@app.route('/')
@login_required
def index():
    user = get_user_from_session()
    return render_template('index.html', user=user)

@app.route('/view_records.html')
@login_required
def view_records():
    user = get_user_from_session()
    return render_template('view_records.html', user=user)

@app.route('/add_record.html')
@admin_required
def add_record():
    user = get_user_from_session()
    return render_template('add_record.html', user=user)

@app.route('/search.html')
@login_required
def search():
    user = get_user_from_session()
    return render_template('search.html', user=user)

@app.route('/import_artworks.html')
@admin_required
def import_artworks():
    user = get_user_from_session()
    return render_template('import_artworks.html', user=user)

# =====================================
# API Routes - Artists
# =====================================

@app.route('/api/artists', methods=['GET'])
@login_required
def get_artists():
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 25, type=int)
        offset = (page - 1) * limit
        
        cursor.execute('SELECT COUNT(*) as total FROM Artist')
        total = cursor.fetchone()['total']
        
        cursor.execute(f'''
            SELECT ArtistID, ArtistName, Nationality, BirthYear, DeathYear, ArtistBio
            FROM Artist
            ORDER BY ArtistName
            LIMIT {limit} OFFSET {offset}
        ''')
        artists = cursor.fetchall()
        
        return jsonify({
            'records': artists,
            'total': total,
            'page': page,
            'totalPages': (total + limit - 1) // limit
        })
    except MySQLError as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/artists/<int:artist_id>', methods=['GET'])
@login_required
def get_artist(artist_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM Artist WHERE ArtistID = %s', (artist_id,))
        artist = cursor.fetchone()
        
        if artist:
            return jsonify(artist)
        return jsonify({'error': 'Artist not found'}), 404
    except MySQLError as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/artists', methods=['POST'])
@admin_required
def create_artist():
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    data = request.get_json()
    try:
        cursor = connection.cursor()
        cursor.execute('''
            INSERT INTO Artist (ArtistName, Nationality, BirthYear, DeathYear, ArtistBio)
            VALUES (%s, %s, %s, %s, %s)
        ''', (data['ArtistName'], data.get('Nationality'), data.get('BirthYear'), 
              data.get('DeathYear'), data.get('ArtistBio')))
        connection.commit()
        
        return jsonify({'message': 'Artist created successfully', 'id': cursor.lastrowid}), 201
    except MySQLError as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/artists/<int:artist_id>', methods=['PUT'])
@admin_required
def update_artist(artist_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    data = request.get_json()
    try:
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE Artist 
            SET ArtistName=%s, Nationality=%s, BirthYear=%s, DeathYear=%s, ArtistBio=%s
            WHERE ArtistID=%s
        ''', (data['ArtistName'], data.get('Nationality'), data.get('BirthYear'),
              data.get('DeathYear'), data.get('ArtistBio'), artist_id))
        connection.commit()
        
        if cursor.rowcount > 0:
            return jsonify({'message': 'Artist updated successfully'})
        return jsonify({'error': 'Artist not found'}), 404
    except MySQLError as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/artists/<int:artist_id>', methods=['DELETE'])
@admin_required
def delete_artist(artist_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        cursor.execute('DELETE FROM Artist WHERE ArtistID = %s', (artist_id,))
        connection.commit()
        
        if cursor.rowcount > 0:
            return jsonify({'message': 'Artist deleted successfully'})
        return jsonify({'error': 'Artist not found'}), 404
    except MySQLError as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

# =====================================
# API Routes - Artworks (ObjectDetails)
# =====================================

@app.route('/api/artworks', methods=['GET'])
@login_required
def get_artworks():
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 25, type=int)
        offset = (page - 1) * limit
        
        cursor.execute('SELECT COUNT(*) as total FROM ObjectDetails')
        total = cursor.fetchone()['total']
        
        cursor.execute(f'''
            SELECT od.*, oo.Country, oo.City, ogd.GalleryName
            FROM ObjectDetails od
            LEFT JOIN ObjectOrigins oo ON od.OriginID = oo.OriginID
            LEFT JOIN ObjectGalleryData ogd ON od.GalleryID = ogd.GalleryID
            ORDER BY od.Title
            LIMIT {limit} OFFSET {offset}
        ''')
        artworks = cursor.fetchall()
        
        return jsonify({
            'records': artworks,
            'total': total,
            'page': page,
            'totalPages': (total + limit - 1) // limit
        })
    except MySQLError as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/artworks/<int:object_id>', methods=['GET'])
@login_required
def get_artwork(object_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT od.*, oo.Country, oo.City, oo.Culture, ogd.GalleryName, ogd.Department
            FROM ObjectDetails od
            LEFT JOIN ObjectOrigins oo ON od.OriginID = oo.OriginID
            LEFT JOIN ObjectGalleryData ogd ON od.GalleryID = ogd.GalleryID
            WHERE od.ObjectID = %s
        ''', (object_id,))
        artwork = cursor.fetchone()
        
        if artwork:
            # Get associated artists
            cursor.execute('''
                SELECT a.* FROM Artist a
                JOIN ArtworkArtist aa ON a.ArtistID = aa.ArtistID
                WHERE aa.ObjectID = %s
            ''', (object_id,))
            artwork['artists'] = cursor.fetchall()
            return jsonify(artwork)
        return jsonify({'error': 'Artwork not found'}), 404
    except MySQLError as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/artworks', methods=['POST'])
@admin_required
def create_artwork():
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    data = request.get_json()
    try:
        cursor = connection.cursor()
        cursor.execute('''
            INSERT INTO ObjectDetails (Title, ObjectType, Medium, YearCreated, OriginID, GalleryID)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (data['Title'], data.get('ObjectType'), data.get('Medium'),
              data.get('YearCreated'), data.get('OriginID'), data.get('GalleryID')))
        connection.commit()
        
        return jsonify({'message': 'Artwork created successfully', 'id': cursor.lastrowid}), 201
    except MySQLError as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/artworks/<int:object_id>', methods=['PUT'])
@admin_required
def update_artwork(object_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    data = request.get_json()
    try:
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE ObjectDetails 
            SET Title=%s, ObjectType=%s, Medium=%s, YearCreated=%s, OriginID=%s, GalleryID=%s
            WHERE ObjectID=%s
        ''', (data['Title'], data.get('ObjectType'), data.get('Medium'),
              data.get('YearCreated'), data.get('OriginID'), data.get('GalleryID'), object_id))
        connection.commit()
        
        if cursor.rowcount > 0:
            return jsonify({'message': 'Artwork updated successfully'})
        return jsonify({'error': 'Artwork not found'}), 404
    except MySQLError as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/artworks/<int:object_id>', methods=['DELETE'])
@admin_required
def delete_artwork(object_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        cursor.execute('DELETE FROM ObjectDetails WHERE ObjectID = %s', (object_id,))
        connection.commit()
        
        if cursor.rowcount > 0:
            return jsonify({'message': 'Artwork deleted successfully'})
        return jsonify({'error': 'Artwork not found'}), 404
    except MySQLError as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

# =====================================
# API Routes - Origins & Galleries
# =====================================

@app.route('/api/origins', methods=['GET'])
@login_required
def get_origins():
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM ObjectOrigins ORDER BY Country')
        origins = cursor.fetchall()
        return jsonify(origins)
    except MySQLError as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/galleries', methods=['GET'])
@login_required
def get_galleries():
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM ObjectGalleryData ORDER BY GalleryName')
        galleries = cursor.fetchall()
        return jsonify(galleries)
    except MySQLError as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

# =====================================
# API Routes - Search & Stats
# =====================================

@app.route('/api/search', methods=['GET'])
@login_required
def search_collection():
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        category = request.args.get('category', '')
        field = request.args.get('field', '')
        query = request.args.get('query', '')
        match_type = request.args.get('matchType', 'partial')
        
        if category == 'artworks':
            sql = '''
                SELECT od.*, oo.Country, ogd.GalleryName
                FROM ObjectDetails od
                LEFT JOIN ObjectOrigins oo ON od.OriginID = oo.OriginID
                LEFT JOIN ObjectGalleryData ogd ON od.GalleryID = ogd.GalleryID
                WHERE 1=1
            '''
            if query:
                if match_type == 'exact':
                    sql += f" AND {field if field else 'Title'} = '{query}'"
                else:
                    sql += f" AND {field if field else 'Title'} LIKE '%{query}%'"
        
        elif category == 'artists':
            sql = 'SELECT * FROM Artist WHERE 1=1'
            if query:
                if match_type == 'exact':
                    sql += f" AND {field if field else 'ArtistName'} = '{query}'"
                else:
                    sql += f" AND {field if field else 'ArtistName'} LIKE '%{query}%'"
        else:
            return jsonify({'records': []})
        
        cursor.execute(sql)
        results = cursor.fetchall()
        return jsonify({'records': results})
    except MySQLError as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM ObjectDetails')
        artworks_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM Artist')
        artists_count = cursor.fetchone()['count']
        
        return jsonify({
            'artworks': artworks_count,
            'artists': artists_count
        })
    except MySQLError as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

# =====================================
# External API Integration - Metropolitan Museum of Art
# =====================================

@app.route('/api/external/met/search', methods=['GET'])
@login_required
def search_met_artworks():
    """Search Metropolitan Museum of Art API (External REST/JSON API)"""
    try:
        query = request.args.get('q', 'painting')
        has_images = request.args.get('hasImages', 'true')
        
        # Call external Met Museum API
        search_url = f'https://collectionapi.metmuseum.org/public/collection/v1/search'
        params = {
            'q': query,
            'hasImages': has_images
        }
        
        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Limit results to first 20 for performance
        if data.get('objectIDs'):
            object_ids = data['objectIDs'][:20]
            return jsonify({
                'success': True,
                'total': data.get('total', 0),
                'objectIDs': object_ids,
                'message': f'Found {len(object_ids)} artworks'
            })
        
        return jsonify({
            'success': False,
            'message': 'No artworks found',
            'objectIDs': []
        })
    
    except requests.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'External API error: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/external/met/object/<int:object_id>', methods=['GET'])
@login_required
def get_met_artwork_details(object_id):
    """Fetch artwork details from Met Museum API (External REST/JSON API)"""
    try:
        # Call external Met Museum API for object details
        object_url = f'https://collectionapi.metmuseum.org/public/collection/v1/objects/{object_id}'
        
        response = requests.get(object_url, timeout=10)
        response.raise_for_status()
        
        artwork_data = response.json()
        
        # Extract and format relevant data
        formatted_data = {
            'metObjectID': artwork_data.get('objectID'),
            'title': artwork_data.get('title', 'Untitled'),
            'artistName': artwork_data.get('artistDisplayName', 'Unknown'),
            'artistNationality': artwork_data.get('artistNationality', ''),
            'artistBio': artwork_data.get('artistDisplayBio', ''),
            'objectType': artwork_data.get('objectName', ''),
            'medium': artwork_data.get('medium', ''),
            'yearCreated': artwork_data.get('objectDate', ''),
            'culture': artwork_data.get('culture', ''),
            'country': artwork_data.get('country', ''),
            'city': artwork_data.get('city', ''),
            'department': artwork_data.get('department', ''),
            'gallery': artwork_data.get('GalleryNumber', ''),
            'primaryImage': artwork_data.get('primaryImage', ''),
            'metURL': artwork_data.get('objectURL', '')
        }
        
        return jsonify({
            'success': True,
            'data': formatted_data
        })
    
    except requests.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'External API error: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/external/met/import', methods=['POST'])
@admin_required
def import_met_artwork():
    """Import artwork from Met Museum into local database (Saves external data)"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        data = request.get_json()
        met_object_id = data.get('metObjectID')
        
        if not met_object_id:
            return jsonify({'error': 'Met Object ID required'}), 400
        
        # Fetch data from external Met Museum API
        object_url = f'https://collectionapi.metmuseum.org/public/collection/v1/objects/{met_object_id}'
        response = requests.get(object_url, timeout=10)
        response.raise_for_status()
        artwork_data = response.json()
        
        cursor = connection.cursor()
        # Begin a single transaction for the entire import operation
        # (autocommit is False by default; we'll commit once at the end)
        
        # Query 1: Check/Create Origin (saves external location data)
        country = artwork_data.get('country', '') or 'Unknown'
        city = artwork_data.get('city', '') or ''
        culture = artwork_data.get('culture', '') or ''
        
        cursor.execute('''
            SELECT OriginID FROM ObjectOrigins 
            WHERE Country = %s AND City = %s AND Culture = %s
        ''', (country, city, culture))
        
        origin = cursor.fetchone()
        if origin:
            origin_id = origin['OriginID']
        else:
            cursor.execute('''
                INSERT INTO ObjectOrigins (Country, City, Culture)
                VALUES (%s, %s, %s)
            ''', (country, city, culture))
            origin_id = cursor.lastrowid
        
        # Query 2: Check/Create Gallery (saves external gallery data)
        gallery_name = artwork_data.get('GalleryNumber', '') or 'Metropolitan Museum'
        department = artwork_data.get('department', '') or 'General Collection'
        
        cursor.execute('''
            SELECT GalleryID FROM ObjectGalleryData 
            WHERE GalleryName = %s AND Department = %s
        ''', (gallery_name, department))
        
        gallery = cursor.fetchone()
        if gallery:
            gallery_id = gallery['GalleryID']
        else:
            cursor.execute('''
                INSERT INTO ObjectGalleryData (GalleryName, Department)
                VALUES (%s, %s)
            ''', (gallery_name, department))
            gallery_id = cursor.lastrowid
        
        # Query 3: Check/Create Artist (saves external artist data)
        artist_name = artwork_data.get('artistDisplayName', '') or 'Unknown Artist'
        nationality = artwork_data.get('artistNationality', '') or ''
        artist_bio = artwork_data.get('artistDisplayBio', '') or ''
        
        # Try to extract birth/death years from bio
        birth_year = artwork_data.get('artistBeginDate', '') or None
        death_year = artwork_data.get('artistEndDate', '') or None
        
        cursor.execute('''
            SELECT ArtistID FROM Artist 
            WHERE ArtistName = %s
        ''', (artist_name,))
        
        artist = cursor.fetchone()
        if artist:
            artist_id = artist['ArtistID']
        else:
            cursor.execute('''
                INSERT INTO Artist (ArtistName, Nationality, BirthYear, DeathYear, ArtistBio)
                VALUES (%s, %s, %s, %s, %s)
            ''', (artist_name, nationality, birth_year, death_year, artist_bio))
            artist_id = cursor.lastrowid
        
        # Query 4: Insert Artwork (saves external artwork data)
        title = artwork_data.get('title', 'Untitled')
        object_type = artwork_data.get('objectName', '')
        medium = artwork_data.get('medium', '')
        year_created = artwork_data.get('objectDate', '')
        
        cursor.execute('''
            INSERT INTO ObjectDetails (Title, ObjectType, Medium, YearCreated, OriginID, GalleryID)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (title, object_type, medium, year_created, origin_id, gallery_id))
        object_id = cursor.lastrowid
        
        # Query 5: Link Artist to Artwork (saves external relationship data)
        cursor.execute('''
            INSERT INTO ArtworkArtist (ObjectID, ArtistID)
            VALUES (%s, %s)
        ''', (object_id, artist_id))

        # Commit once after all statements succeed
        connection.commit()
        
        return jsonify({
            'success': True,
            'message': 'Artwork imported successfully from Met Museum',
            'objectID': object_id,
            'metObjectID': met_object_id,
            'title': title,
            'artist': artist_name
        }), 201
    
    except requests.RequestException as e:
        if connection:
            connection.rollback()
        return jsonify({
            'success': False,
            'error': f'External API error: {str(e)}'
        }), 500
    except MySQLError as e:
        if connection:
            connection.rollback()
        return jsonify({
            'success': False,
            'error': f'Database error: {str(e)}'
        }), 500
    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if connection:
            cursor.close()
            connection.close()

if __name__ == '__main__':
    init_db()
    print("Starting Art Museum Database Server...")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, port=5000)
