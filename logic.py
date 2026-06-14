import sqlite3
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

class DB_Map:
    def __init__(self, database):
        self.database = database
        self.create_user_table()  # Otomatis buat tabel saat inisialisasi

    def _get_conn(self):
        conn = sqlite3.connect(self.database)
        conn.row_factory = sqlite3.Row
        return conn

    def create_user_table(self):
        with self._get_conn() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS users_cities (
                                user_id INTEGER,
                                city_id TEXT,
                                FOREIGN KEY(city_id) REFERENCES cities(id)
                            )''')
            conn.commit()

    def add_city(self, user_id, city_name):
        if not city_name or not city_name.strip():
            return False
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM cities WHERE LOWER(city)=LOWER(?)", (city_name.strip(),))
            city_data = cursor.fetchone()
            if city_data:
                # Cek duplikat
                cursor.execute("SELECT * FROM users_cities WHERE user_id=? AND city_id=?", 
                               (user_id, city_data['id']))
                if cursor.fetchone():
                    return 2  # Sudah ada
                conn.execute('INSERT INTO users_cities VALUES (?, ?)', (user_id, city_data['id']))
                conn.commit()
                return True
            return False

    def select_cities(self, user_id):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT cities.city, cities.lat, cities.lng
                            FROM users_cities  
                            JOIN cities ON users_cities.city_id = cities.id
                            WHERE users_cities.user_id = ?''', (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_coordinates(self, city_name):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT lat, lng FROM cities WHERE LOWER(city)=LOWER(?)", (city_name.strip(),))
            row = cursor.fetchone()
            return (row['lat'], row['lng']) if row else None

    @staticmethod
    def _haversine(lat1, lon1, lat2, lon2):
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
            math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))

    def draw_distance(self, ax, city1_coords, city2_coords):
        """Menggambar garis antara dua kota + label jarak"""
        lat1, lon1 = city1_coords
        lat2, lon2 = city2_coords
        distance = self._haversine(lat1, lon1, lat2, lon2)
        
        ax.plot([lon1, lon2], [lat1, lat2], 'r-', linewidth=2, 
                transform=ccrs.PlateCarree())
        mid_lat = (lat1 + lat2) / 2
        mid_lon = (lon1 + lon2) / 2
        ax.text(mid_lon, mid_lat, f'{distance:.0f} km',
                fontsize=9, color='red', fontweight='bold',
                transform=ccrs.PlateCarree(),
                ha='center', va='bottom')

    def create_graph(self, path, cities):
        """
        cities: list of dict [{'city': name, 'lat': x, 'lng': y}, ...]
        """
        if not cities:
            return None

        fig, ax = plt.subplots(figsize=(10, 8), subplot_kw={'projection': ccrs.PlateCarree()})
        ax.set_global()
        ax.add_feature(cfeature.LAND)
        ax.add_feature(cfeature.OCEAN)
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.BORDERS, linestyle=':')

        coords = []
        for c in cities:
            ax.plot(c['lng'], c['lat'], 'bo', markersize=8, transform=ccrs.PlateCarree())
            ax.text(c['lng'] + 1, c['lat'] + 1, c['city'],
                    fontsize=10, transform=ccrs.PlateCarree(),
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
            coords.append((c['lat'], c['lng']))

        # Gambar garis antar semua pasangan kota
        for i in range(len(coords)):
            for j in range(i+1, len(coords)):
                self.draw_distance(ax, coords[i], coords[j])

        plt.tight_layout()
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return path