# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Bot

To run the Discord bot:
```bash
python main.py
```

The bot requires a `.env` file with `DISCORD_TOKEN` environment variable.

## Dependencies

Install dependencies with:
```bash
pip install -r requirements.txt
```

## Architecture

This is a Discord bot with the following core functionality:

### Role Management System
- Channel ID `1381707666249875496` handles role selection via reaction-based interface
- Users react with emoji (🎮, 🎨) to get corresponding Discord roles
- Bot automatically manages role assignment/removal based on reactions

### Feedback System  
- Channel ID `1381642719557845063` serves as feedback collection channel
- Auto-detects categories from message content using emojis or keywords:
  - 🎮/ゲーム: ゲームプレイ
  - 🐛/バグ: バグ報告  
  - 💡/提案: 新機能提案
  - ❓/質問: 質問
  - 📝/その他: その他
- Creates threaded discussions for each feedback item
- Tracks resolution status with ⏳ (未解決) and ✅ (解決済み) reactions
- Sends notifications to management channel when new feedback is posted

### Configuration
All hardcoded IDs, messages, and mappings are centralized in the `Config` class at the top of `main.py`. When modifying channel IDs, role IDs, or behavior, update the constants in this class.

### Key Functions
- `find_or_create_feedback_message()`: Manages persistent feedback instruction messages
- Event handlers for `on_message`, `on_raw_reaction_add/remove`: Core bot interaction logic