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

# チャンネルIDとロールIDの設定
ROLE_CHANNEL_ID = 1381707666249875496
ROLE_REACTIONS = {
    '🎮': 1381708151891562690,  # 1つ目のロールID
    '🎨': 1381708218639581355,  # 2つ目のロールID
}

@bot.event
async def on_ready():
    print(f'{bot.user} としてログインしました！')
    
    # 指定されたチャンネルにメッセージを投稿
    channel = bot.get_channel(ROLE_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="ロール選択",
            description="下のリアクションをクリックして、あなたのロールを選択してください！",
            color=discord.Color.blue()
        )
        
        for emoji, role_id in ROLE_REACTIONS.items():
            role = channel.guild.get_role(role_id)
            if role:
                embed.add_field(name=role.name, value=f"{emoji} をクリック", inline=False)
        
        message = await channel.send(embed=embed)
        
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
    
    role_id = ROLE_REACTIONS[emoji]
    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    
    # ロールを取得して付与
    role = guild.get_role(role_id)
    if role:
        await member.add_roles(role)
        await member.send(f"{role.name}ロールを付与しました！")

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
    
    role_id = ROLE_REACTIONS[emoji]
    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    
    # ロールを取得して削除
    role = guild.get_role(role_id)
    if role:
        await member.remove_roles(role)
        await member.send(f"{role.name}ロールを削除しました！")

# Botを起動
bot.run(os.getenv('DISCORD_TOKEN')) 