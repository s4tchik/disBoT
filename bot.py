import discord
from discord.ext import commands, tasks
import youtube_dl
import os
import asyncio

intents = discord.Intents.all()  # Включаем все разрешения
bot = commands.Bot(command_prefix="!", intents=intents)

# === Функция приветствия ===
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="general")
    if channel:
        await channel.send(f"Добро пожаловать на сервер, {member.mention}! Прочитай правила и наслаждайся общением.")

# === Функции модерации ===
@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f'Пользователь {member} был забанен по причине: {reason}.')

@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f'Пользователь {member} был кикнут по причине: {reason}.')

# === Настройка музыкального проигрывателя ===
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'default_search': 'auto'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        
        if 'entries' in data:
            data = data['entries'][0]
        
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

@bot.command(name='play')
async def play(ctx, url):
    # Проверяем, подключен ли бот
    if ctx.author.voice:
        voice_channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await voice_channel.connect()
    
    # Воспроизведение аудио
    # async with ctx.text():
        try:
            player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print(f'Ошибка: {e}') if e else None)
            await ctx.send(f'Сейчас играет: {player.data["title"]}')
        except Exception as e:
            await ctx.send(f"Ошибка при воспроизведении: {str(e)}")
            print(e)

# Команда для отключения от голосового канала
@bot.command(name='leave')
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()

# === Уведомления ===
@tasks.loop(minutes=1)
async def scheduled_announcement():
    channel = discord.utils.get(bot.get_all_channels(), name="announcements")
    if channel:
        await channel.send("Не забывайте сегодня ваш последний день! https://solo.to/sat4ik Здесь кайф")

@bot.command(name="start_announcement")
@commands.has_permissions(administrator=True)
async def start_announcement(ctx):
    scheduled_announcement.start()
    await ctx.send("Уведомления запущены!")

@bot.command(name="stop_announcement")
@commands.has_permissions(administrator=True)
async def stop_announcement(ctx):
    scheduled_announcement.stop()
    await ctx.send("Уведомления остановлены.")

# === Мини-игра: Ответ на команду с приветствием ===
@bot.command(name="hello")
async def hello(ctx):
    await ctx.send(f"Привет, {ctx.author.mention}! мин нет?")

# === Команды управления ролями ===
@bot.command(name="add_role")
@commands.has_permissions(manage_roles=True)
async def add_role(ctx, role: discord.Role, member: discord.Member):
    await member.add_roles(role)
    await ctx.send(f"Роль {role.name} добавлена пользователю {member.mention}.")

@bot.command(name="remove_role")
@commands.has_permissions(manage_roles=True)
async def remove_role(ctx, role: discord.Role, member: discord.Member):
    await member.remove_roles(role)
    await ctx.send(f"Роль {role.name} удалена у пользователя {member.mention}.")


# === Запуск бота ===
TOKEN = ""  # Замените на ваш токен
bot.run(TOKEN)
