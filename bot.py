import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime
import asyncio

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

# 解決状態のスタンプ
RESOLUTION_REACTIONS = {
    '⏳': '未解決',
    '✅': '解決済み'
}

# 説明メッセージの内容
FEEDBACK_DESCRIPTION = (
    "このチャンネルで意見や質問を投稿できます。\n\n"
    "**カテゴリ一覧：**\n"
    "🎮 ゲームプレイ\n"
    "🐛 バグ報告\n"
    "💡 新機能提案\n"
    "❓ 質問\n"
    "📝 その他\n\n"
    "メッセージ内にカテゴリの絵文字や文字列が含まれていると、\n"
    "自動的にそのカテゴリとして認識され、スレッドが作成されます。\n"
    "例：`🎮 ゲームの操作方法について` または `ゲーム 操作方法について`\n\n"
    "**解決状態の管理：**\n"
    "⏳ 未解決\n"
    "✅ 解決済み\n"
    "これらのスタンプをクリックすることで、解決状態を切り替えることができます。"
)

async def find_or_create_feedback_message(channel):
    """説明メッセージを探すか、なければ作成する"""
    async for message in channel.history(limit=100):
        if message.author == bot.user and message.embeds and message.embeds[0].title == "ご意見箱":
            return message
    
    # メッセージが見つからない場合は新規作成
    embed = discord.Embed(
        title="ご意見箱",
        description=FEEDBACK_DESCRIPTION,
        color=discord.Color.green()
    )
    return await channel.send(embed=embed)

@bot.event
async def on_ready():
    print(f'{bot.user} としてログインしました！')
    
    # ロール選択メッセージの投稿
    role_channel = bot.get_channel(ROLE_CHANNEL_ID)
    if role_channel:
        # 既存のメッセージを探す
        async for message in role_channel.history(limit=100):
            if message.author == bot.user and message.embeds and message.embeds[0].title == "ロール選択":
                # 既存のメッセージが見つかった場合、リアクションを確認
                for emoji in ROLE_REACTIONS.keys():
                    if not any(reaction.emoji == emoji for reaction in message.reactions):
                        await message.add_reaction(emoji)
                break
        else:
            # メッセージが見つからない場合は新規作成
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
    
    # ご意見箱の説明メッセージを投稿または再利用
    feedback_channel = bot.get_channel(FEEDBACK_CHANNEL_ID)
    if feedback_channel:
        await find_or_create_feedback_message(feedback_channel)

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
            # スレッドを作成
            thread_name = f"{detected_category} - {datetime.now().strftime('%Y/%m/%d')}"
            thread = await message.create_thread(name=thread_name)
            
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
                embed.add_field(name="スレッド", value=f"[リンク]({thread.jump_url})", inline=True)
                await notification_channel.send(embed=embed)
            
            # メッセージにカテゴリの確認を追加
            await message.add_reaction('✅')
            
            # スレッド内に受け付けメッセージを投稿
            await thread.send(f"✅ {detected_category}として受け付けました")
            
            # 解決状態のスタンプを追加（初期状態は未解決）
            await message.add_reaction('⏳')
    
    await bot.process_commands(message)

@bot.event
async def on_raw_reaction_add(payload):
    """リアクションが追加されたときの処理"""
    # Botのリアクションは無視
    if payload.user_id == bot.user.id:
        return
    
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    
    # ロール選択のリアクション処理
    if message.author == bot.user and message.embeds and message.embeds[0].title == "ロール選択":
        emoji = str(payload.emoji)
        if emoji in ROLE_REACTIONS:
            role_id = ROLE_REACTIONS[emoji]
            guild = bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            
            # ロールを取得して付与
            role = guild.get_role(role_id)
            if role:
                await member.add_roles(role)
                # 一時的な通知メッセージを送信
                temp_message = await channel.send(f"{member.mention} に {role.name}ロールを付与しました！")
                await asyncio.sleep(10)  # 10秒待機
                await temp_message.delete()  # メッセージを削除
    
    # 解決状態のリアクション処理
    elif message.channel.id == FEEDBACK_CHANNEL_ID:
        emoji = str(payload.emoji)
        if emoji in RESOLUTION_REACTIONS:
            # 現在の解決状態を確認
            current_state = '⏳' if any(r.emoji == '⏳' for r in message.reactions) else '✅'
            new_state = '✅' if current_state == '⏳' else '⏳'
            
            # ユーザーのリアクションを削除
            await message.remove_reaction(emoji, payload.member)
            
            # 古いリアクションを削除
            await message.remove_reaction(current_state, bot.user)
            # 新しいリアクションを追加
            await message.add_reaction(new_state)

@bot.event
async def on_raw_reaction_remove(payload):
    """リアクションが削除されたときの処理"""
    # Botのリアクションは無視
    if payload.user_id == bot.user.id:
        return
    
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    
    # ロール選択のリアクション処理
    if message.author == bot.user and message.embeds and message.embeds[0].title == "ロール選択":
        emoji = str(payload.emoji)
        if emoji in ROLE_REACTIONS:
            role_id = ROLE_REACTIONS[emoji]
            guild = bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            
            # ロールを取得して削除
            role = guild.get_role(role_id)
            if role:
                await member.remove_roles(role)
                # 一時的な通知メッセージを送信
                temp_message = await channel.send(f"{member.mention} から {role.name}ロールを削除しました！")
                await asyncio.sleep(10)  # 10秒待機
                await temp_message.delete()  # メッセージを削除

# Botを起動
bot.run(os.getenv('DISCORD_TOKEN')) 