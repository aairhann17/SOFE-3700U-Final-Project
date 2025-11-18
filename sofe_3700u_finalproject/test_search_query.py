import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='softEng@2028',
    database='art_museum_db',
    cursorclass=pymysql.cursors.DictCursor
)
cur = conn.cursor()

# Simulate empty search (should return all records)
category = 'artworks'
field = ''
query = ''
match_type = 'partial'

allowed = {'Title', 'Medium', 'ObjectType', 'YearCreated'}
use_field = field if field in allowed else 'Title'

sql = '''
    SELECT od.*, oo.Country, ogd.GalleryName
    FROM ObjectDetails od
    LEFT JOIN ObjectOrigins oo ON od.OriginID = oo.OriginID
    LEFT JOIN ObjectGalleryData ogd ON od.GalleryID = ogd.GalleryID
    WHERE 1=1
'''
params = []

print(f'Query param: "{query}"')
print(f'Use field: {use_field}')

if query:
    sql += f' AND {use_field} LIKE %s'
    params.append(f'%{query}%')
    
sql += ' ORDER BY od.Title LIMIT 25 OFFSET 0'

print(f'\nSQL:\n{sql}')
print(f'\nParams: {params}')

cur.execute(sql, params)
results = cur.fetchall()

print(f'\n✓ Results: {len(results)} records')
for r in results[:3]:
    print(f"  - {r['ObjectID']}: {r['Title']} ({r['Medium']})")

cur.close()
conn.close()
