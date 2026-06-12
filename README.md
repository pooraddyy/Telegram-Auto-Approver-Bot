<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0f0c29,50:302b63,100:24243e&height=220&section=header&text=Auto%20Approve%20Bot&fontSize=58&fontColor=ffffff&fontAlignY=40&desc=Telegram%20Join%20Request%20Automation&descAlignY=62&descSize=17&descColor=a5b4fc&animation=fadeIn" width="100%"/>

<br/>

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Pyrofork](https://img.shields.io/badge/Pyrofork-2.3.68-5B6EF5?style=flat-square&logo=telegram&logoColor=white)](https://github.com/TelegramPlayGround/Pyrofork)
[![MongoDB](https://img.shields.io/badge/MongoDB-Motor-47A248?style=flat-square&logo=mongodb&logoColor=white)](https://mongodb.com)
[![License](https://img.shields.io/badge/License-MIT-64748b?style=flat-square)](LICENSE)

</div>

---

## Overview

**Auto Approve Bot** is a high-performance Telegram bot for automated join request management. handles thousands of requests with zero manual effort.

---

## Features

| Feature | Description |
|---|---|
| Auto Approve | Instantly approves incoming join requests when enabled |
| Per-Chat Toggle | Enable or disable independently per group or channel |
| Bulk Approve | Approves all pending requests via userbot with live progress |
| Stop Control | Cancel bulk approval at any time via inline button |
| Leave Notification | Sends a styled DM with rejoin link when a member leaves |
| Broadcast | Forward any message to all registered bot users |
| Pinned Broadcast | Broadcast and auto-pin in every user's DM |
| Userbot Login | Log in a Telegram account for user-level bulk actions |
| Live Stats | Real-time user count, chat count, and Python version |

---

## Configuration

| Variable | Required | Default | Description |
|---|:---:|---|---|
| `TOKEN` | yes | — | Bot token from @BotFather |
| `API_ID` | yes | — | Integer API ID from my.telegram.org |
| `API_HASH` | yes | — | API hash from my.telegram.org |
| `DB_URL` | yes | — | MongoDB connection URI |
| `DB_NAME` | no | `AutoApproveBot` | MongoDB database name |
| `OWNER_ID` | no | `5938660179` | Your Telegram numeric user ID |
| `START_PHOTO` | no | built-in | Photo shown on `/start` |
| `PING_PHOTO` | no | built-in | Photo shown on `/ping` |
| `PORT` | no | `8080` | Health-check HTTP server port |

```env
TOKEN=your_bot_token
API_ID=12345678
API_HASH=your_api_hash
DB_URL=mongodb+srv://user:pass@cluster.mongodb.net/
DB_NAME=AutoApproveBot
OWNER_ID=your_telegram_id
```

---

## Deploy

**Railway**

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/pooraddyy/Telegram-Auto-Approver-Bot)

**Render**

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/pooraddyy/Telegram-Auto-Approver-Bot)

Set `TOKEN`, `API_ID`, `API_HASH`, `DB_URL`, and `OWNER_ID` in the platform dashboard after deploying.

**Docker**

```bash
git clone https://github.com/pooraddyy/Telegram-Auto-Approver-Bot.git
cd Telegram-Auto-Approver-Bot
cp sample.env .env
docker compose up -d
```

**Manual**

```bash
git clone https://github.com/pooraddyy/Telegram-Auto-Approver-Bot.git
cd Telegram-Auto-Approver-Bot
pip install -r requirements.txt
cp sample.env .env
python main.py
```

---

## Commands

| Command | Access | Scope | Description |
|---|:---:|:---:|---|
| `/start` | all | private | Open the main menu |
| `/ping` | all | anywhere | Latency, uptime, and current time |
| `/autoapprove` | admin | group / channel | Toggle auto-approve on or off |
| `/approve_all` | admin | group / channel | Bulk-approve all pending requests |
| `/leave_noti` | admin | group / channel | Toggle leave notification DMs |
| `/login` | all | private | Connect Telegram account for userbot |
| `/logout` | all | private | Disconnect saved account |
| `/broadcast` | owner | private | Send message to all bot users |
| `/pbroadcast` | owner | private | Broadcast and pin in every DM |
| `/stats` | owner | private | View user, chat, and system stats |
| `/restart` | owner | private | Restart the bot remotely |

---

## Usage

1. Add the bot to your group or channel
2. Promote it as **Administrator** and grant **Invite Users** permission
3. Run `/autoapprove` and press **Enable** to start auto-approving
4. For bulk approval of existing pending requests: `/login` in private, then `/approve_all` in the group or channel

---

## License

[MIT](LICENSE) — maintained by [PythonTodayz](https://t.me/pythontodayz)

<div align="center">
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0f0c29,50:302b63,100:24243e&height=110&section=footer&animation=fadeIn" width="100%"/>
</div>
