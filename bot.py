import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# Botの設定
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ロールとリアクションの対応関係を定義
ROLE_REACTIONS = {
    '🎮': 'ゲーマー',  # 例: 🎮リアクションで「ゲーマー」ロール
    '🎨': 'アーティスト',  # 例: 🎨リアクションで「アーティスト」ロール
    '🎵': 'ミュージシャン',  # 例: 🎵リアクションで「ミュージシャン」ロール
}

@bot.event
async def on_ready():
    print(f'{bot.user} としてログインしました！')

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    """ロール選択メッセージを設定するコマンド"""
    embed = discord.Embed(
        title="ロール選択",
        description="下のリアクションをクリックして、あなたのロールを選択してください！",
        color=discord.Color.blue()
    )
    
    for emoji, role_name in ROLE_REACTIONS.items():
        embed.add_field(name=role_name, value=f"{emoji} をクリック", inline=False)
    
    message = await ctx.send(embed=embed)
    
    # リアクションを追加
    for emoji in ROLE_REACTIONS.keys():
        await message.add_reaction(emoji)

@bot.event
async def on_raw_reaction_add(payload):
    """リアクションが追加されたときの処理"""
    # Botのリアクションは無視
    if payload.user_id == bot.user.id:
        return
    
    # メッセージがBotのメッセージでない場合は無視
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    if message.author != bot.user:
        return
    
    # リアクションに対応するロールを取得
    emoji = str(payload.emoji)
    if emoji not in ROLE_REACTIONS:
        return
    
    role_name = ROLE_REACTIONS[emoji]
    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    
    # ロールを取得して付与
    role = discord.utils.get(guild.roles, name=role_name)
    if role:
        await member.add_roles(role)
        await member.send(f"{role_name}ロールを付与しました！")

@bot.event
async def on_raw_reaction_remove(payload):
    """リアクションが削除されたときの処理"""
    # Botのリアクションは無視
    if payload.user_id == bot.user.id:
        return
    
    # メッセージがBotのメッセージでない場合は無視
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    if message.author != bot.user:
        return
    
    # リアクションに対応するロールを取得
    emoji = str(payload.emoji)
    if emoji not in ROLE_REACTIONS:
        return
    
    role_name = ROLE_REACTIONS[emoji]
    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    
    # ロールを取得して削除
    role = discord.utils.get(guild.roles, name=role_name)
    if role:
        await member.remove_roles(role)
        await member.send(f"{role_name}ロールを削除しました！")

# Botを起動
bot.run(os.getenv('DISCORD_TOKEN')) 