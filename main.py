import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime
import asyncio

# 環境変数の読み込み
load_dotenv()

# Botの設定
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# 定数定義
class Config:
    # チャンネルID
    ROLE_CHANNEL_ID = 1381638244005052466  # サーバールールチャンネル
    FEEDBACK_CHANNEL_ID = 1381642719557845063
    NOTIFICATION_CHANNEL_ID = 1381707666249875496

    # ロール設定（本番用）
    GENERAL_ROLE_ID = 1381643598126387281  # 一般ロール（参加者用）

    # 意見のカテゴリ
    FEEDBACK_CATEGORIES = {
        '🎮': 'ゲームプレイ',
        '🐛': 'バグ報告',
        '💡': '新機能提案',
        '❓': '質問',
        '📝': 'その他',
        # テキストベースのカテゴリ
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

    # 説明メッセージ
    FEEDBACK_DESCRIPTION = (
        "このチャンネルで気軽に意見や質問を投稿しよう！\n\n"
        "## 使い方\n"
        "メッセージ内にカテゴリの絵文字や文字列が含まれていると、\n"
        "自動的にそのカテゴリとして認識され、スレッドが作成されるので、\n"
        "そのスレッド内に内容を書いてください。スレッド内で返信いたします。\n"
        "例1: `質問 シャルベを救った回数って何ですか？`\n"
        "例2: `💡 シャルベボールの残り数を表示すると良さそう！`\n\n"
        "**カテゴリ一覧：**\n"
        "🎮 ゲームプレイ\n"
        "🐛 バグ報告\n"
        "💡 新機能提案\n"
        "❓ 質問\n"
        "📝 その他\n\n"
        "また、スタンプをクリックすることで、解決状態を切り替えることができます。(⏳ 未解決 / ✅ 解決済み)\n"
        "(このメッセージは常に一番下に表示されます)"
    )

async def find_or_create_feedback_message(channel):
    """説明メッセージを探すか、なければ作成する"""
    async for message in channel.history(limit=100):
        if message.author == bot.user and message.embeds and message.embeds[0].title == "ご意見箱":
            return message
    
    # メッセージが見つからない場合は新規作成
    embed = discord.Embed(
        title="ご意見箱",
        description=Config.FEEDBACK_DESCRIPTION,
        color=discord.Color.green()
    )
    return await channel.send(embed=embed)

async def recreate_feedback_message(channel):
    """既存のフィードバックメッセージを削除して新しいものを作成する"""
    # 既存のフィードバックメッセージを探して削除
    async for message in channel.history(limit=100):
        if message.author == bot.user and message.embeds and message.embeds[0].title == "ご意見箱":
            await message.delete()
            break
    
    # 新しいフィードバックメッセージを作成
    embed = discord.Embed(
        title="ご意見箱",
        description=Config.FEEDBACK_DESCRIPTION,
        color=discord.Color.green()
    )
    await channel.send(embed=embed)

@bot.event
async def on_ready():
    """Bot起動時の処理"""
    print(f'{bot.user} としてログインしました！')
    
    # サーバー参加用メッセージの投稿
    role_channel = bot.get_channel(Config.ROLE_CHANNEL_ID)
    if role_channel:
        # 既存のメッセージを探す
        async for message in role_channel.history(limit=100):
            if message.author == bot.user and message.embeds and message.embeds[0].title == "サーバー参加":
                # 既存のメッセージが見つかった場合、リアクションを確認
                if not any(reaction.emoji == '✅' for reaction in message.reactions):
                    await message.add_reaction('✅')
                break
        else:
            # メッセージが見つからない場合は新規作成
            embed = discord.Embed(
                title="サーバー参加",
                description="上記のルールを確認の上、下のリアクションを押してサーバーへご参加ください\n\nPlease check the above rules and press the reaction below to join the server!",
                color=discord.Color.green()
            )
            
            general_role = role_channel.guild.get_role(Config.GENERAL_ROLE_ID)
            if general_role:
                embed.add_field(name="参加後に付与されるロール / Role to be assigned", value=f"✅ {general_role.name}", inline=False)
            
            message = await role_channel.send(embed=embed)
            
            # リアクションを追加
            await message.add_reaction('✅')
    
    # ご意見箱の説明メッセージを投稿または再利用
    feedback_channel = bot.get_channel(Config.FEEDBACK_CHANNEL_ID)
    if feedback_channel:
        await find_or_create_feedback_message(feedback_channel)

@bot.event
async def on_message(message):
    """メッセージ受信時の処理"""
    # Botのメッセージは無視
    if message.author.bot:
        return
    
    # ご意見箱チャンネルのメッセージを処理
    if message.channel.id == Config.FEEDBACK_CHANNEL_ID:
        content = message.content.strip()
        
        # カテゴリの検出
        detected_category = None
        for emoji, category in Config.FEEDBACK_CATEGORIES.items():
            if emoji in content or category in content:
                detected_category = category
                break
        
        if detected_category:
            # スレッドを作成
            thread_name = f"{detected_category} - {datetime.now().strftime('%Y/%m/%d')}"
            thread = await message.create_thread(name=thread_name)
            
            # 運営への通知
            notification_channel = bot.get_channel(Config.NOTIFICATION_CHANNEL_ID)
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
            
            # スレッド内に受け付けメッセージを投稿
            await thread.send(f"✅{detected_category}として受け付けました")
            
            # 解決状態のスタンプを追加（初期状態は未解決）
            await message.add_reaction('⏳')
            
            # フィードバックメッセージを再作成（一番下に表示されるように）
            await recreate_feedback_message(message.channel)
    
    await bot.process_commands(message)

@bot.event
async def on_raw_reaction_add(payload):
    """リアクション追加時の処理"""
    # Botのリアクションは無視
    if payload.user_id == bot.user.id:
        return
    
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    
    # サーバー参加のリアクション処理
    if message.author == bot.user and message.embeds and message.embeds[0].title == "サーバー参加":
        emoji = str(payload.emoji)
        if emoji == '✅':
            guild = bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            
            # 一般ロールを取得して付与
            role = guild.get_role(Config.GENERAL_ROLE_ID)
            if role and role not in member.roles:
                await member.add_roles(role)
                # 一時的な通知メッセージを送信
                temp_message = await channel.send(f"✅{member.mention} さん、サーバーへようこそ！{role.name}ロールを付与しました！\nWelcome to the server! {role.name} role has been assigned!")
                await asyncio.sleep(15)  # 15秒待機
                await temp_message.delete()  # メッセージを削除
    
    # 解決状態のリアクション処理
    elif message.channel.id == Config.FEEDBACK_CHANNEL_ID:
        emoji = str(payload.emoji)
        if emoji in Config.RESOLUTION_REACTIONS:
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
    """リアクション削除時の処理"""
    # Botのリアクションは無視
    if payload.user_id == bot.user.id:
        return
    
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    
    # サーバー参加のリアクション削除処理（ロール削除はしない）
    if message.author == bot.user and message.embeds and message.embeds[0].title == "サーバー参加":
        emoji = str(payload.emoji)
        if emoji == '✅':
            # リアクション削除時は特に何もしない（一度参加したらロールは維持）
            pass

def main():
    """メイン関数"""
    bot.run(os.getenv('DISCORD_TOKEN'))

if __name__ == "__main__":
    main() 