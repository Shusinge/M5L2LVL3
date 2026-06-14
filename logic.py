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

    @staticmethod
    def _get_non_overlapping_position(ax, x, y, existing_boxes, offset_candidates=None):
        """
        Mencari posisi label yang tidak bertabrakan dengan elemen lain.
        Mengembalikan (x_baru, y_baru) dalam data coordinates.
        """
        if offset_candidates is None:
            # 8 arah pencarian: atas, bawah, kiri, kanan, dan 4 diagonal
            offsets = [
                (0, 2), (0, -2), (2, 0), (-2, 0),
                (1.5, 1.5), (-1.5, 1.5), (1.5, -1.5), (-1.5, -1.5)
            ]
        else:
            offsets = offset_candidates

        renderer = ax.figure.canvas.get_renderer()
        
        for dx, dy in offsets:
            test_x, test_y = x + dx, y + dy
            # Buat bounding box teks di posisi kandidat
            temp_text = ax.text(test_x, test_y, "test", transform=ccrs.PlateCarree())
            bb = temp_text.get_window_extent(renderer=renderer)
            temp_text.remove()
            
            # Cek apakah bertabrakan dengan box yang sudah ada
            overlap = False
            for existing_bb in existing_boxes:
                if bb.overlaps(existing_bb):
                    overlap = True
                    break
            
            if not overlap:
                return test_x, test_y, bb
        
        # Fallback: gunakan posisi asli jika semua kandidat tabrakan
        fallback_text = ax.text(x, y, "test", transform=ccrs.PlateCarree())
        bb = fallback_text.get_window_extent(renderer=renderer)
        fallback_text.remove()
        return x, y, bb

    def draw_distance(self, ax, city1_coords, city2_coords, existing_boxes):
        """Menggambar garis + label jarak yang tidak bertabrakan"""
        lat1, lon1 = city1_coords
        lat2, lon2 = city2_coords
        distance = self._haversine(lat1, lon1, lat2, lon2)
        
        # Gambar garis penghubung
        ax.plot([lon1, lon2], [lat1, lat2], 'r-', linewidth=1.5, 
                alpha=0.7, transform=ccrs.PlateCarree())
        
        # Titik tengah garis sebagai posisi awal label
        mid_lat = (lat1 + lat2) / 2
        mid_lon = (lon1 + lon2) / 2
        
        # Cari posisi yang tidak bertabrakan
        safe_lon, safe_lat, bbox = self._get_non_overlapping_position(
            ax, mid_lon, mid_lat, existing_boxes
        )
        
        # Gambar label di posisi aman
        label = ax.text(
            safe_lon, safe_lat, f'{distance:.0f} km',
            fontsize=8, color='darkred', fontweight='bold',
            transform=ccrs.PlateCarree(),
            ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', 
                      edgecolor='lightgray', alpha=0.9)
        )
        
        # Daftarkan bounding box label ini agar label berikutnya menghindarinya
        renderer = ax.figure.canvas.get_renderer()
        existing_boxes.append(label.get_window_extent(renderer=renderer))

    def create_graph(self, path, cities):
        if not cities:
            return None

        fig, ax = plt.subplots(figsize=(12, 9), subplot_kw={'projection': ccrs.PlateCarree()})
        ax.set_global()
        ax.add_feature(cfeature.LAND, facecolor='#f0f0f0')
        ax.add_feature(cfeature.OCEAN, facecolor='#d4e6f1')
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
        ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.3)

        coords = []
        existing_boxes = []  # ← Tracker semua elemen yang sudah digambar
        renderer = fig.canvas.get_renderer()

        # Gambar marker & nama kota dulu (prioritas tertinggi)
        for c in cities:
            marker, = ax.plot(c['lng'], c['lat'], 'bo', markersize=8, 
                              transform=ccrs.PlateCarree())
            existing_boxes.append(marker.get_window_extent(renderer=renderer))
            
            city_label = ax.text(
                c['lng'] + 1.5, c['lat'] + 1.5, c['city'],
                fontsize=10, fontweight='bold',
                transform=ccrs.PlateCarree(),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.9)
            )
            existing_boxes.append(city_label.get_window_extent(renderer=renderer))
            coords.append((c['lat'], c['lng']))

        # Gambar garis jarak DENGAN anti-tabrakan
        for i in range(len(coords)):
            for j in range(i + 1, len(coords)):
                self.draw_distance(ax, coords[i], coords[j], existing_boxes)

        plt.tight_layout()
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return path
    
    def delete_city(self, user_id, city_name):
        """Menghapus kota dari daftar user. Return: True=berhasil, False=tidak ditemukan"""
        if not city_name or not city_name.strip():
            return False
        with self._get_conn() as conn:
            cursor = conn.cursor()
            # Cari city_id berdasarkan nama (case insensitive)
            cursor.execute("SELECT id FROM cities WHERE LOWER(city)=LOWER(?)", (city_name.strip(),))
            city_data = cursor.fetchone()
            if not city_data:
                return None  # Kota tidak ada di database sama sekali
            
            # Hapus relasi user-kota
            cursor.execute(
                "DELETE FROM users_cities WHERE user_id=? AND city_id=?",
                (user_id, city_data['id'])
            )
            conn.commit()
            return cursor.rowcount > 0  # True jika baris berhasil dihapus

    def search_cities(self, keyword, limit=10):
        """Cari kota dengan kata kunci parsial. Return list of dict"""
        if not keyword or not keyword.strip():
            return []
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT city, lat, lng FROM cities WHERE LOWER(city) LIKE LOWER(?) LIMIT ?",
                (f"%{keyword.strip()}%", limit)
            )
            return [dict(row) for row in cursor.fetchall()]