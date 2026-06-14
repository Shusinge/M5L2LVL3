# Bot Peta

Proyek ini adalah bot yang memungkinkan pengguna untuk menampilkan kota tertentu pada peta dan untuk menyimpan kota untuk ditampilkan lebih lanjut.

## Fitur Utama

- **Menampilkan kota pada peta**: Bot dapat menampilkan kota yang dipilih pada peta menggunakan library Cartopy dan Matplotlib.
- **Menyimpan kota**: Pengguna dapat menyimpan kota yang mereka ingin lihat ke daftar pribadi mereka.
- **Menampilkan kota yang disimpan**: Saat diminta, bot dapat menampilkan daftar semua kota yang disimpan oleh pengguna.

## Teknologi

- **Python 3**: Bahasa pemrograman.
- **SQLite**: Database untuk menyimpan informasi pengguna dan kota.
- **Matplotlib dan Cartopy**: Library untuk membuat representasi data grafis.
- **Discord.py**: Library untuk membuat dan mengelola bot.

## Instalasi dan Pengaturan

1. **Kloning repository:**
    ```bash
    git clone <url_to_repository>
    cd <repository_name>
    ```
2. **Instalasi dependensi:**
    ```bash
    pip install -r requirements.txt
    ```
3. **Konfigurasi variabel lingkungan:**
    Buka file `config.py` di root proyek dan setel variabel yang diperlukan:
    ```bash
    TOKEN=<your_bot_token>
    ```
4. **Menjalankan bot:**
    ```bash
    python bot.py
    ```

## Daftar perintah bot

- `!start` - mulai bekerja dengan bot dan menerima pesan selamat datang.\n"
- `!help_me` - menerima daftar perintah yang tersedia\n"
- `!show_city <city_name>` - menampilkan kota yang diberikan pada peta.\n"
- `!remember_city <city_name>` - menghafal kota yang diberikan.\n"
- `!show_my_cities` - menampilkan semua kota yang dihafal."
        
