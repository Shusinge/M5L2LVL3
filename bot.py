import os
import discord
from discord.ext import commands
from config import TOKEN
from logic import DB_Map

manager = DB_Map("database.db")
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

MAP_DIR = "maps"
os.makedirs(MAP_DIR, exist_ok=True)


@bot.event
async def on_ready():
    print(f"✅ Bot started as {bot.user}")


@bot.command()
async def start(ctx: commands.Context):
    await ctx.send(
        f"Halo, **{ctx.author.name}**! 👋\n"
        "Ketik `!help_me` untuk melihat daftar perintah yang tersedia."
    )


@bot.command()
async def help_me(ctx: commands.Context):
    embed = discord.Embed(title="📖 Daftar Perintah", color=discord.Color.blue())
    embed.add_field(name="!start", value="Sapaan awal", inline=False)
    embed.add_field(name="!remember_city <nama_kota>", value="Simpan kota ke daftar kamu (bahasa Inggris)", inline=False)
    embed.add_field(name="!show_my_cities", value="Tampilkan peta semua kota yang kamu simpan", inline=False)
    embed.add_field(name="!show_city <nama_kota>", value="Tampilkan peta satu kota tertentu", inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def show_city(ctx: commands.Context, *, city_name: str = ""):
    if not city_name.strip():
        await ctx.send("⚠️ Masukkan nama kota! Contoh: `!show_city Jakarta`")
        return

    coords = manager.get_coordinates(city_name)
    if not coords:
        await ctx.send(f"❌ Kota **{city_name}** tidak ditemukan dalam database.")
        return

    path = os.path.join(MAP_DIR, f"{ctx.author.id}_{city_name.replace(' ', '_')}.png")
    city_data = [{'city': city_name, 'lat': coords[0], 'lng': coords[1]}]
    manager.create_graph(path, city_data)

    await ctx.send(f"🗺️ Peta **{city_name}**:", file=discord.File(path))


@bot.command()
async def show_my_cities(ctx: commands.Context):
    cities = manager.select_cities(ctx.author.id)
    if not cities:
        await ctx.send("📭 Kamu belum menyimpan kota apa pun. Gunakan `!remember_city <nama_kota>` terlebih dahulu.")
        return

    path = os.path.join(MAP_DIR, f"{ctx.author.id}_my_cities.png")
    manager.create_graph(path, cities)

    city_names = ", ".join(c['city'] for c in cities)
    await ctx.send(f"🗺️ Peta kota-kotamu (**{city_names}**):", file=discord.File(path))


@bot.command()
async def remember_city(ctx: commands.Context, *, city_name: str = ""):
    if not city_name.strip():
        await ctx.send("⚠️ Format: `!remember_city <nama_kota>` (dalam bahasa Inggris)")
        return

    result = manager.add_city(ctx.author.id, city_name)
    if result is True:
        await ctx.send(f"✅ Kota **{city_name}** berhasil disimpan!")
    elif result == 2:
        await ctx.send(f"ℹ️ Kota **{city_name}** sudah ada di daftar kamu.")
    else:
        await ctx.send(f"❌ Kota **{city_name}** tidak ditemukan. Pastikan nama kota dalam bahasa Inggris dan ejaan benar.")


if __name__ == "__main__":
    bot.run(TOKEN)