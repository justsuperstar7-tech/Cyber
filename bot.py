import os
import logging
import json
import random
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN = "8907822126:AAHYCaMf10hA75j5yxUQWHt8D-RqfnduVEU"
MAIN_ADMIN = 8603893462
CO_ADMINS = [7659172575]
ADMIN_IDS = [8603893462, 7659172575]
GROUP_USERNAME = "@CertifiedDeal"
POWERED_BY = "@cyber_amit"

DATA_FILE = "escrow_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {
        "users": {},
        "banned_users": [],
        "co_admins": [7659172575],
        "global_stats": {"total_deals": 0, "total_volume": {"TON": 0, "USDT": 0, "INR": 0}},
        "pending_deals": [],
        "completed_deals": [],
        "giveaways": [],
        "auto_match": {"enabled": True},
        "spam_detection": {"enabled": True, "threshold": 5, "users": {}},
        "audit_logs": []
    }

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

data = load_data()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

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

def is_admin(user_id): return user_id in ADMIN_IDS
def is_main_admin(user_id): return user_id == MAIN_ADMIN
def is_banned(user_id): return str(user_id) in data["banned_users"]
def escape_html(text): return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
def premium_button(text, emoji, callback_data): return InlineKeyboardButton(f"{emoji} {text}", callback_data=callback_data)
def get_leaderboard(): return sorted(data["users"].items(), key=lambda x: x[1].get("deals_count", 0), reverse=True)[:10]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    user_id = update.effective_user.id
    if is_banned(user_id):
        await update.message.reply_text("🚫 You are BANNED!", parse_mode="HTML")
        return
    get_user_stats(user_id)
    keyboard = [
        [premium_button("My Stats", "📊", "mystats"), premium_button("My Deals", "📋", "mydeals")],
        [premium_button("Pending", "⏳", "mypending"), premium_button("Global", "🌍", "globalstats")],
        [premium_button("New Deal", "💰", "new_deal"), premium_button("Leaderboard", "🏆", "leaderboard")],
        [premium_button("Referral", "🔰", "referral"), premium_button("Settings", "⚙️", "user_settings")]
    ]
    if is_admin(user_id):
        keyboard.append([premium_button("Admin Panel", "👑", "admin_panel")])
    await update.message.reply_text(
        f"✨ Welcome {escape_html(user)}!\n💎 {escape_html(GROUP_USERNAME)}\n⭐ {escape_html(POWERED_BY)}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    if is_banned(user_id):
        await query.edit_message_text("🚫 BANNED!", parse_mode="HTML")
        return
    if query.data == "referral":
        await query.edit_message_text("🔰 Under Maintenance\nContact: @cyber_amit", parse_mode="HTML")
        return
    if query.data == "mystats":
        stats = get_user_stats(user_id)
        await query.edit_message_text(
            f"✨ {escape_html(user_name)} Stats ✨\n\n🏆 Rank: #{stats['rank']}\n📌 Active: {stats['active_deals']}\n📦 Escrows: {stats['total_escrows']}\n💰 TON: {stats['volume']['TON']}\n💰 USDT: {stats['volume']['USDT']}\n💰 TR4: {stats['volume']['TR4']}\n⭐ Rating: {stats.get('rating', 0)}/5\n📊 Deals: {stats.get('deals_count', 0)}\n⚠️ Warnings: {stats.get('warnings', 0)}",
            parse_mode="HTML"
        )
        return
    if query.data == "mydeals":
        keyboard = [[premium_button("Active", "📌", "my_active_deals")], [premium_button("Completed", "✅", "my_completed_deals")], [premium_button("Back", "🔙", "back")]]
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
    if query.data == "mypending":
        keyboard = [[premium_button("Back", "🔙", "back")]]
        await query.edit_message_text("⏳ No pending deals!", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    if query.data == "globalstats":
        stats = data["global_stats"]
        keyboard = [[premium_button("Refresh", "🔄", "globalstats")], [premium_button("Back", "🔙", "back")]]
        await query.edit_message_text(
            f"🌍 Global Stats\n\n📊 Deals: {stats['total_deals']}\n💰 TON: {stats['total_volume']['TON']:.2f}\n💰 USDT: {stats['total_volume']['USDT']:.2f}\n💰 INR: {stats['total_volume']['INR']:.2f}\n👥 Users: {len(data['users'])}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        return
    if query.data == "new_deal":
        keyboard = [[premium_button("Create Deal", "📝", "create_deal")], [premium_button("Back", "🔙", "back")]]
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
        data["pending_deals"].append({"id": deal_id, "user": user_id, "user_name": user_name, "amount": {"TON": 10.5, "USDT": 250, "INR": 1500}, "status": "pending", "created_at": str(datetime.now())})
        save_data(data)
        keyboard = [[premium_button("Back", "🔙", "back")]]
        await query.edit_message_text(f"✅ Deal #{deal_id} Created!\n💰 10.5 TON | 250 USDT | 1500 INR", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
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
    if query.data == "user_settings":
        keyboard = [[premium_button("Notifications", "🔔", "toggle_notifications")], [premium_button("Back", "🔙", "back")]]
        await query.edit_message_text("⚙️ Settings", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    if query.data == "toggle_notifications":
        stats = get_user_stats(user_id)
        stats["notifications"] = not stats.get("notifications", True)
        save_data(data)
        await query.edit_message_text(f"✅ Notifications {'Enabled' if stats['notifications'] else 'Disabled'}!", parse_mode="HTML")
        return
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
            [premium_button("Giveaway", "🎁", "admin_giveaway")],
            [premium_button("Auto Match", "🤖", "admin_auto_match")],
            [premium_button("Spam", "🛡️", "admin_spam_settings")],
            [premium_button("Analytics", "📊", "admin_analytics")],
            [premium_button("Daily Report", "📈", "admin_daily_report")],
        ]
        if is_main:
            keyboard.append([premium_button("Broadcast", "📢", "admin_broadcast")])
            keyboard.append([premium_button("Manage Admins", "👥", "admin_manage_admins")])
        keyboard.append([premium_button("Back", "🔙", "back")])
        await query.edit_message_text(f"👑 Admin Panel\nRole: {'Main Admin' if is_main else 'Co-Admin'}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    if query.data == "admin_manage_admins":
        if not is_main_admin(user_id):
            await query.edit_message_text("❌ Only Main Admin!")
            return
        keyboard = [[premium_button("Add", "➕", "add_co_admin")], [premium_button("Remove", "➖", "remove_co_admin")], [premium_button("View", "📋", "view_admins")], [premium_button("Back", "🔙", "admin_panel")]]
        await query.edit_message_text("👥 Manage Admins", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    if query.data == "add_co_admin":
        if not is_main_admin(user_id): return
        await query.edit_message_text("➕ /addadmin user_id", parse_mode="HTML")
        return
    if query.data == "remove_co_admin":
        if not is_main_admin(user_id): return
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
        if not is_main_admin(user_id): return
        co_list = "\n".join([f"• {uid}" for uid in CO_ADMINS]) or "No co-admins"
        keyboard = [[premium_button("Back", "🔙", "admin_panel")]]
        await query.edit_message_text(f"👑 Main: {MAIN_ADMIN}\n💎 Co-Admins:\n{co_list}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    if query.data == "admin_users":
        if not is_admin(user_id): return
        keyboard = [[premium_button("Back", "🔙", "admin_panel")]]
        await query.edit_message_text(f"👥 Users: {len(data['users'])}\n🚫 Banned: {len(data['banned_users'])}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    if query.data == "admin_volume":
        if not is_admin(user_id): return
        stats = data["global_stats"]
        keyboard = [[premium_button("Back", "🔙", "admin_panel")]]
        await query.edit_message_text(f"💰 TON: {stats['total_volume']['TON']:.2f}\n💰 USDT: {stats['total_volume']['USDT']:.2f}\n💰 INR: {stats['total_volume']['INR']:.2f}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    if query.data == "admin_add_deal":
        if not is_admin(user_id): return
        keyboard = [[InlineKeyboardButton("✅ +10 TON", callback_data="add_default_deal")], [premium_button("Back", "🔙", "admin_panel")]]
        await query.edit_message_text("📝 Add Deal", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    if query.data == "add_default_deal":
        if not is_admin(user_id): return
        stats = data["global_stats"]
        stats["total_deals"] += 1
        stats["total_volume"]["TON"] += 10.5
        stats["total_volume"]["USDT"] += 250
        stats["total_volume"]["INR"] += 1500
        save_data(data)
        keyboard = [[premium_button("Back", "🔙", "admin_panel")]]
        await query.edit_message_text(f"✅ Deal Added! Total: {stats['total_deals']}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    if query.data == "admin_remove_deal":
        if not is_admin(user_id): return
        stats = data["global_stats"]
        if stats["total_deals"] > 0:
            stats["total_deals"] -= 1
            stats["total_volume"]["TON"] -= 10.5
            stats["total_volume"]["USDT"] -= 250
            stats["total_volume"]["INR"] -= 1500
            save_data(data)
            msg = f"✅ Removed! Total: {stats['total_deals']}"
        else:
            msg = "❌ No deals!"
        keyboard = [[premium_button("Back", "🔙", "admin_panel")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    if query.data == "admin_edit_stats":
        if not is_admin(user_id): return
        stats = data["global_stats"]
        keyboard = [[premium_button("TON", "📊", "edit_ton")], [premium_button("USDT", "📊", "edit_usdt")], [premium_button("INR", "📊", "edit_inr")], [premium_button("Deals", "📊", "edit_deals")], [premium_button("Back", "🔙", "admin_panel")]]
        await query.edit_message_text(f"Current:\nTON: {stats['total_volume']['TON']:.2f}\nUSDT: {stats['total_volume']['USDT']:.2f}\nINR: {stats['total_volume']['INR']:.2f}\nDeals: {stats['total_deals']}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    if query.data in ["edit_ton", "edit_usdt", "edit_inr", "edit_deals"]:
        if not is_admin(user_id): return
        field = query.data.replace("edit_", "")
        cmds = {"ton": "setton", "usdt": "setusdt", "inr": "setinr", "deals": "setdeals"}
        await query.edit_message_text(f"📊 Edit {field.upper()}\n\n/{cmds.get(field)} value", parse_mode="HTML")
        return
    if query.data == "admin_reset":
        if not is_admin(user_id): return
        keyboard = [[InlineKeyboardButton("⚠️ YES", callback_data="admin_reset_confirm")], [premium_button("Cancel", "❌", "admin_panel")]]
        await query.edit_message_text("⚠️ Reset all data?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    if query.data == "admin_reset_confirm":
        if not is_admin(user_id): return
        data["global_stats"] = {"total_deals": 0, "total_volume": {"TON": 0, "USDT": 0, "INR": 0}}
        data["users"] = {}
        data["pending_deals"] = []
        data["completed_deals"] = []
        data["audit_logs"] = []
        save_data(data)
        keyboard = [[premium_button("Back", "🔙", "admin_panel")]]
        await query.edit_message_text("✅ Reset complete!", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    if query.data == "admin_broadcast":
        if not is_main_admin(user_id):
            await query.edit_message_text("❌ Only Main Admin!")
            return
        keyboard = [[premium_button("Back", "🔙", "admin_panel")]]
        await query.edit_message_text("📢 /broadcast message", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    if query.data == "admin_ban_user":
        if not is_admin(user_id): return
        keyboard = [[premium_button("Back", "🔙", "admin_panel")]]
        await query.edit_message_text("🚫 /ban user_id", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    if query.data == "admin_unban_user":
        if not is_admin(user_id): return
        banned = "\n".join([f"• {uid}" for uid in data["banned_users"]]) or "None"
        keyboard = [[premium_button("Back", "🔙", "admin_panel")]]
        await query.edit_message_text(f"✅ /unban user_id\n\nBanned:\n{banned}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    if query.data == "admin_pending_deals":
        if not is_admin(user_id): return
        pending = data["pending_deals"]
        text = "\n".join([f"• #{d.get('id')} - {d.get('user_name')}" for d in pending[:10]]) or "No pending"
        keyboard = [[premium_button("Back", "🔙", "admin_panel")]]
        await query.edit_message_text(f"📋 Pending:\n{text}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    if query.data == "admin_giveaway":
        if not is_admin(user_id): return
        keyboard = [[premium_button("Start", "🎁", "giveaway_start")], [premium_button("Pick Winner", "🏆", "giveaway_pick_winner")], [premium_button("Back", "🔙", "admin_panel")]]
        await query.edit_message_text("🎁 Giveaway", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    if query.data == "giveaway_start":
        if not is_admin(user_id): return
        gid = len(data["giveaways"]) + 1
        data["giveaways"].append({"id": gid, "prize": "10 TON", "status": "active", "entries": []})
        save_data(data)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="🎁 GIVEAWAY!\nPrize: 10 TON\nType /join_giveaway", parse_mode="HTML")
        keyboard = [[premium_button("Back", "🔙", "admin_panel")]]
        await query.edit_message_text("✅ Giveaway started!", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    if query.data == "giveaway_pick_winner":
        if not is_admin(user_id): return
        active = None
        for g in data["giveaways"]:
            if g["status"] == "active":
                active = g
                break
        if not active:
            await query.edit_message_text("❌ No active giveaway!")
            return
        if not active["entries"]:
            await query.edit_message_text("❌ No entries!")
            return
        winner = random.choice(active["entries"])
        active["winner"] = winner
        active["status"] = "completed"
        save_data(data)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"🏆 Winner: {winner}!", parse_mode="HTML")
        keyboard = [[premium_button("Back", "🔙", "admin_panel")]]
        await query.edit_message_text(f"✅ Winner: {winner}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    if query.data == "admin_auto_match":
        if not is_admin(user_id): return
        status = "✅ Enabled" if data["auto_match"]["enabled"] else "❌ Disabled"
        keyboard = [[InlineKeyboardButton(f"🔄 Toggle", callback_data="toggle_auto_match")], [premium_but
