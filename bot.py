import os
import logging
import json
import random
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# ============================================
# CONFIG
# ============================================

BOT_TOKEN = "8907822126:AAHYCaMf10hA75j5yxUQWHt8D-RqfnduVEU"
MAIN_ADMIN = 8603893462
CO_ADMINS = [7659172575]
ADMIN_IDS = [8603893462, 7659172575]
GROUP_USERNAME = "@CertifiedDeal"
POWERED_BY = "@cyber_amit"

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
        "global_stats": {"total_deals": 0, "total_volume": {"TON": 0, "USDT": 0, "INR": 0}},
        "pending_deals": [],
        "completed_deals": [],
        "transactions": [],
        "disputes": [],
        "giveaways": [],
        "auto_match": {"enabled": True, "buyers": [], "sellers": []},
        "spam_detection": {"enabled": True, "threshold": 5, "users": {}},
        "deal_categories": ["💎 Crypto", "📈 Forex", "📊 Stocks", "🎨 NFT", "📦 General"],
        "group_settings": {"auto_reply": True, "welcome_message": True, "live_ticker": True, "deal_keywords": ["deal", "escrow", "buy", "sell", "trade"]},
        "payment_methods": ["💳 USDT", "🪙 TON", "🏦 Bank Transfer", "📱 UPI"],
        "audit_logs": []
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
            "notifications": True
        }
        save_data(data)
    return data["users"][user_id]

def is_main_admin(user_id):
    return user_id == MAIN_ADMIN

def is_admin(user_id):
    return user_id in ADMIN_IDS

def is_banned(user_id):
    return str(user_id) in data["banned_users"]

def escape_html(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def premium_button(text, emoji, callback_data):
    return InlineKeyboardButton(f"✨ {emoji} {text}", callback_data=callback_data)

def get_leaderboard():
    sorted_users = sorted(data["users"].items(), key=lambda x: x[1].get("deals_count", 0), reverse=True)
    return sorted_users[:10]

def log_audit(action, user_id, details):
    data["audit_logs"].append({"action": action, "user": str(user_id), "details": details, "time": str(datetime.now())})
    save_data(data)

# ============================================
# START
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    user_id = update.effective_user.id
    
    if is_banned(user_id):
        await update.message.reply_text("🚫 You are BANNED!", parse_mode="HTML")
        return
    
    get_user_stats(user_id)
    
    keyboard = [
        [premium_button("My Stats", "📊", "mystats"), premium_button("My Deals", "📋", "mydeals")],
        [premium_button("Pending", "⏳", "mypending"), premium_button("Global Stats", "🌍", "globalstats")],
        [premium_button("New Deal", "💰", "new_deal"), premium_button("History", "📈", "history")],
        [premium_button("Leaderboard", "🏆", "leaderboard"), premium_button("Referral", "🔰", "referral")],
        [premium_button("Categories", "📂", "deal_categories"), premium_button("Payments", "💳", "payment_methods")],
        [premium_button("Settings", "⚙️", "user_settings")]
    ]
    
    if is_admin(user_id):
        keyboard.append([premium_button("Admin Panel", "👑", "admin_panel")])
    
    await update.message.reply_text(
        f"✨ Welcome {escape_html(user)}!\n💎 {escape_html(GROUP_USERNAME)}\n⭐ {escape_html(POWERED_BY)}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

# ============================================
# GROUP MESSAGE
# ============================================

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type not in ["group", "supergroup"]:
        return
    
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
            return
        spam_data["count"] += 1
        save_data(data)
    
    keywords = ["deal", "escrow", "buy", "sell", "trade", "exchange"]
    if any(word in text.lower() for word in keywords):
        await update.message.reply_text(
            f"✅ Deal Request Received!\n👤 {escape_html(user)}\n📝 {escape_html(text)}\n💎 {escape_html(GROUP_USERNAME)}",
            parse_mode="HTML"
        )

# ============================================
# GIVEAWAY JOIN
# ============================================

async def join_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_banned(user_id):
        await update.message.reply_text("🚫 Banned!", parse_mode="HTML")
        return
    
    active = None
    for g in data["giveaways"]:
        if g["status"] == "active":
            active = g
            break
    
    if not active:
        await update.message.reply_text("❌ No active giveaway!", parse_mode="HTML")
        return
    
    if str(user_id) in active["entries"]:
        await update.message.reply_text("⚠️ Already joined!", parse_mode="HTML")
        return
    
    active["entries"].append(str(user_id))
    save_data(data)
    await update.message.reply_text(f"✅ Joined! Total entries: {len(active['entries'])}", parse_mode="HTML")

# ============================================
# BUTTON HANDLER
# ============================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    if is_banned(user_id):
        await query.edit_message_text("🚫 BANNED!", parse_mode="HTML")
        return
    
    # REFERRAL
    if query.data == "referral":
        await query.edit_message_text("🔰 Under Maintenance\n\nContact: @cyber_amit", parse_mode="HTML")
        return
    
    # MY STATS
    if query.data == "mystats":
        stats = get_user_stats(user_id)
        await query.edit_message_text(
            f"✨ {escape_html(user_name)} Stats ✨\n\n"
            f"🏆 Rank: #{stats['rank']}\n"
            f"📌 Active: {stats['active_deals']}\n"
            f"📦 Escrows: {stats['total_escrows']}\n"
            f"💰 TON: {stats['volume']['TON']}\n"
            f"💰 USDT: {stats['volume']['USDT']}\n"
            f"💰 TR4: {stats['volume']['TR4']}\n"
            f"⭐ Rating: {stats.get('rating', 0)}/5\n"
            f"📊 Deals: {stats.get('deals_count', 0)}\n"
            f"⚠️ Warnings: {stats.get('warnings', 0)}",
            parse_mode="HTML"
        )
        return
    
    # MY DEALS
    if query.data == "mydeals":
        keyboard = [
            [premium_button("Active", "📌", "my_active_deals")],
            [premium_button("Completed", "✅", "my_completed_deals")],
            [premium_button("Back", "🔙", "back")]
        ]
        await query.edit_message_text("📋 Your Deals", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    
    if query.data == "my_active_deals":
        deals = [d for d in data["pending_deals"] if d.get("user") == str(user_id)]
        text = "\n".join([f"• #{d.get('id')} - {d.get('amount', {}).get('TON', 0)} TON" for d in deals[:10]]) or "No active deals"
        keyboard = [[premium_button("Back", "🔙", "mydeals")]]
        await query.edit_message_text(f"📌 {text}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    
    if query.data == "my_completed_deals":
        deals = [d for d in data["completed_deals"] if d.get("user") == str(user_id)]
        text = "\n".join([f"• #{d.get('id')} - {d.get('amount', {}).get('TON', 0)} TON" for d in deals[-10:]]) or "No completed deals"
        keyboard = [[premium_button("Back", "🔙", "mydeals")]]
        await query.edit_message_text(f"✅ {text}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    
    # PENDING
    if query.data == "mypending":
        keyboard = [[premium_button("Back", "🔙", "back")]]
        await query.edit_message_text("⏳ No pending deals!", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    
    # GLOBAL STATS
    if query.data == "globalstats":
        stats = data["global_stats"]
        keyboard = [[premium_button("Refresh", "🔄", "globalstats")], [premium_button("Back", "🔙", "back")]]
        await query.edit_message_text(
            f"🌍 Global Stats\n\n"
            f"📊 Deals: {stats['total_deals']}\n"
            f"💰 TON: {stats['total_volume']['TON']:.2f}\n"
            f"💰 USDT: {stats['total_volume']['USDT']:.2f}\n"
            f"💰 INR: {stats['total_volume']['INR']:.2f}\n"
            f"👥 Users: {len(data['users'])}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        return
    
    # NEW DEAL
    if query.data == "new_deal":
        keyboard = [
            [premium_button("Create Deal", "📝", "create_deal")],
            [premium_button("Back", "🔙", "back")]
        ]
        await query.edit_message_text("💰 Create Deal", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
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
        
        keyboard = [[premium_button("Back", "🔙", "back")]]
        await query.edit_message_text(f"✅ Deal #{deal_id} Created!\n💰 10.5 TON | 250 USDT | 1500 INR", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    
    # CATEGORIES
    if query.data == "deal_categories":
        cats = data.get("deal_categories", ["💎 Crypto", "📈 Forex", "📊 Stocks", "🎨 NFT", "📦 General"])
        keyboard = [[premium_button("Back", "🔙", "back")]]
        await query.edit_message_text(f"📂 Categories\n\n" + "\n".join(cats), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    
    # PAYMENT METHODS
    if query.data == "payment_methods":
        methods = data.get("payment_methods", ["💳 USDT", "🪙 TON", "🏦 Bank Transfer", "📱 UPI"])
        keyboard = [[premium_button("Back", "🔙", "back")]]
        await query.edit_message_text(f"💳 Payment Methods\n\n" + "\n".join(methods), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    
    # HISTORY
    if query.data == "history":
        keyboard = [[premium_button("Back", "🔙", "back")]]
        await query.edit_message_text("📈 No history yet!", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    
    # LEADERBOARD
    if query.data == "leaderboard":
        top = get_leaderboard()
        if top:
            text = "🏆 Leaderboard\n\n"
            for i, (uid, stats) in enumerate(top, 1):
                name = data["users"].get(uid, {}).get("name", uid)
                medals = {1: "🥇", 2: "🥈", 3: "🥉"}
                text += f"{medals.get(i, f'#{i}')} {name} - {stats.get('deals_count', 0)} deals\n"
        else:
            text = "🏆 No users yet!"
        keyboard = [[premium_button("Back", "🔙", "back")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    
    # SETTINGS
    if query.data == "user_settings":
        keyboard = [
            [premium_button("🔔 Notifications", "🔔", "toggle_notifications")],
            [premium_button("Back", "🔙", "back")]
        ]
        await query.edit_message_text("⚙️ Settings", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    
    if query.data == "toggle_notifications":
        stats = get_user_stats(user_id)
        stats["notifications"] = not stats.get("notifications", True)
        save_data(data)
        await query.edit_message_text(f"✅ Notifications {'Enabled' if stats['notifications'] else 'Disabled'}!", parse_mode="HTML")
        return
    
    # ============================================================
    # ADMIN PANEL
    # ============================================================
    
    if query.data == "admin_panel":
        if not is_admin(user_id):
            await query.edit_message_text("❌ Unauthorized!", parse_mode="HTML")
            return
        
        is_main = is_main_admin(user_id)
        keyboard = [
            [premium_button("Users", "👥", "admin_users")],
            [premium_button("Volume", "💰", "admin_volume")],
            [premium_button("Add Deal", "📝", "admin_add_deal")],
            [premium_button("Remove Deal", "🗑️", "admin_remove_deal")],
            [premium_button("Edit Stats", "📊", "admin_edit_stats")],
            [premium_button("Reset", "🔄", "admin_reset")],
            [premium_button("Ban", "🚫", "admin_ban_user")],
            [premium_button("Unban", "✅", "admin_unban_user")],
            [premium_button("Pending", "📋", "admin_pending_deals")],
            [premium_button("Disputes", "⚖️", "admin_disputes")],
            [premium_button("Giveaway", "🎁", "admin_giveaway")],
            [premium_button("Auto Match", "🤖", "admin_auto_match")],
            [premium_button("Spam", "🛡️", "admin_spam_settings")],
            [premium_button("Analytics", "📊", "admin_analytics")],
            [premium_button("Daily Report", "📈", "admin_daily_report")],
            [premium_button("Audit Logs", "📝", "admin_audit_logs")],
        ]
        
        if is_main:
            keyboard.append([premium_button("Broadcast", "📢", "admin_broadcast")])
            keyboard.append([premium_button("Manage Admins", "👥", "admin_manage_admins")])
        
        keyboard.append([premium_button("Back", "🔙", "back")])
        
        await query.edit_message_text(
            f"👑 Admin Panel\nRole: {'Main Admin' if is_main else 'Co-Admin'}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        return
    
    # MANAGE ADMINS
    if query.data == "admin_manage_admins":
        if not is_main_admin(user_id):
            await query.edit_message_text("❌ Only Main Admin!")
            return
        keyboard = [
            [premium_button("Add", "➕", "add_co_admin")],
            [premium_button("Remove", "➖", "remove_co_admin")],
            [premium_button("View", "📋", "view_admins")],
            [premium_button("Back", "🔙", "admin_panel")]
        ]
        await query.edit_message_text("👥 Manage Admins", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    
    if query.data == "add_co_admin":
        if not is_main_admin(user_id):
            return
        await query.edit_message_text("➕ /addadmin user_id", parse_mode="HTML")
        return
    
    if query.data == "remove_co_admin":
        if not is_main_admin(user_id):
            return
        if not CO_ADMINS:
            await query.edit_message_text("❌ No co-admins!")
            return
        keyboard = []
        for aid in CO_ADMINS:
            keyboard.append([InlineKeyboardButton(f"❌ Remove {aid}", callback_data=f"remove_admin_{aid}")])
        keyboard.append([premium_button("Back", "🔙", "admin_panel")])
        await query.edit_message_text("➖ Select:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    
    if query.data == "view_admins":
        if not is_main_admin(user_id):
            return
        co_list = "\n".join([f"• {uid}" for uid in CO_ADMINS]) or "No co-admins"
        keyboard = [[premium_button("Back", "🔙", "admin_panel")]]
        await query.edit_message_text(f"👑 Main: {MAIN_ADMIN}\n💎 Co-Admins:\n{co_list}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    
    # USERS
    if query.data == "admin_users":
        if not is_admin(user_id):
            return
        keyboard = [[premium_button("Back", "🔙", "admin_panel")]]
        await query.edit_message_text(f"👥 Users: {len(data['users'])}\n🚫 Banned: {len(data['banned_users'])}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    
    # VOLUME
    if query.data == "admin_volume":
        if not is_admin(user_id):
            return
        stats = data["global_stats"]
        keyboard = [[premium_button("Back", "🔙", "admin_panel")]]
        await query.edit_message_text(
            f"💰 TON: {stats['total_volume']['TON']:.2f}\n"
            f"💰 USDT: {stats['total_volume']['USDT']:.2f}\n"
            f"💰 INR: {stats['total_volume']['INR']:.2f}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        return
    
    # ADD DEAL
    if query.data == "admin_add_deal":
        if not is_admin(user_id):
            return
        keyboard = [
            [InlineKeyboardButton("✅ +10 TON", callback_data="add_default_deal")],
            [premium_button("Back", "🔙", "admin_panel")]
        ]
        await query.edit_message_text("📝 Add Deal", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    
    if query.data == "add_default_deal":
        if not is_admin(user_id):
            return
        stats = data["global_stats"]
        stats["total_deals"] += 1
        stats["total_volume"]["TON"] += 10.5
        stats["total_volume"]["USDT"] += 250
        stats["total_volume"]["INR"] += 1500
        save_data(data)
        keyboard = [[premium_button("Back", "🔙", "admin_panel")]]
        await query.edit_message_text(f"✅ Deal Added! Total: {stats['total_deals']}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML
