# 🎨 Art Museum Database - SOFE 3700U Final Project

A full-stack web application for managing an art museum's collection, including artworks, artists, exhibitions, and gallery information.

## 📋 Features

- **Browse Collection**: View artworks, artists, exhibitions, and galleries with pagination
- **Add Items**: Add new artworks, artists, and other museum data
- **Search**: Advanced search functionality with filtering options
- **CRUD Operations**: Complete Create, Read, Update, Delete for all entities
- **Responsive Design**: Modern UI that works on desktop and mobile

## 🛠️ Technology Stack

### Backend

- **Python Flask** - Web framework
- **MySQL** - Relational database
- **Flask-CORS** - Cross-origin resource sharing

### Frontend

- **HTML5/CSS3** - Structure and styling
- **JavaScript (ES6)** - Client-side logic
- **Bootstrap 5** - Responsive UI framework
- **Font Awesome** - Icons

## 📊 Database Schema

- **Artist**: Artist information (name, nationality, birth/death years, bio)
- **ObjectDetails**: Artwork details (title, type, medium, year)
- **ObjectOrigins**: Geographic origins (country, city, culture)
- **ObjectGalleryData**: Gallery information (name, number, department)
- **ArtworkArtist**: Many-to-many relationship between artworks and artists

## 🚀 Setup Instructions

### Prerequisites

1. **Python 3.8+** installed
2. **MySQL Server** installed and running
3. **pip** (Python package manager)

### Step 1: Install Python Dependencies

Open PowerShell in the project directory and run:

```powershell
pip install -r requirements.txt
```

This installs:

- Flask (web framework)
- flask-cors (CORS support)
- mysql-connector-python (MySQL database driver)

### Step 2: Configure Database Credentials

1. Open `config.py`
2. Update the MySQL credentials:

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',           # Your MySQL username
    'password': 'your_password',  # Your MySQL password
    'database': 'art_museum_db'
}
```

*Important*: Also update the same credentials in `app.py` (lines 11-15) and `setup_database.py` (lines 5-9)

### Step 3: Create and Populate Database

Run the database setup script:

```powershell
python setup_database.py
```

This will:

- Create the `art_museum_db` database
- Create all tables (Artist, ObjectDetails, ObjectOrigins, etc.)
- Insert sample data (6 artists, 6 artworks, etc.)

**Expected Output:**

```bash
✓ Database 'art_museum_db' created/selected
✓ Executed statements...
✓ Database setup completed successfully!
Artists: 6
Artworks: 6
```

### Step 4: Start the Flask Server

```powershell
python app.py
```

**Expected Output:**

```bash
Starting Art Museum Database Server...
Open http://localhost:5000 in your browser
 * Running on http://127.0.0.1:5000
```

### Step 5: Access the Application

Open your web browser and navigate to:

```bash
http://localhost:5000
```

## 📁 Project Structure

```bash
sofe_3700u_finalproject/
│
├── app.py                    # Flask backend server
├── config.py                 # Configuration settings
├── setup_database.py         # Database initialization script
├── database.sql              # SQL schema and sample data
├── requirements.txt          # Python dependencies
│
├── templates/                # HTML pages
│   ├── index.html           # Home page
│   ├── view_records.html    # Browse collection
│   ├── add_record.html      # Add new items
│   └── search.html          # Search functionality
│
└── static/                   # Static assets
    ├── css/
    │   └── style.css        # Custom styles
    └── js/
        ├── main.js          # Core utilities
        ├── view_records.js  # View/edit/delete logic
        ├── add_record.js    # Add record logic
        └── search.js        # Search logic
```

## 🔌 API Endpoints

### Artists

- `GET /api/artists` - Get all artists (paginated)
- `GET /api/artists/<id>` - Get single artist
- `POST /api/artists` - Create new artist
- `PUT /api/artists/<id>` - Update artist
- `DELETE /api/artists/<id>` - Delete artist

### Artworks

- `GET /api/artworks` - Get all artworks (paginated)
- `GET /api/artworks/<id>` - Get single artwork
- `POST /api/artworks` - Create new artwork
- `PUT /api/artworks/<id>` - Update artwork
- `DELETE /api/artworks/<id>` - Delete artwork

### Other

- `GET /api/origins` - Get all origins
- `GET /api/galleries` - Get all galleries
- `GET /api/search` - Search collection
- `GET /api/stats` - Get statistics

## 💡 Usage Examples

### Browse Collection

1. Navigate to "Browse Collection"
2. Select a category (Artworks, Artists, etc.)
3. View items with pagination
4. Click Edit/Delete buttons for actions

### Add Artwork

1. Navigate to "Add Artwork"
2. Select "Artwork" category
3. Fill in the form:
   - Title (required)
   - Object Type (required)
   - Medium, Year, Origin, Gallery (optional)
4. Click "Save Item"

### Add Artist

1. Navigate to "Add Artwork"
2. Select "Artist" category
3. Fill in artist information
4. Click "Save Item"

### Search

1. Navigate to "Search"
2. Select category (optional)
3. Select field to search (optional)
4. Enter search query
5. Choose match type (exact or partial)
6. Click "Search"

## 🐛 Troubleshooting

### Database Connection Error

- Verify MySQL is running
- Check credentials in `config.py`, `app.py`, and `setup_database.py`
- Ensure database `art_museum_db` exists

### Port Already in Use

If port 5000 is busy:

1. Open `app.py`
2. Change `port=5000` to another port (e.g., `port=5001`)
3. Update `API_BASE_URL` in `static/js/main.js` to match

### CORS Error

- Make sure flask-cors is installed: `pip install flask-cors`
- CORS is enabled in `app.py` with `CORS(app)`

### Module Not Found

```powershell
pip install --upgrade -r requirements.txt
```

## 📝 Sample Data

The database comes pre-loaded with:

- **6 Artists**: Claude Monet, Vincent van Gogh, Frida Kahlo, Leonardo da Vinci, Georgia O'Keeffe, Hokusai
- **6 Artworks**: Water Lilies, Starry Night, The Two Fridas, Mona Lisa, Red Canna, The Great Wave
- **6 Origins**: France, Netherlands, Mexico, Italy, USA, Japan
- **6 Galleries**: Different museum departments

## 🔄 Development Tips

### Add New Tables

1. Update `database.sql` with new table schema
2. Add API routes in `app.py`
3. Update frontend JavaScript to handle new data
4. Add form fields in `add_record.js`

### Modify Existing Features

- **Frontend**: Edit HTML/CSS/JS files
- **Backend**: Modify `app.py` routes
- **Database**: Update `database.sql` and re-run `setup_database.py`

## 📦 Deployment

For production deployment:

1. Set `debug=False` in `app.py`
2. Use environment variables for credentials
3. Use a production WSGI server (gunicorn, uWSGI)
4. Set up proper MySQL user with limited permissions
5. Enable HTTPS

## 👥 Authors

SOFE 3700U Final Project - Phase 3

## 📄 License

Educational project for SOFE 3700U course

---

**Need Help?** Check the troubleshooting section or review the API documentation above.
