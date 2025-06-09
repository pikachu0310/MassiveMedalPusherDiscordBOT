import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime

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
FEEDBACK_CHANNEL_ID = 1381642719557845063
NOTIFICATION_CHANNEL_ID = 1381707666249875496

ROLE_REACTIONS = {
    '🎮': 1381708151891562690,  # 1つ目のロールID
    '🎨': 1381708218639581355,  # 2つ目のロールID
}

# 意見のカテゴリ
FEEDBACK_CATEGORIES = {
    '🎮': 'ゲームプレイ',
    '🐛': 'バグ報告',
    '💡': '新機能提案',
    '❓': '質問',
    '📝': 'その他',
    # テキストベースのカテゴリも追加
    'ゲーム': 'ゲームプレイ',
    'バグ': 'バグ報告',
    '提案': '新機能提案',
    '質問': '質問',
    'その他': 'その他'
}

@bot.event
async def on_ready():
    print(f'{bot.user} としてログインしました！')
    
    # ロール選択メッセージの投稿
    role_channel = bot.get_channel(ROLE_CHANNEL_ID)
    if role_channel:
        embed = discord.Embed(
            title="ロール選択",
            description="下のリアクションをクリックして、あなたのロールを選択してください！",
            color=discord.Color.blue()
        )
        
        for emoji, role_id in ROLE_REACTIONS.items():
            role = role_channel.guild.get_role(role_id)
            if role:
                embed.add_field(name=role.name, value=f"{emoji} をクリック", inline=False)
        
        message = await role_channel.send(embed=embed)
        
        # リアクションを追加
        for emoji in ROLE_REACTIONS.keys():
            await message.add_reaction(emoji)
    
    # ご意見箱の説明メッセージを投稿
    feedback_channel = bot.get_channel(FEEDBACK_CHANNEL_ID)
    if feedback_channel:
        embed = discord.Embed(
            title="ご意見箱",
            description=(
                "このチャンネルで意見や質問を投稿できます。\n\n"
                "**カテゴリ一覧：**\n"
                "🎮 ゲームプレイ\n"
                "🐛 バグ報告\n"
                "💡 新機能提案\n"
                "❓ 質問\n"
                "📝 その他\n\n"
                "メッセージ内にカテゴリの絵文字や文字列が含まれていると、\n"
                "自動的にそのカテゴリとして認識されます。\n"
                "例：`🎮 ゲームの操作方法について` または `ゲーム 操作方法について`"
            ),
            color=discord.Color.green()
        )
        await feedback_channel.send(embed=embed)

@bot.event
async def on_message(message):
    # Botのメッセージは無視
    if message.author.bot:
        return
    
    # ご意見箱チャンネルのメッセージを処理
    if message.channel.id == FEEDBACK_CHANNEL_ID:
        content = message.content.strip()
        
        # カテゴリの検出
        detected_category = None
        for emoji, category in FEEDBACK_CATEGORIES.items():
            if emoji in content or category in content:
                detected_category = category
                break
        
        if detected_category:
            # 運営への通知
            notification_channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
            if notification_channel:
                embed = discord.Embed(
                    title="新しい意見が投稿されました",
                    description=content,
                    color=discord.Color.blue()
                )
                embed.add_field(name="カテゴリ", value=detected_category, inline=True)
                embed.add_field(name="投稿者", value=message.author.mention, inline=True)
                embed.add_field(name="メッセージ", value=f"[リンク]({message.jump_url})", inline=True)
                await notification_channel.send(embed=embed)
            
            # メッセージにカテゴリの確認を追加
            await message.add_reaction('✅')
            await message.reply(f"✅ {detected_category}として受け付けました", mention_author=False)
    
    await bot.process_commands(message)

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