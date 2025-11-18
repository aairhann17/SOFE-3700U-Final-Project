from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, make_response
from flask_cors import CORS
from functools import wraps
import pymysql
from pymysql import MySQLError
import os
from datetime import datetime
import secrets
import requests  # For external API calls
import re
import csv
from io import StringIO, BytesIO
from reportlab.pdfgen import canvas
from xml.etree.ElementTree import Element, SubElement, tostring
from werkzeug.security import generate_password_hash, check_password_hash
from pathlib import Path

app = Flask(__name__)
# Secret key loaded from environment (fallback for dev)
app.secret_key = os.getenv('ART_MUSEUM_SECRET', 'art_museum_secret_key_2025')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
CORS(app, supports_credentials=True)

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
    """Return current logged in user dict or None (Flask-managed only).
    Roles: 0=regular user, 1=admin, 2=guest (read-only)"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    connection = get_db_connection()
    if not connection:
        return None
    try:
        cursor = connection.cursor()
        cursor.execute('SELECT ID, username, role FROM user WHERE ID = %s', (user_id,))
        return cursor.fetchone()
    except MySQLError:
        return None
    finally:
        cursor.close()
        connection.close()

def login_required(f):
    """Decorator for requiring authentication."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = get_user_from_session()
        if not user:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    """Decorator requiring admin role (role=1)."""
    def guest_allowed(f):
        """Decorator allowing guests (role=2) and authenticated users. Guests have read-only access."""
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = get_user_from_session()
            if not user:
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'Authentication required'}), 401
                return redirect(url_for('login', next=request.path))
            # Allow role 0 (user), 1 (admin), or 2 (guest)
            return f(*args, **kwargs)
        return wrapper

    @wraps(f)
    def wrapper(*args, **kwargs):
        user = get_user_from_session()
        if not user:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login', next=request.path))
        if user['role'] != 1:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Admin access required'}), 403
            flash('Admin access required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return wrapper

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

# ---------- Authentication Pages ----------

EMAIL_REGEX = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')

def validate_password_strength(pw: str) -> bool:
    # Minimum 8 chars, one letter, one digit
    return bool(re.search(r'[A-Za-z]', pw) and re.search(r'\d', pw) and len(pw) >= 8)

def generate_csrf_token():
    token = session.get('csrf_token')
    if not token:
        token = secrets.token_hex(16)
        session['csrf_token'] = token
    return token

@app.context_processor
def inject_csrf():
    return {'csrf_token': generate_csrf_token()}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        form_token = request.form.get('csrf_token')
        if not form_token or form_token != session.get('csrf_token'):
            flash('CSRF token missing or invalid.', 'danger')
            return render_template('login.html')
        connection = get_db_connection()
        if not connection:
            flash('Database connection failed.', 'danger')
            return render_template('login.html')
        try:
            cursor = connection.cursor()
            cursor.execute('SELECT ID, username, user_password, role FROM user WHERE username = %s', (username,))
            user = cursor.fetchone()
            if user:
                try:
                    if check_password_hash(user['user_password'], password):
                        session['user_id'] = user['ID']
                        session['role'] = user['role']
                        flash('Logged in successfully.', 'success')
                        next_url = request.args.get('next') or url_for('index')
                        return redirect(next_url)
                except ValueError:
                    flash('Legacy password format detected. Please re-register your account.', 'warning')
                    return redirect(url_for('register'))
            flash('Invalid credentials.', 'danger')
        finally:
            cursor.close()
            connection.close()
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')
        form_token = request.form.get('csrf_token')
        if not form_token or form_token != session.get('csrf_token'):
            flash('CSRF token missing or invalid.', 'danger')
            return render_template('register.html')
        if not email or not username or not password:
            flash('All fields are required.', 'danger')
            return render_template('register.html')
        if not EMAIL_REGEX.match(email):
            flash('Invalid email format.', 'danger')
            return render_template('register.html')
        if not validate_password_strength(password):
            flash('Password must be ≥8 chars and include a letter and a digit.', 'danger')
            return render_template('register.html')
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        connection = get_db_connection()
        if not connection:
            flash('Database connection failed.', 'danger')
            return render_template('register.html')
        try:
            cursor = connection.cursor()
            cursor.execute('SELECT ID FROM user WHERE username = %s OR email = %s', (username, email))
            existing = cursor.fetchone()
            if existing:
                flash('Username or email already exists.', 'warning')
                return render_template('register.html')
            # Check if registering as guest (optional query param)
            guest_mode = request.args.get('guest', '').lower() == 'true'
            role = 2 if guest_mode else 0  # 0=user, 1=admin (manual), 2=guest
            hashed = generate_password_hash(password)
            cursor.execute('INSERT INTO user (email, username, user_password, role) VALUES (%s, %s, %s, %s)', (email, username, hashed, role))
            connection.commit()
            flash(f'{"Guest" if guest_mode else "User"} account created. Please log in.', 'success')
            return redirect(url_for('login'))
        finally:
            cursor.close()
            connection.close()
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'info')
    return redirect(url_for('login'))

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

@app.route('/stats.html')
@login_required
def stats_page():
    user = get_user_from_session()
    return render_template('stats.html', user=user)

@app.route('/views.html')
@login_required
def views_page():
    user = get_user_from_session()
    return render_template('views.html', user=user)

@app.route('/edit_artwork/<int:object_id>')
@admin_required
def edit_artwork_page(object_id):
    user = get_user_from_session()
    return render_template('edit_artwork.html', user=user, object_id=object_id)

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
        artist_name = request.args.get('artistName', '').strip()
        country = request.args.get('country', '').strip()
        year_from = request.args.get('yearFrom', type=int)
        year_to = request.args.get('yearTo', type=int)
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 25, type=int)
        offset = (page - 1) * limit
        
        allowed_fields_artworks = {'Title','Medium','ObjectType','YearCreated'}
        allowed_fields_artists = {'ArtistName','Nationality','BirthYear','DeathYear'}
        if field:
            field = field.strip()
        if category == 'artworks':
            use_field = field if field in allowed_fields_artworks else 'Title'
            sql = '''
                SELECT od.*, oo.Country, ogd.GalleryName
                FROM ObjectDetails od
                LEFT JOIN ObjectOrigins oo ON od.OriginID = oo.OriginID
                LEFT JOIN ObjectGalleryData ogd ON od.GalleryID = ogd.GalleryID
                WHERE 1=1
            '''
            params = []
            if query:
                if match_type == 'exact':
                    sql += f" AND {use_field} = %s"
                    params.append(query)
                else:
                    sql += f" AND {use_field} LIKE %s"
                    params.append(f"%{query}%")
            if country:
                sql += " AND oo.Country = %s"
                params.append(country)
            if year_from is not None:
                sql += " AND CAST(od.YearCreated AS UNSIGNED) >= %s"
                params.append(year_from)
            if year_to is not None:
                sql += " AND CAST(od.YearCreated AS UNSIGNED) <= %s"
                params.append(year_to)
            if artist_name:
                sql += ''' AND EXISTS (
                    SELECT 1 FROM ArtworkArtist aa
                    JOIN Artist a ON a.ArtistID = aa.ArtistID
                    WHERE aa.ObjectID = od.ObjectID AND a.ArtistName LIKE %s
                )'''
                params.append(f"%{artist_name}%")
            sql += " ORDER BY od.Title LIMIT %s OFFSET %s"
            params.extend([limit, offset])
        
        elif category == 'artists':
            use_field = field if field in allowed_fields_artists else 'ArtistName'
            sql = 'SELECT * FROM Artist WHERE 1=1'
            params = []
            if query:
                if match_type == 'exact':
                    sql += f" AND {use_field} = %s"
                    params.append(query)
                else:
                    sql += f" AND {use_field} LIKE %s"
                    params.append(f"%{query}%")
            if country:
                sql += " AND Nationality = %s"
                params.append(country)
            sql += " ORDER BY ArtistName LIMIT %s OFFSET %s"
            params.extend([limit, offset])
        else:
            return jsonify({'records': []})
        cursor.execute(sql, params)
        results = cursor.fetchall()
        return jsonify({'records': results, 'page': page, 'limit': limit})
    except MySQLError as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

# Whitelist of allowed SQL views
ALLOWED_VIEWS = {
    'ArtworkSummary': 'ArtworkSummary',
    'v_artists_dominant_in_nationality': 'v_artists_dominant_in_nationality',
    'ArtworkOrigins': 'ArtworkOrigins',
    'v_recent_artworks': 'v_recent_artworks',
    'v_artists_zero_or_multiple': 'v_artists_zero_or_multiple',
    'v_full_objects_origins': 'v_full_objects_origins',
    'v_artworks_by_prolific_artists': 'v_artworks_by_prolific_artists',
    'v_gallery_artwork_counts': 'v_gallery_artwork_counts',
    'v_artist_artwork_titles': 'v_artist_artwork_titles',
    'v_multi_artist_artworks': 'v_multi_artist_artworks'
}

# API endpoint to get SQL view data
@app.route('/api/views/<view_name>', methods=['GET'])
@login_required
def get_sql_view(view_name):
    # Validate view name against whitelist
    if view_name not in ALLOWED_VIEWS:
        return jsonify({'error': 'Invalid view name'}), 400
    
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    offset = (page - 1) * limit
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Build base select to reuse in both queries
        base_select = f"SELECT * FROM {ALLOWED_VIEWS[view_name]}"

        # Try direct COUNT first, fallback to derived-table COUNT if needed
        total = 0
        try:
            cursor.execute(f"SELECT COUNT(*) as total FROM {ALLOWED_VIEWS[view_name]}")
            total = cursor.fetchone()['total']
        except Exception as ce:
            # Fallback using derived table without ORDER BY influence
            fallback = f"SELECT COUNT(*) as total FROM ({base_select}) AS t"
            cursor.execute(fallback)
            total = cursor.fetchone()['total']

        # Get paginated data
        data_query = base_select + " LIMIT %s OFFSET %s"
        cursor.execute(data_query, (limit, offset))
        rows = cursor.fetchall()

        # Get column names from the last select
        columns = [desc[0] for desc in cursor.description] if cursor.description else []

        return jsonify({
            'view': view_name,
            'columns': columns,
            'records': rows,
            'page': page,
            'limit': limit,
            'total': total,
            'totalPages': (total + limit - 1) // limit if limit else 1
        })
    except Exception as e:
        # Log server-side for debugging
        print(f"[ERROR] /api/views/{view_name}: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

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
        
        cursor.execute('SELECT oo.Country, COUNT(*) as count FROM ObjectDetails od LEFT JOIN ObjectOrigins oo ON od.OriginID=oo.OriginID GROUP BY oo.Country ORDER BY count DESC LIMIT 10')
        by_country = cursor.fetchall()
        cursor.execute('SELECT a.ArtistName, COUNT(*) as count FROM ArtworkArtist aa JOIN Artist a ON a.ArtistID=aa.ArtistID GROUP BY a.ArtistName ORDER BY count DESC LIMIT 10')
        by_artist = cursor.fetchall()
        return jsonify({
            'artworks': artworks_count,
            'artists': artists_count,
            'topCountries': by_country,
            'topArtists': by_artist
        })
    except MySQLError as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

# -------------------------------------
# Admin utility: Recreate SQL Views
# -------------------------------------

def _execute_sql_file(connection, file_path: str) -> int:
    """Execute semicolon-terminated statements from a .sql file. Returns count executed."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"SQL file not found: {file_path}")
    sql_text = path.read_text(encoding='utf-8')
    statements = []
    buffer = []
    for line in sql_text.splitlines():
        # Skip comment lines
        striped = line.strip()
        if striped.startswith('--') or striped.startswith('#'):
            continue
        buffer.append(line)
        if striped.endswith(';'):
            stmt = '\n'.join(buffer).rstrip().rstrip(';').strip()
            if stmt:
                statements.append(stmt)
            buffer = []
    # Append any remaining buffer (in case last line missing semicolon)
    if buffer:
        stmt = '\n'.join(buffer).strip()
        if stmt:
            statements.append(stmt)
    cur = connection.cursor()
    executed = 0
    try:
        for stmt in statements:
            cur.execute(stmt)
            executed += 1
        connection.commit()
        return executed
    except Exception:
        connection.rollback()
        raise
    finally:
        cur.close()


@app.route('/api/admin/recreate_views', methods=['POST'])
@admin_required
def api_recreate_views():
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        sql_file = os.path.join(os.path.dirname(__file__), 'recreate_views.sql')
        executed = _execute_sql_file(connection, sql_file)
        return jsonify({'ok': True, 'executed': executed})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

@app.route('/admin/recreate_views', methods=['GET'])
@admin_required
def web_recreate_views():
    connection = get_db_connection()
    if not connection:
        return 'Database connection failed', 500
    try:
        sql_file = os.path.join(os.path.dirname(__file__), 'recreate_views.sql')
        executed = _execute_sql_file(connection, sql_file)
        return f'Recreated views successfully. Executed {executed} statements.'
    except Exception as e:
        return f'Error: {e}', 500
    finally:
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

# =====================================
# Data Export Endpoints (CSV / PDF)
# =====================================

@app.route('/api/export/artworks.csv', methods=['GET'])
@login_required
def export_artworks_csv():
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT od.ObjectID, od.Title, od.ObjectType, od.Medium, od.YearCreated, oo.Country, ogd.GalleryName
            FROM ObjectDetails od
            LEFT JOIN ObjectOrigins oo ON od.OriginID = oo.OriginID
            LEFT JOIN ObjectGalleryData ogd ON od.GalleryID = ogd.GalleryID
            ORDER BY od.Title
        ''')
        rows = cursor.fetchall()
        si = StringIO()
        writer = csv.writer(si)
        writer.writerow(['ObjectID','Title','ObjectType','Medium','YearCreated','Country','Gallery'])
        for r in rows:
            writer.writerow([r['ObjectID'], r['Title'], r.get('ObjectType',''), r.get('Medium',''), r.get('YearCreated',''), r.get('Country',''), r.get('GalleryName','')])
        output = make_response(si.getvalue())
        output.headers['Content-Disposition'] = 'attachment; filename=artworks.csv'
        output.headers['Content-Type'] = 'text/csv'
        return output
    except MySQLError as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close(); connection.close()

@app.route('/api/export/artworks.pdf', methods=['GET'])
@login_required
def export_artworks_pdf():
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = connection.cursor()
        cursor.execute('SELECT ObjectID, Title, YearCreated FROM ObjectDetails ORDER BY Title LIMIT 200')
        rows = cursor.fetchall()
        buffer = BytesIO()
        c = canvas.Canvas(buffer)
        c.setFont('Helvetica', 12)
        c.drawString(40, 800, 'Artworks (First 200)')
        y = 780
        for r in rows:
            line = f"{r['ObjectID']} - {r['Title']} ({r.get('YearCreated','')})"
            c.drawString(40, y, line[:100])
            y -= 16
            if y < 40:
                c.showPage(); c.setFont('Helvetica', 12); y = 800
        c.save()
        pdf = buffer.getvalue(); buffer.close()
        resp = make_response(pdf)
        resp.headers['Content-Type'] = 'application/pdf'
        resp.headers['Content-Disposition'] = 'attachment; filename=artworks.pdf'
        return resp
    except MySQLError as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close(); connection.close()

# =====================================
# XML Endpoint
# =====================================

@app.route('/api/artworks.xml', methods=['GET'])
@login_required
def artworks_xml():
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT od.ObjectID, od.Title, od.ObjectType, od.Medium, od.YearCreated, oo.Country, ogd.GalleryName
            FROM ObjectDetails od
            LEFT JOIN ObjectOrigins oo ON od.OriginID = oo.OriginID
            LEFT JOIN ObjectGalleryData ogd ON od.GalleryID = ogd.GalleryID
            ORDER BY od.Title
            LIMIT 500
        ''')
        rows = cursor.fetchall()
        root = Element('Artworks')
        for r in rows:
            art_el = SubElement(root, 'Artwork', id=str(r['ObjectID']))
            SubElement(art_el, 'Title').text = r['Title']
            SubElement(art_el, 'Type').text = r.get('ObjectType','') or ''
            SubElement(art_el, 'Medium').text = r.get('Medium','') or ''
            SubElement(art_el, 'YearCreated').text = r.get('YearCreated','') or ''
            SubElement(art_el, 'Country').text = r.get('Country','') or ''
            SubElement(art_el, 'Gallery').text = r.get('GalleryName','') or ''
        xml_bytes = tostring(root, encoding='utf-8')
        resp = make_response(xml_bytes)
        resp.headers['Content-Type'] = 'application/xml'
        return resp
    except MySQLError as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close(); connection.close()

# =====================================
# Global Error Handlers
# =====================================

@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    flash('Page not found.', 'warning')
    return redirect(url_for('index'))

@app.errorhandler(500)
def server_error(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    flash('An internal error occurred.', 'danger')
    return redirect(url_for('index'))

# =====================================
# Utility / Validation Endpoints
# =====================================

@app.route('/api/username_available')
def username_available():
    username = request.args.get('u', '').strip()
    if not username:
        return jsonify({'available': False, 'reason': 'blank'}), 200
    connection = get_db_connection()
    if not connection:
        return jsonify({'available': False, 'error': 'db'}), 500
    try:
        cursor = connection.cursor()
        cursor.execute('SELECT ID FROM user WHERE username=%s', (username,))
        row = cursor.fetchone()
        return jsonify({'available': row is None})
    finally:
        cursor.close(); connection.close()

if __name__ == '__main__':
    init_db()
    print("Starting Art Museum Database Server...")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, port=5000)
