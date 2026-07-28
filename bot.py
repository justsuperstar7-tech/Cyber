import os
import logging
import json
import random
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# ============================================
# 🔥 CONFIG - YAHAN NAYA TOKEN DAALO
# ============================================

# ⚠️ YAHAN @BotFather SE MILA NAYA TOKEN DAALO
BOT_TOKEN = "8907822126:AAHYCaMf10hA75j5yxUQWHt8D-RqfnduVEU"  # <-- CHANGE KARO

MAIN_ADMIN = 8603893462
CO_ADMINS = [7659172575]
ADMIN_IDS = [8603893462, 7659172575]
GROUP_USERNAME = "@CertifiedDeal"
POWERED_BY = "@cyber_amit"
BOT_NAME = "✨ CYBER ESCROW BOT ✨"

# ============================================
# DATABASE
# ============================================

DATA_FILE = "escrow_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {
        "users": {},
        "banned_users": [],
        "warnings": {},
        "co_admins": [7659172575],
        "global_stats": {
            "total_deals": 0,
            "total_volume": {"TON": 0, "USDT": 0, "INR": 0}
        },
        "pending_deals": [],
        "completed_deals": [],
        "transactions": [],
        "disputes": [],
        "giveaways": [],
        "referrals": {},
        "leaderboard": {},
        "daily_reports": [],
        "auto_match": {"enabled": True, "buyers": [], "sellers": []},
        "spam_detection": {"enabled": True, "threshold": 5, "users": {}},
        "deal_categories": ["💎 Crypto", "📈 Forex", "📊 Stocks", "🎨 NFT", "📦 General"],
        "group_settings": {
            "auto_reply": True,
            "welcome_message": True,
            "live_ticker": True,
            "deal_keywords": ["deal", "escrow", "buy", "sell", "trade", "exchange"]
        },
        "payment_methods": ["💳 USDT", "🪙 TON", "🏦 Bank Transfer", "📱 UPI"],
        "withdraw_requests": [],
        "audit_logs": [],
        "reports": []
    }

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

data = load_data()

# ============================================
# LOGGING
# ============================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ============================================
# HELPERS
# ============================================

def get_user_stats(user_id):
    user_id = str(user_id)
    if user_id not in data["users"]:
        data["users"][user_id] = {
            "rank": len(data["users"]) + 1,
            "active_deals": 0,
            "total_escrows": 0,
            "volume": {"TON": 0, "USDT": 0, "TR4": 0},
            "joined_date": str(datetime.now()),
            "warnings": 0,
            "deals_count": 0,
            "rating": 0,
            "referred_by": None,
            "referrals_count": 0,
            "notifications": True,
            "theme": "light"
        }
        save_data(data)
    return data["users"][user_id]

def is_main_admin(user_id):
    return user_id == MAIN_ADMIN

def is_co_admin(user_id):
    return user_id in CO_ADMINS

def is_admin(user_id):
    return user_id in ADMIN_IDS

def is_banned(user_id):
    return str(user_id) in data["banned_users"]

def escape_html(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def premium_button(text, emoji, callback_data, style="premium"):
    styles = {
        "gold": "✨",
        "platinum": "💎",
        "diamond": "💠",
        "ruby": "🔴",
        "sapphire": "🔵",
        "emerald": "🟢",
        "amethyst": "🟣",
        "onyx": "⚫",
        "rose": "🩷",
        "crystal": "🔮",
        "premium": "⭐",
        "luxury": "👑",
        "vip": "💎"
    }
    prefix = styles.get(style, "⭐")
    return InlineKeyboardButton(f"{prefix} {emoji} {text}", callback_data=callback_data)

def get_leaderboard():
    sorted_users = sorted(data["users"].items(), key=lambda x: x[1].get("deals_count", 0), reverse=True)
    return sorted_users[:10]

def log_audit(action, user_id, details):
    data["audit_logs"].append({
        "action": action,
        "user": str(user_id),
        "details": details,
        "time": str(datetime.now())
    })
    save_data(data)

# ============================================
# START COMMAND
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    user_id = update.effective_user.id
    
    if is_banned(user_id):
        await update.message.reply_text("🚫 <b>You are BANNED from using this bot!</b>", parse_mode="HTML")
        return
    
    get_user_stats(user_id)
    
    keyboard = [
        [
            premium_button("My Stats", "📊", "mystats", "gold"),
            premium_button("My Deals", "📋", "mydeals", "platinum")
        ],
        [
            premium_button("Pending Deals", "⏳", "mypending", "crystal"),
            premium_button("Global Stats", "🌍", "globalstats", "diamond")
        ],
        [
            premium_button("New Deal", "💰", "new_deal", "emerald"),
            premium_button("History", "📈", "history", "sapphire")
        ],
        [
            premium_button("Leaderboard", "🏆", "leaderboard", "gold"),
            premium_button("Referral", "🔰", "referral", "rose")
        ],
        [
            premium_button("Deal Categories", "📂", "deal_categories", "amethyst"),
            premium_button("Payment Methods", "💳", "payment_methods", "crystal")
        ],
        [
            premium_button("Settings", "⚙️", "user_settings", "onyx")
        ]
    ]
    
    if is_admin(user_id):
        keyboard.append([premium_button("👑 Admin Panel", "👑", "admin_panel", "luxury")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"✨ <b>Welcome {escape_html(user.upper())}!</b> ✨\n\n"
        f"💎 <b>Escrow Bot for {escape_html(GROUP_USERNAME)}</b>\n"
        f"⭐ Powered by {escape_html(POWERED_BY)}\n"
        f"👑 <b>THE DIGITAL WORLD</b>\n"
        f"🎯 <b>FOCUS MUST WIN</b>\n\n"
        f"📌 <b>Your Premium Dashboard:</b>\n"
        f"Select an option below 👇"
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    
    log_audit("user_started", user_id, f"User {user} started the bot")

# ============================================
# GROUP MESSAGE HANDLER
# ============================================

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ["group", "supergroup"]:
        text = update.message.text
        user = update.effective_user.first_name
        user_id = update.effective_user.id
        
        if is_banned(user_id):
            await update.message.delete()
            return
        
        if data["spam_detection"]["enabled"]:
            if str(user_id) not in data["spam_detection"]["users"]:
                data["spam_detection"]["users"][str(user_id)] = {"count": 0, "time": str(datetime.now())}
            
            spam_data = data["spam_detection"]["users"][str(user_id)]
            if spam_data["count"] >= data["spam_detection"]["threshold"]:
                data["banned_users"].append(str(user_id))
                save_data(data)
                await update.message.delete()
                await update.message.reply_text(f"🚫 {user} auto-banned for spamming!")
                log_audit("auto_ban", user_id, f"User {user} auto-banned for spamming")
                return
            
            spam_data["count"] += 1
            save_data(data)
        
        if data["group_settings"].get("live_ticker", True):
            if any(word in text.lower() for word in ["deal", "escrow", "buy", "sell", "trade", "exchange"]):
                stats = data["global_stats"]
                await update.message.reply_text(
                    f"📊 <b>Live Deal Ticker</b>\n\n"
                    f"💰 <b>Total Deals:</b> {stats['total_deals']}\n"
                    f"📈 <b>Total Volume:</b> {stats['total_volume']['TON']:.2f} TON\n"
                    f"👥 <b>Active Users:</b> {len(data['users'])}\n\n"
                    f"📌 <b>Latest Deal by:</b> {escape_html(user)}\n"
                    f"🔒 {escape_html(GROUP_USERNAME)}",
                    parse_mode="HTML"
                )
        
        if data["group_settings"].get("auto_reply", True):
            keywords = data["group_settings"].get("deal_keywords", ["deal", "escrow", "buy", "sell", "trade"])
            if any(word in text.lower() for word in keywords):
                reply_text = (
                    f"✅ <b>Deal Request Received!</b>\n\n"
                    f"👤 <b>User:</b> {escape_html(user)}\n"
                    f"📝 <b>Message:</b> {escape_html(text)}\n\n"
                    f"💎 <b>Escrow Bot for {escape_html(GROUP_USERNAME)}</b>\n"
                    f"⭐ Powered by {escape_html(POWERED_BY)}\n\n"
                    f"📌 Please wait for admin to process your request."
                )
                await update.message.reply_text(reply_text, parse_mode="HTML")
        
        elif text.startswith("/start"):
            await start(update, context)
        
        elif text.startswith("/help"):
            help_text = (
                f"✨ <b>Escrow Bot Help</b>\n\n"
                f"📌 <b>Commands:</b>\n"
                f"• /start - Show premium dashboard\n"
                f"• /help - Show this message\n"
                f"• /join_giveaway - Join active giveaway\n\n"
                f"💎 <b>Escrow Bot for {escape_html(GROUP_USERNAME)}</b>\n"
                f"⭐ Powered by {escape_html(POWERED_BY)}"
            )
            await update.message.reply_text(help_text, parse_mode="HTML")

# ============================================
# GIVEAWAY JOIN
# ============================================

async def join_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if is_banned(user_id):
        await update.message.reply_text("🚫 You are banned!", parse_mode="HTML")
        return
    
    active_giveaway = None
    for g in data["giveaways"]:
        if g["status"] == "active":
            active_giveaway = g
            break
    
    if not active_giveaway:
        await update.message.reply_text("❌ No active giveaway right now!", parse_mode="HTML")
        return
    
    if str(user_id) in active_giveaway["entries"]:
        await update.message.reply_text("⚠️ You already joined this giveaway!", parse_mode="HTML")
        return
    
    active_giveaway["entries"].append(str(user_id))
    save_data(data)
    
    await update.message.reply_text(
        f"✅ <b>You joined the giveaway!</b>\n\n"
        f"🎁 <b>Prize:</b> {active_giveaway['prize']}\n"
        f"📌 <b>Total Entries:</b> {len(active_giveaway['entries'])}\n\n"
        f"Good luck! 🍀",
        parse_mode="HTML"
    )

# ============================================
# BUTTON HANDLER (SIMPLE)
# ============================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    if is_banned(user_id):
        await query.edit_message_text("🚫 <b>You are BANNED!</b>", parse_mode="HTML")
        return
    
    if query.data == "referral":
        await query.edit_message_text(
            "🔰 <b>Referral System</b>\n\n🛠️ <b>Under Maintenance</b>\n\n📌 Contact: @cyber_amit",
            parse_mode="HTML"
        )
        return
    
    if query.data == "mystats":
        stats = get_user_stats(user_id)
        text = (
            f"✨ <b>{escape_html(user_name)} Deal stats !</b> ✨\n\n"
            f"🏆 <b>Rank</b> ➤ #{stats['rank']}\n"
            f"📌 <b>Active deals</b> ➤ {stats['active_deals']}\n"
            f"📦 <b>Total Escrow's</b> ➤ {stats['total_escrows']}\n"
            f"💰 <b>Total Volume</b> :\n"
            f"  • <b>TON</b> ➤ {stats['volume']['TON']}\n"
            f"  • <b>USDT</b> ➤ {stats['volume']['USDT']}\n"
            f"  • <b>TR4</b> ➤ {stats['volume']['TR4']}\n\n"
            f"⭐ <b>Rating</b> ➤ {stats.get('rating', 0)}/5\n"
            f"📊 <b>Deals Done</b> ➤ {stats.get('deals_count', 0)}\n"
            f"⚠️ <b>Warnings</b> ➤ {stats.get('warnings', 0)}\n"
            f"📅 <b>Joined</b> ➤ {stats.get('joined_date', 'N/A')}\n\n"
            f"💎 <b>Escrow Bot for {escape_html(GROUP_USERNAME)}</b>\n"
            f"⭐ Provided by {escape_html(POWERED_BY)} !"
        )
        await query.edit_message_text(text, parse_mode="HTML")
        return
    
    if query.data == "mydeals":
        keyboard = [
            [premium_button("Active Deals", "📌", "my_active_deals", "emerald")],
            [premium_button("Completed Deals", "✅", "my_completed_deals", "platinum")],
            [premium_button("Back", "🔙", "back", "onyx")]
        ]
        await query.edit_message_text("📋 <b>Your Deals</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    
    if query.data == "my_active_deals":
        user_deals = [d for d in data["pending_deals"] if d.get("user") == str(user_id)]
        text = "\n".join([f"• #{d.get('id')} - {d.get('amount', {}).get('TON', 0)} TON" for d in user_deals[:10]]) if user_deals else "No active deals"
        keyboard = [[premium_button("Back", "🔙", "mydeals", "onyx")]]
        await query.edit_message_text(f"📌 <b>Active Deals</b>\n\n{text}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    
    if query.data == "my_completed_deals":
        user_deals = [d for d in data["completed_deals"] if d.get("user") == str(user_id)]
        text = "\n".join([f"• #{d.get('id')} - {d.get('amount', {}).get('TON', 0)} TON" for d in user_deals[-10:]]) if user_deals else "No completed deals"
        keyboard = [[premium_button("Back", "🔙", "mydeals", "onyx")]]
        await query.edit_message_text(f"✅ <b>Completed Deals</b>\n\n{text}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    
    if query.data == "mypending":
        keyboard = [[premium_button("Back", "🔙", "back", "onyx")]]
        await query.edit_message_text("⏳ <b>No pending deals!</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    
    if query.data == "globalstats":
        stats = data["global_stats"]
        keyboard = [[premium_button("Refresh", "🔄", "globalstats", "crystal")], [premium_button("Back", "🔙", "back", "onyx")]]
        text = (
            f"🌍 <b>Global Stats</b>\n\n"
            f"📊 Total Deals: {stats['total_deals']}\n"
            f"💰 TON: {stats['total_volume']['TON']:.2f}\n"
            f"💰 USDT: {stats['total_volume']['USDT']:.2f}\n"
            f"💰 INR: {stats['total_volume']['INR']:.2f}\n"
            f"👥 Users: {len(data['users'])}"
        )
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    
    if query.data == "new_deal":
        keyboard = [
            [premium_button("Create Deal", "📝", "create_deal", "emerald")],
            [premium_button("Back", "🔙", "back", "onyx")]
        ]
        await query.edit_message_text("💰 <b>Create New Deal</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    
    if query.data == "create_deal":
        stats = data["global_stats"]
        stats["total_deals"] += 1
        stats["total_volume"]["TON"] += 10.5
        stats["total_volume"]["USDT"] += 250
        stats["total_volume"]["INR"] += 1500
        save_data(data)
        
        deal_id = len(data["pending_deals"]) + 1
        data["pending_deals"].append({
            "id": deal_id,
            "user": user_id,
            "user_name": user_name,
            "amount": {"TON": 10.5, "USDT": 250, "INR": 1500},
            "status": "pending",
            "created_at": str(datetime.now())
        })
        save_data(data)
        
        keyboard = [[premium_button("Back", "🔙", "back", "onyx")]]
        await query.edit_message_text(f"✅ <b>Deal #{deal_id} Created!</b>\n\n💰 10.5 TON | 250 USDT | 1500 INR", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    
    if query.data == "deal_categories":
        categories = data.get("deal_categories", ["💎 Crypto", "📈 Forex", "📊 Stocks", "🎨 NFT", "📦 General"])
        keyboard = [[premium_button("Back", "🔙", "back", "onyx")]]
        await query.edit_message_text(f"📂 <b>Categories</b>\n\n" + "\n".join(categories), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    
    if query.data == "payment_methods":
        methods = data.get("payment_methods", ["💳 USDT", "🪙 TON", "🏦 Bank Transfer", "📱 UPI"])
        keyboard = [[premium_button("Back", "🔙", "back", "onyx")]]
        await query.edit_message_text(f"💳 <b>Payment Methods</b>\n\n" + "\n".join(methods), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    
    if query.data == "history":
        keyboard = [[premium_button("Back", "🔙", "back", "onyx")]]
        await query.edit_message_text("📈 <b>No history yet!</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    
    if query.data == "leaderboard":
        top_users = get_leaderboard()
        if top_users:
            text = "🏆 <b>Leaderboard</b>\n\n"
            for i, (uid, stats) in enumerate(top_users, 1):
                name = data["users"].get(uid, {}).get("name", uid)
                deals = stats.get("deals_count", 0)
                medals = {1: "🥇", 2: "🥈", 3: "🥉"}
                text += f"{medals.get(i, f'#{i}')} {name} - {deals} deals\n"
        else:
            text = "🏆 <b>No users yet!</b>"
        keyboard = [[premium_button("Back", "🔙", "back", "onyx")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    
    if query.data == "user_settings":
        keyboard = [
            [premium_button("🔔 Notifications", "🔔", "toggle_notifications", "crystal")],
            [premium_button("Back", "🔙", "back", "onyx")]
        ]
        await query.edit_message_text("⚙️ <b>Settings</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    
    if query.data == "toggle_notifications":
        user_stats = get_user_stats(user_id)
        user_stats["notifications"] = not user_stats.get("notifications", True)
        save_data(data)
        await query.edit_message_text(f"✅ Notifications {'Enabled' if user_stats['notifications'] else 'Disabled'}!")
        return
    
    # ============================================================
    # ADMIN PANEL
    # ============================================================
    
    if query.data == "admin_panel":
        if not is_admin(user_id):
            await query.edit_message_text("❌ Unauthorized!", parse_mode="HTML")
            return
        
        is_main = is_main_admin(user_id)
        admin_type = "👑 Main Admin" if is_main else "💎 Co-Admin"
        
        keyboard = [
            [premium_button("Total Users", "👥", "admin_users", "sapphire")],
            [premium_button("Volume Stats", "💰", "admin_volume", "emerald")],
            [premium_button("Add Deal", "📝", "admin_add_deal", "gold")],
            [premium_button("Remove Deal", "🗑️", "admin_remove_deal", "ruby")],
            [premium_button("Edit Stats", "📊", "admin_edit_stats", "crystal")],
            [premium_button("Reset Stats", "🔄", "admin_reset", "ruby")],
            [premium_button("Ban User", 
