import discord
from discord.ext import commands
import asyncio
import random
import traceback
import os
import json
import io
from datetime import datetime

# ============================================================
# 7R COMMUNITY - Discord Bot
# ============================================================
# IMPORTANT:
# Put your bot token in the DISCORD_TOKEN environment variable.
# Never publish your token inside this file.
#
# Requires:
#   pip install -U discord.py
#
# Enable these intents in Discord Developer Portal:
#   MESSAGE CONTENT INTENT
#   SERVER MEMBERS INTENT
#   PRESENCE INTENT
# ============================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.guilds = True

bot = commands.Bot(command_prefix="$", intents=intents, help_command=None)

# =========================
# SERVER / PERMISSIONS
# =========================
OLD_SERVER_ID = 1300210023275827291
NEW_SERVER_ID = 1404871303340621996

OWNER_ID = 1021501331636244490
ADMIN_IDS = [1021501331636244490, 1133434766738329640]

# Only these commands work in the NEW server.
NEW_SERVER_ONLY_COMMANDS = {"tax", "massdm"}

# =========================
# CHANNELS / ROLES
# =========================
FEEDBACK_CHANNEL_ID = 1541011452037439489
WELCOME_CHANNEL_ID = 1538994818150170714
LOGS_CHANNEL_ID = 1538994821455282197

TICKET_PANEL_CHANNEL_ID = 1540797737438810172

SUPPORT_CATEGORY_ID = 1540776948954038452
MEDIATOR_CATEGORY_ID = 1540776952787632220

SUPPORT_ROLE_ID = 1543149771299094650
MEDIATOR_ROLE_ID = 1543142907958001768

MEDIATOR_CLIENT_ROLE_ID = 1543276152951414885
VIP_CLIENT_ROLE_ID = 1543276454895161455

TICKET_LOG_CHANNEL_ID = 1543277110951678155
MEDIATOR_RESULTS_CHANNEL_ID = 1540776982265073765

DIVIDER_IMAGE_URL = (
    "https://cdn.discordapp.com/attachments/1336759214378582066/"
    "1539262263893037086/Gemini_Generated_Image_97gvdg97gvdg97gv.jfif"
    "?ex=6a8af331&is=6a89a1b1&hm="
    "d057e94d76fb45c269c7262846cd27c363f1b88d8868586b0aa01121d28e2933"
)

# =========================
# STORE / POINTS
# =========================
store_credits = {}
EXCHANGE_RATE = 10

# Persistent mediator data.
DATA_FILE = "7r_bot_data.json"

data = {
    "mediator_points": {},       # user_id -> points
    "mediator_tickets": {},      # user_id -> successful ticket count
    "ticket_counter": 0,         # global ticket number
    "ticket_records": {},        # channel_id -> ticket metadata
    "ratings": {},                # ticket_number -> rating data
}

rated_users = set()
active_tickets = {}

SENSITIVE_WORDS = {
    "متوفر": "مـتـوفــر", "متوفره": "مـتـوفــرة", "متوفرة": "مـتـوفــرة", "توفر": "تـو_فُـر",
    "حسابات": "حـس_ابـات", "حساب": "حـس_اب", "ايميل": "ايـم___يل", "إيميل": "إيـم___يل",
    "ايميلات": "ايـم_يــلات", "إيميلات": "إيـم_يــلات", "جيميل": "جـيـمــيل", "gmail": "g_m_a_i_l",
    "نيترو": "نـيـتـــرو", "نايترو": "نـايـتـــرو", "nitro": "n_i_t_r_o", "بوت": "بـو_ت",
    "توكن": "تـوكــن", "token": "t_o_k_e_n", "بيع": "بـيـــع", "شراء": "شــــراء",
    "سعر": "سـعـــر", "اسعار": "أسـعـــار", "أسعار": "أسـعـــار", "ثمن": "ثـمــــن",
    "رخيص": "ر_خـيـص", "متجر": "مـت-جـــر", "عروضكم": "عـرو_ضـكم", "عروض": "عـرُو_ض",
    "عرض": "عَـرْ_ض", "طلب": "طـلـــب", "طلبات": "طـلــبات", "تسليم": "ت-س-ل-يــم",
    "ضمان": "ضـمـــان", "وسيط": "وسـيـــط", "كريديت": "كـرِيـدِيـت", "كريديتات": "كـرِي-ديــتات",
    "كرديت": "كـرديــت", "كردت": "كـر_دت", "بروبوت": "بـروبـوت", "probot": "p_r_o_b_o_t",
    "بايبال": "بـايـبــال", "paypal": "p_a_y_p_a_l", "رصيد": "ر_صـيـد", "فلوس": "فـلــوس",
    "مبلغ": "مـبـلـــغ", "تحويل": "ت-ح-ويــل", "كاش": "كــاش", "درهم": "در_هـم",
    "دولار": "دو_لار", "خاص": "خ_اص", "الخاص": "الـخ_اص", "خاصك": "خـاصـك",
    "دي ام": "دي_ام", "dm": "d_m", "خاصي": "خ_اصي", "تواصل": "ت-واصــل",
    "واتساب": "واتسـاب", "تيليجرام": "تيليـجرام", "telegram": "t_e_l_e_جـرام"
}


# ============================================================
# DATA HELPERS
# ============================================================

def load_data():
    global data, store_credits
    if not os.path.exists(DATA_FILE):
        return
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        for key in data:
            if key in loaded:
                data[key] = loaded[key]
        # Convert JSON keys to strings consistently.
        data["mediator_points"] = {str(k): int(v) for k, v in data["mediator_points"].items()}
        data["mediator_tickets"] = {str(k): int(v) for k, v in data["mediator_tickets"].items()}
        data["ticket_records"] = {str(k): v for k, v in data["ticket_records"].items()}
        data["ratings"] = {str(k): v for k, v in data["ratings"].items()}
    except Exception:
        traceback.print_exc()


def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        traceback.print_exc()


def get_store_credit(user_id):
    return store_credits.get(user_id, 0)


def update_store_credit(user_id, amount):
    current = get_store_credit(user_id)
    store_credits[user_id] = current + amount


def get_mediator_points(user_id):
    return int(data["mediator_points"].get(str(user_id), 0))


def set_mediator_points(user_id, amount):
    data["mediator_points"][str(user_id)] = max(0, int(amount))
    save_data()


def add_mediator_point(user_id, amount=1):
    uid = str(user_id)
    data["mediator_points"][uid] = get_mediator_points(user_id) + int(amount)
    data["mediator_tickets"][uid] = int(data["mediator_tickets"].get(uid, 0)) + int(amount)
    save_data()


def get_mediator_ticket_count(user_id):
    return int(data["mediator_tickets"].get(str(user_id), 0))


def all_mediator_ids():
    ids = set(data["mediator_points"].keys())
    ids.update(data["mediator_tickets"].keys())
    return [int(x) for x in ids if str(x).isdigit()]


def average_rating_for_mediator(user_id):
    values = []
    for record in data["ratings"].values():
        if str(record.get("mediator_id")) == str(user_id):
            try:
                values.append(float(record.get("rating", 0)))
            except Exception:
                pass
    return (sum(values) / len(values)) if values else 0.0


# ============================================================
# GENERIC HELPERS
# ============================================================

def parse_time(time_str):
    time_str = time_str.lower().strip()
    try:
        if time_str.endswith("s"):
            return int(time_str[:-1])
        if time_str.endswith("m"):
            return int(time_str[:-1]) * 60
        if time_str.endswith("h"):
            return int(time_str[:-1]) * 3600
        return int(time_str) * 60
    except ValueError:
        return None


def parse_amount(amount_str):
    amount_str = amount_str.lower().replace(",", "").strip()
    try:
        if amount_str.endswith("k"):
            return int(float(amount_str[:-1]) * 1000)
        if amount_str.endswith("m"):
            return int(float(amount_str[:-1]) * 1000000)
        return int(float(amount_str))
    except ValueError:
        return None


def is_admin(user_id):
    return user_id in ADMIN_IDS


def is_owner(user_id):
    return user_id == OWNER_ID


def is_old_server(ctx):
    return ctx.guild is not None and ctx.guild.id == OLD_SERVER_ID


def is_new_server(ctx):
    return ctx.guild is not None and ctx.guild.id == NEW_SERVER_ID


async def delete_after(message, seconds=10):
    await asyncio.sleep(seconds)
    try:
        await message.delete()
    except Exception:
        pass


async def deny(message, text="❌ هذا الأمر غير متاح هنا."):
    try:
        await message.reply(text, delete_after=8)
    except Exception:
        pass


async def send_divider(channel):
    if DIVIDER_IMAGE_URL:
        try:
            await channel.send(DIVIDER_IMAGE_URL)
        except Exception:
            pass


def ticket_record(channel):
    return data["ticket_records"].get(str(channel.id))


def get_ticket_record_by_number(number):
    for record in data["ticket_records"].values():
        if str(record.get("ticket_number")) == str(number):
            return record
    return None


def ticket_is_mediator(channel):
    record = ticket_record(channel)
    return bool(record and record.get("type") == "mediator")


def user_is_ticket_creator(member, channel):
    record = ticket_record(channel)
    return bool(record and str(record.get("creator_id")) == str(member.id))


def user_is_current_mediator(member, channel):
    record = ticket_record(channel)
    return bool(record and str(record.get("mediator_id")) == str(member.id))


async def get_member(guild, user_id):
    member = guild.get_member(int(user_id))
    if member:
        return member
    try:
        return await guild.fetch_member(int(user_id))
    except Exception:
        return None


async def create_text_transcript(channel):
    """Collects all visible messages from the ticket before deletion."""
    lines = []
    try:
        async for msg in channel.history(limit=None, oldest_first=True):
            created = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            content = msg.content or ""
            if msg.attachments:
                content += " " + " ".join(a.url for a in msg.attachments)
            if msg.embeds and not content:
                content = "[EMBED]"
            lines.append(
                f"[{created}] {msg.author} ({msg.author.id}): {content}"
            )
    except Exception as e:
        lines.append(f"[Transcript error] {e}")
    if not lines:
        lines.append("لا توجد رسائل في التكت.")
    return "\n".join(lines)


# ============================================================
# COMMAND GATE
# ============================================================

@bot.check
async def command_server_check(ctx):
    """All normal commands stay on OLD_SERVER.
       tax/massdm are exceptions and work only on NEW_SERVER."""
    if ctx.guild is None:
        # Keep commands from being used in DMs unless explicitly coded.
        return False

    if ctx.command and ctx.command.name in NEW_SERVER_ONLY_COMMANDS:
        return ctx.guild.id == NEW_SERVER_ID

    return ctx.guild.id == OLD_SERVER_ID


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        if ctx.guild:
            await deny(ctx.message, "❌ هذا الأمر مخصص للسيرفر المحدد له فقط.")
        return
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ ناقصك واحد من المعطيات المطلوبة.", delete_after=8)
        return
    if isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ لم أجد العضو المحدد.", delete_after=8)
        return
    if isinstance(error, commands.BadArgument):
        await ctx.send("❌ صيغة الأمر غير صحيحة.", delete_after=8)
        return
    print(f"Command error in {ctx.command}: {error}")
    traceback.print_exception(type(error), error, error.__traceback__)


# ============================================================
# READY / MEMBER JOIN
# ============================================================

@bot.event
async def on_ready():
    load_data()
    print(f"Logged in as {bot.user} ({bot.user.id})")
    print("7R COMMUNITY bot is ready.")
    print(f"Old server: {OLD_SERVER_ID}")
    print(f"New server: {NEW_SERVER_ID}")


@bot.event
async def on_member_join(member):
    try:
        class WelcomeView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)
                self.add_item(discord.ui.Button(
                    label="اضغط هنا للانتقال إلى القناة المخصصة",
                    style=discord.ButtonStyle.link,
                    url=f"https://discord.com/channels/{member.guild.id}/{WELCOME_CHANNEL_ID}"
                ))

        embed = discord.Embed(
            title="✨ مرحباً بك في سيرفرنا!",
            description=(
                f"مرحباً بك يا {member.mention} في سيرفر **{member.guild.name}**!\n\n"
                "نحن سعداء بانضمامك إلينا 🚀.\n"
                "للبدء، ندعوك لزيارة هذه الروم المهمة:\n"
                "👉 اضغط الزر أدناه للانتقال المباشر للقناة المخصصة."
            ),
            color=discord.Color.gold()
        )
        embed.set_footer(text="Made with ❤️ by 7R COMMUNITY")
        await member.send(embed=embed, view=WelcomeView())
    except Exception as e:
        print(f"Could not send welcome DM to {member}: {e}")


# ============================================================
# MESSAGE HANDLER
# ============================================================

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # DM relay to the two admins.
    if isinstance(message.channel, discord.DMChannel) and not message.content.startswith("$"):
        for admin_id in ADMIN_IDS:
            try:
                admin_user = await bot.fetch_user(admin_id)
                if admin_user:
                    embed = discord.Embed(
                        title="📩 رسالة جديدة في خاص البوت (DM)",
                        description=(
                            f"👤 **من العضو:** {message.author.mention} "
                            f"(`{message.author.id}`)\n\n"
                            f"💬 **النص:**\n{message.content}"
                        ),
                        color=discord.Color.blurple()
                    )
                    await admin_user.send(embed=embed)
            except Exception as e:
                print(f"DM relay error: {e}")
        return

    # Sensitive word filter remains on OLD_SERVER only.
    if message.guild and message.guild.id == OLD_SERVER_ID and not message.content.startswith("$"):
        content_lower = message.content.lower()
        if any(w in content_lower for w in [
            "كيف اصنع", "كيف أنشئ", "كيف اسوي", "صنع ايميل", "طريقة صنع", "كيفاش نسوي"
        ]):
            await message.reply(
                f"أهلاً بك يا بطل! 🌟 طريقتنا سهلة، زُر الروم المخصص هنا:\n"
                f"👉 <#{WELCOME_CHANNEL_ID}>"
            )
            return

        content = message.content
        contains_sensitive = False
        for word, replacement in SENSITIVE_WORDS.items():
            if word in content.lower():
                content = content.replace(word, replacement)
                contains_sensitive = True

        if contains_sensitive:
            try:
                await message.delete()
            except Exception:
                pass
            try:
                await message.author.send(
                    embed=discord.Embed(
                        title="⚠️ تنبيه أمني: تم حذف رسالتك",
                        description=(
                            f"مرحباً يا {message.author.mention}, تم حذف رسالتك "
                            "لتفادي البلاغات."
                        ),
                        color=discord.Color.orange()
                    )
                )
                await message.author.send(f"```{content}```")
            except Exception:
                pass
            return

    await bot.process_commands(message)


# ============================================================
# TICKET PANEL VIEWS
# ============================================================

class SupportPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="فتح تذكرة دعم فني",
        emoji="🛠️",
        style=discord.ButtonStyle.primary,
        custom_id="7r_open_support"
    )
    async def open_support(self, interaction: discord.Interaction, button):
        await create_ticket(interaction, "support")


class MediatorPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="فتح تذكرة وسيط",
        emoji="🤝",
        style=discord.ButtonStyle.success,
        custom_id="7r_open_mediator"
    )
    async def open_mediator(self, interaction: discord.Interaction, button):
        await create_ticket(interaction, "mediator")


class ClaimTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="استلام التذكرة",
        emoji="📥",
        style=discord.ButtonStyle.success,
        custom_id="7r_claim_ticket"
    )
    async def claim(self, interaction: discord.Interaction, button):
        channel = interaction.channel
        record = ticket_record(channel)

        if not record or record.get("type") != "mediator":
            return await interaction.response.send_message(
                "❌ هذه ليست تذكرة وسطاء صالحة.", ephemeral=True
            )

        if record.get("mediator_id"):
            return await interaction.response.send_message(
                f"❌ التذكرة مستلمة مسبقاً من <@{record['mediator_id']}>.",
                ephemeral=True
            )

        mediator_role = interaction.guild.get_role(MEDIATOR_ROLE_ID)
        if not mediator_role or mediator_role not in interaction.user.roles:
            return await interaction.response.send_message(
                "❌ هذا الزر مخصص للوسطاء فقط.", ephemeral=True
            )

        record["mediator_id"] = interaction.user.id
        record["claimed_at"] = datetime.utcnow().isoformat()
        save_data()

        overwrites = channel.overwrites_for(interaction.user)
        overwrites.view_channel = True
        overwrites.send_messages = True
        overwrites.read_message_history = True

        try:
            await channel.set_permissions(
                interaction.user,
                overwrite=overwrites,
                reason="Mediator claimed ticket"
            )
        except Exception:
            pass

        button.disabled = True
        button.label = f"مستلمة من {interaction.user.display_name}"

        creator_id = record.get("creator_id")
        creator_mention = f"<@{creator_id}>"

        embed = discord.Embed(
            title="🤝 تم استلام تذكرة الوسيط",
            description=(
                f"تم استلام التذكرة من طرف {interaction.user.mention}\n"
                f"العميل: {creator_mention}\n\n"
                "**- سلعه الطرف الاول :**\n"
                "**- سلعه الطرف الثاني :**\n"
                "**- يوزر الطرف الثاني :**"
            ),
            color=discord.Color.green()
        )
        embed.set_footer(text="7R COMMUNITY • نظام الوسطاء")

        await interaction.response.edit_message(view=self)
        await channel.send(content=creator_mention, embed=embed)

        # Add the mediator role to the channel explicitly.
        if mediator_role:
            try:
                await channel.set_permissions(
                    mediator_role,
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True
                )
            except Exception:
                pass


class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="إغلاق التذكرة 🔒",
        style=discord.ButtonStyle.danger,
        custom_id="7r_close_ticket"
    )
    async def close_ticket(self, interaction: discord.Interaction, button):
        record = ticket_record(interaction.channel)
        if not record:
            return await interaction.response.send_message(
                "❌ هذه ليست تذكرة.", ephemeral=True
            )

        if not (
            is_admin(interaction.user.id)
            or user_is_ticket_creator(interaction.user, interaction.channel)
            or user_is_current_mediator(interaction.user, interaction.channel)
        ):
            return await interaction.response.send_message(
                "❌ ما عندكش صلاحية تسد هاد التكت.", ephemeral=True
            )

        await interaction.response.send_message(
            "⚠️ سيتم إغلاق التذكرة وحفظ سجلها خلال ثانيتين..."
        )
        await asyncio.sleep(2)
        await finalize_ticket(interaction.channel, interaction.user)


# ============================================================
# TICKET CREATION
# ============================================================

async def create_ticket(interaction, ticket_type):
    guild = interaction.guild

    if guild.id != OLD_SERVER_ID:
        return await interaction.response.send_message(
            "❌ نظام التذاكر هذا مخصص للسيرفر الأساسي فقط.",
            ephemeral=True
        )

    category_id = SUPPORT_CATEGORY_ID if ticket_type == "support" else MEDIATOR_CATEGORY_ID
    category = guild.get_channel(category_id)

    if not isinstance(category, discord.CategoryChannel):
        return await interaction.response.send_message(
            "❌ لم أجد الكاتيجوري المحددة للتذاكر. تأكد من الآيدي.",
            ephemeral=True
        )

    # Prevent duplicate open ticket of same type by same user.
    for rec in data["ticket_records"].values():
        if (
            str(rec.get("creator_id")) == str(interaction.user.id)
            and rec.get("type") == ticket_type
            and not rec.get("closed")
        ):
            existing = guild.get_channel(int(rec.get("channel_id", 0)))
            if existing:
                return await interaction.response.send_message(
                    f"❌ عندك تذكرة مفتوحة بالفعل: {existing.mention}",
                    ephemeral=True
                )

    data["ticket_counter"] = int(data.get("ticket_counter", 0)) + 1
    ticket_number = data["ticket_counter"]

    prefix = "وسيط" if ticket_type == "mediator" else "دعم"
    safe_name = interaction.user.name.lower().replace(" ", "-")[:30]
    channel_name = f"{prefix}-{ticket_number}-{safe_name}"

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            attach_files=True,
            embed_links=True
        )
    }

    # Support staff role.
    support_role = guild.get_role(SUPPORT_ROLE_ID)
    mediator_role = guild.get_role(MEDIATOR_ROLE_ID)

    if ticket_type == "support" and support_role:
        overwrites[support_role] = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True
        )

    if ticket_type == "mediator" and mediator_role:
        overwrites[mediator_role] = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True
        )

    try:
        channel = await guild.create_text_channel(
            name=channel_name,
            overwrites=overwrites,
            category=category,
            topic=f"7R TICKET #{ticket_number} | {ticket_type} | {interaction.user.id}"
        )
    except Exception as e:
        return await interaction.response.send_message(
            f"❌ تعذر إنشاء التذكرة: `{e}`",
            ephemeral=True
        )

    record = {
        "channel_id": channel.id,
        "ticket_number": ticket_number,
        "type": ticket_type,
        "creator_id": interaction.user.id,
        "mediator_id": None,
        "party1_id": None,
        "party2_id": None,
        "item1": "",
        "item2": "",
        "created_at": datetime.utcnow().isoformat(),
        "claimed_at": None,
        "closed": False,
    }
    data["ticket_records"][str(channel.id)] = record
    active_tickets[channel.id] = record
    save_data()

    if ticket_type == "mediator":
        try:
            role = guild.get_role(MEDIATOR_CLIENT_ROLE_ID)
            if role and role not in interaction.user.roles:
                await interaction.user.add_roles(
                    role, reason="Opened mediator ticket"
                )
        except Exception:
            pass

        mention = f"<@&{MEDIATOR_ROLE_ID}> {interaction.user.mention}"
        embed = discord.Embed(
            title=f"🤝 تذكرة وسيط #{ticket_number}",
            description=(
                f"مرحباً {interaction.user.mention}!\n\n"
                "تم فتح تذكرة وسيط. سيتم استلامها من طرف أحد الوسطاء.\n"
                "بعد الاستلام سيظهر للوسيط نموذج بيانات الطرفين."
            ),
            color=discord.Color.green()
        )
        embed.set_footer(text="7R COMMUNITY • نظام الوسطاء")
        await channel.send(
            content=mention,
            embed=embed,
            view=ClaimTicketView()
        )
    else:
        mention = f"<@&{SUPPORT_ROLE_ID}> {interaction.user.mention}"
        embed = discord.Embed(
            title=f"🛠️ تذكرة دعم فني #{ticket_number}",
            description=(
                f"مرحباً {interaction.user.mention}!\n"
                "تم فتح تذكرة الدعم الفني بنجاح.\n"
                "سيتم الرد عليك من طرف فريق الدعم قريباً."
            ),
            color=discord.Color.blurple()
        )
        embed.set_footer(text="7R COMMUNITY • الدعم الفني")
        await channel.send(
            content=mention,
            embed=embed,
            view=CloseTicketView()
        )

    await interaction.response.send_message(
        f"✅ تم فتح التذكرة: {channel.mention}",
        ephemeral=True
    )


# ============================================================
# TICKET SETUP
# ============================================================

def build_panel_embed(title, description, color, guild):
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.utcnow()
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.set_footer(text="7R COMMUNITY • نظام التذاكر")
    return embed


@bot.command(name="ticketsetup", help="خاص بالمالكَين لإرسال بانلات التذاكر والإحصائيات.")
async def ticketsetup(ctx):
    if not is_admin(ctx.author.id):
        return await ctx.send("❌ هذا الأمر خاص بالمالكَين فقط!", delete_after=8)

    if not is_old_server(ctx):
        return await deny(ctx.message)

    try:
        await ctx.message.delete()
    except Exception:
        pass

    channel = ctx.guild.get_channel(TICKET_PANEL_CHANNEL_ID)
    if not channel:
        return await ctx.send(
            "❌ لم أجد روم بانل التذاكر.",
            delete_after=8
        )

    mediator_count = 0
    mediator_role = ctx.guild.get_role(MEDIATOR_ROLE_ID)
    if mediator_role:
        mediator_count = len([m for m in mediator_role.members if not m.bot])

    opened_mediator = sum(
        1 for r in data["ticket_records"].values()
        if r.get("type") == "mediator"
    )

    # Support panel.
    support_embed = build_panel_embed(
        "🛠️ 7R COMMUNITY | الدعم الفني",
        (
            "إذا عندك مشكلة أو استفسار وتحتاج تدخل الإدارة، "
            "اضغط على الزر لفتح تذكرة دعم فني.\n\n"
            "⚠️ لا تفتح تذكرة بدون سبب."
        ),
        discord.Color.blurple(),
        ctx.guild
    )
    await channel.send(embed=support_embed, view=SupportPanelView())

    await send_divider(channel)

    # Mediator panel.
    mediator_embed = build_panel_embed(
        "🤝 7R COMMUNITY | الوسطاء",
        (
            "لإجراء عملية توسط آمنة داخل السيرفر، اضغط على زر فتح تذكرة وسيط.\n\n"
            "سيتم تنبيه الوسطاء تلقائياً، وأول وسيط يستلم التذكرة يتكلف بالعملية."
        ),
        discord.Color.green(),
        ctx.guild
    )
    await channel.send(embed=mediator_embed, view=MediatorPanelView())

    await send_divider(channel)

    # Professional statistics panel.
    stats_embed = discord.Embed(
        title="📊 7R COMMUNITY | إحصائيات الوسطاء",
        description=(
            f"🤝 **عدد الوسطاء:** `{mediator_count}`\n"
            f"🎫 **مجموع تذاكر الوسطاء المفتوحة:** `{opened_mediator}`\n"
            f"🏆 **مجموع التوسطات الناجحة:** "
            f"`{sum(int(v) for v in data['mediator_tickets'].values())}`\n\n"
            "يتم تحديث أرقام الوسطاء والنقاط تلقائياً مع كل عملية ناجحة."
        ),
        color=discord.Color.gold(),
        timestamp=datetime.utcnow()
    )
    if ctx.guild.icon:
        stats_embed.set_thumbnail(url=ctx.guild.icon.url)
    stats_embed.set_footer(text="7R COMMUNITY • Statistics")
    await channel.send(embed=stats_embed)

    await ctx.send("✅ تم إرسال بانل الدعم والوسطاء والإحصائيات.", delete_after=8)


# ============================================================
# MEDIATOR COMMANDS
# ============================================================

@bot.command(name="وسيط", help="لإضافة عضو إلى تذكرة الوسيط.")
async def add_party(ctx, member: discord.Member):
    if not is_old_server(ctx):
        return await deny(ctx.message)

    if not ticket_is_mediator(ctx.channel):
        return await ctx.send("❌ هذا الأمر يعمل داخل تكت وسيط فقط.", delete_after=8)

    record = ticket_record(ctx.channel)

    if not (
        is_admin(ctx.author.id)
        or user_is_current_mediator(ctx.author, ctx.channel)
    ):
        return await ctx.send(
            "❌ هذا الأمر خاص بالوسيط المستلم للتذكرة.",
            delete_after=8
        )

    if member.bot:
        return await ctx.send("❌ لا يمكن إضافة بوت كطرف.", delete_after=8)

    try:
        await ctx.channel.set_permissions(
            member,
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            attach_files=True,
            embed_links=True
        )
        await ctx.send(
            f"✅ تمت إضافة {member.mention} إلى التذكرة بنجاح.",
            delete_after=8
        )
    except Exception as e:
        await ctx.send(f"❌ فشل إضافة العضو: `{e}`", delete_after=8)


@bot.command(name="طرفين", aliases=["parties"], help="خاص بالوسيط لتحديد طرفي العملية.")
async def set_parties(ctx, party1: discord.Member, party2: discord.Member):
    if not is_old_server(ctx):
        return await deny(ctx.message)

    if not ticket_is_mediator(ctx.channel):
        return await ctx.send("❌ هذا الأمر يعمل داخل تكت وسيط فقط.", delete_after=8)

    if not (
        is_admin(ctx.author.id)
        or user_is_current_mediator(ctx.author, ctx.channel)
    ):
        return await ctx.send("❌ هذا الأمر خاص بالوسيط.", delete_after=8)

    if party1.id == party2.id:
        return await ctx.send("❌ خاصك جوج أعضاء مختلفين.", delete_after=8)

    record = ticket_record(ctx.channel)
    record["party1_id"] = party1.id
    record["party2_id"] = party2.id
    save_data()

    for member in (party1, party2):
        try:
            await ctx.channel.set_permissions(
                member,
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            )
        except Exception:
            pass

    await ctx.send(
        (
            f"✅ تم تحديد الطرفين:\n"
            f"**الطرف الأول:** {party1.mention}\n"
            f"**الطرف الثاني:** {party2.mention}\n\n"
            "تمت إضافتهما للتكت تلقائياً."
        ),
        delete_after=12
    )


@bot.command(name="سلع", aliases=["items"], help="تحديد السلعتين في تكت الوسيط.")
async def set_items(ctx, *, items_text: str):
    if not is_old_server(ctx):
        return await deny(ctx.message)

    if not ticket_is_mediator(ctx.channel):
        return await ctx.send("❌ هذا الأمر يعمل داخل تكت وسيط فقط.", delete_after=8)

    if not (
        is_admin(ctx.author.id)
        or user_is_current_mediator(ctx.author, ctx.channel)
    ):
        return await ctx.send("❌ هذا الأمر خاص بالوسيط.", delete_after=8)

    parts = [p.strip() for p in items_text.split("|", 1)]
    record = ticket_record(ctx.channel)

    if len(parts) == 2:
        record["item1"] = parts[0]
        record["item2"] = parts[1]
    else:
        record["item1"] = items_text.strip()
        record["item2"] = "غير محددة"

    save_data()
    await ctx.send(
        (
            "✅ تم حفظ الأغراض:\n"
            f"**- سلعه الطرف الاول :** {record['item1']}\n"
            f"**- سلعه الطرف الثاني :** {record['item2']}"
        ),
        delete_after=12
    )


@bot.command(name="تنبيه", help="إرسال تنبيه الوسيط للطرفين.")
async def mediator_warning(ctx):
    if not is_old_server(ctx):
        return await deny(ctx.message)

    if not ticket_is_mediator(ctx.channel):
        return await ctx.send("❌ هذا الأمر يعمل داخل تكت وسيط فقط.", delete_after=8)

    record = ticket_record(ctx.channel)
    if not (
        is_admin(ctx.author.id)
        or user_is_current_mediator(ctx.author, ctx.channel)
    ):
        return await ctx.send("❌ هذا الأمر خاص بالوسيط.", delete_after=8)

    p1 = record.get("party1_id")
    p2 = record.get("party2_id")

    if not p1 or not p2:
        return await ctx.send(
            "❌ حدد الطرفين أولاً باستعمال `$طرفين @الطرف1 @الطرف2`.",
            delete_after=10
        )

    warning = (
        "- **السيرفر و الوسطاء يخليان مسؤولية تماما ولا يتحملان اي تعويض "
        "اذا تم سحب الحساب اثناء او بعد التوسط**\n"
        "**السبب :**\n"
        "**`#` اللعبة شددت على حماية الحسابات و قد اصبحت الحسابات في خطر "
        "لتقفيل الحساب اثناء التوسط او ترجيعه من الطرف الثاني**\n"
        "__** مثلا **__\n"
        "**`#` قام الطرف تاني بسحب الحساب عن طريق دعم اللعبة فالوسيط و السيرفر "
        "ليس لهم دخل في امر الحساب الذي تم استرجاعه**\n"
        "**هل انتم موافقون؟**"
    )

    await ctx.send(
        content=f"<@{p1}> <@{p2}>",
        embed=discord.Embed(
            title="⚠️ تنبيه مهم قبل التوسط",
            description=warning,
            color=discord.Color.orange()
        )
    )


@bot.command(name="تخلي", help="يجعل الوسيط يتخلى عن التذكرة ويعيد زر الاستلام.")
async def release_ticket(ctx):
    if not is_old_server(ctx):
        return await deny(ctx.message)

    if not ticket_is_mediator(ctx.channel):
        return await ctx.send("❌ هذا الأمر يعمل داخل تكت وسيط فقط.", delete_after=8)

    record = ticket_record(ctx.channel)
    if not (
        is_admin(ctx.author.id)
        or user_is_current_mediator(ctx.author, ctx.channel)
    ):
        return await ctx.send("❌ هذا الأمر خاص بالوسيط المستلم.", delete_after=8)

    old_mediator_id = record.get("mediator_id")
    record["mediator_id"] = None
    record["claimed_at"] = None
    save_data()

    # Remove current mediator-specific access, but keep mediator role access.
    if old_mediator_id and not is_admin(old_mediator_id):
        try:
            await ctx.channel.set_permissions(old_mediator_id, overwrite=None)
        except Exception:
            pass

    await ctx.send(
        content=f"<@&{MEDIATOR_ROLE_ID}>",
        embed=discord.Embed(
            title="🔓 التذكرة متاحة للاستلام من جديد",
            description=(
                f"الوسيط السابق {f'<@{old_mediator_id}>' if old_mediator_id else 'غير معروف'} "
                "تخلى عن التذكرة.\n"
                "يمكن لأي وسيط متاح استلامها الآن."
            ),
            color=discord.Color.orange()
        ),
        view=ClaimTicketView()
    )


@bot.command(name="end", help="إنهاء التوسط وإضافة نقطة للوسيط.")
async def end_mediation(ctx):
    if not is_old_server(ctx):
        return await deny(ctx.message)

    if not ticket_is_mediator(ctx.channel):
        return await ctx.send("❌ هذا الأمر يعمل داخل تكت وسيط فقط.", delete_after=8)

    record = ticket_record(ctx.channel)
    mediator_id = record.get("mediator_id")

    if not mediator_id:
        return await ctx.send("❌ لا يوجد وسيط مستلم للتكت.", delete_after=8)

    if ctx.author.id != mediator_id and not is_admin(ctx.author.id):
        return await ctx.send("❌ فقط الوسيط المستلم يمكنه إنهاء التوسط.", delete_after=8)

    # Prevent double completion.
    if record.get("completed"):
        return await ctx.send("❌ تم إنهاء هذه التذكرة مسبقاً.", delete_after=8)

    record["completed"] = True
    record["completed_at"] = datetime.utcnow().isoformat()
    save_data()

    # One successful mediator ticket = 1 point.
    add_mediator_point(mediator_id, 1)

    mediator = await get_member(ctx.guild, mediator_id)
    mediator_mention = mediator.mention if mediator else f"<@{mediator_id}>"

    p1 = record.get("party1_id")
    p2 = record.get("party2_id")

    # Professional completion message.
    completion_text = (
        f"- **تمت عملية التوسط بنجاح من الطرف الوسيط {mediator_mention}**\n"
        "- **يرجى كتابة تم و تقييم الوسيط من طرف رسالة بتوصلك بلخاص**\n"
        "- **احنا مش مسؤولين على اي شي يحصل بعد 5 دقايق من انتهاء التبادل**\n"
        "- **لو عجبتك خدمه سيرفرنا لا تنسى تعيد تطلب مننا مره ثانية**\n"
        f"- **للحصول على رتبة عميل مميز (<@{VIP_CLIENT_ROLE_ID}>) يرجى طلب وسيط "
        "10 مرات و ان يتم التوسط بنجاح، صور دلائلك و تعال تستلم رتبتك**"
    )

    await ctx.send(
        content=f"{p1 and f'<@{p1}>' or ''} {p2 and f'<@{p2}>' or ''}",
        embed=discord.Embed(
            title="✅ تمت عملية التوسط بنجاح",
            description=completion_text,
            color=discord.Color.green()
        )
    )

    # Send rating request to both parties.
    rating_view_1 = RatingView(
        ticket_number=record["ticket_number"],
        mediator_id=mediator_id,
        client_id=p1
    )
    rating_view_2 = RatingView(
        ticket_number=record["ticket_number"],
        mediator_id=mediator_id,
        client_id=p2
    )

    for party_id, view in ((p1, rating_view_1), (p2, rating_view_2)):
        if not party_id:
            continue
        try:
            user = await bot.fetch_user(int(party_id))
            await user.send(
                embed=discord.Embed(
                    title="⭐ تقييم الوسيط | 7R COMMUNITY",
                    description=(
                        f"تم إنهاء التوسط رقم **#{record['ticket_number']}**.\n"
                        f"الوسيط: {mediator_mention}\n\n"
                        "من فضلك قيّم الوسيط بالنجوم:"
                    ),
                    color=discord.Color.gold()
                ),
                view=view
            )
        except Exception as e:
            print(f"Rating DM failed for {party_id}: {e}")

    # Announce successful mediation in the result channel.
    result_channel = ctx.guild.get_channel(MEDIATOR_RESULTS_CHANNEL_ID)
    if result_channel:
        await send_mediator_result(result_channel, record, mediator_mention)

    # Close after a short delay, preserving the final messages in transcript.
    await asyncio.sleep(3)
    await finalize_ticket(ctx.channel, ctx.author)


# ============================================================
# RATING SYSTEM
# ============================================================

class RatingView(discord.ui.View):
    def __init__(self, ticket_number, mediator_id, client_id):
        super().__init__(timeout=None)
        self.ticket_number = ticket_number
        self.mediator_id = mediator_id
        self.client_id = client_id

    async def handle_rating(self, interaction, stars):
        if interaction.user.id != int(self.client_id):
            return await interaction.response.send_message(
                "❌ هذا التقييم مخصص للشخص المحدد فقط.",
                ephemeral=True
            )

        ticket_key = str(self.ticket_number)
        existing = data["ratings"].get(ticket_key)

        # Allow two parties to rate the same ticket.
        if existing is None:
            existing = {"ratings": []}
            data["ratings"][ticket_key] = existing

        for r in existing["ratings"]:
            if str(r.get("client_id")) == str(interaction.user.id):
                return await interaction.response.send_message(
                    "❌ سبق لك تقييم هذه العملية.",
                    ephemeral=True
                )

        rating_value = int(stars)
        existing["ratings"].append({
            "client_id": interaction.user.id,
            "mediator_id": self.mediator_id,
            "rating": rating_value,
            "created_at": datetime.utcnow().isoformat()
        })

        # The mediator result record is also kept for easy averaging.
        data["ratings"][ticket_key] = existing
        save_data()

        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(
            content=f"❤️ شكراً لك! تم تسجيل تقييمك: **{'⭐' * rating_value}**",
            view=self
        )

        # Update result channel after a rating.
        guild = None
        for g in bot.guilds:
            if g.id == OLD_SERVER_ID:
                guild = g
                break
        if guild:
            channel = guild.get_channel(MEDIATOR_RESULTS_CHANNEL_ID)
            record = get_ticket_record_by_number(self.ticket_number)
            if channel and record:
                mediator = await get_member(guild, self.mediator_id)
                mediator_mention = (
                    mediator.mention if mediator else f"<@{self.mediator_id}>"
                )
                await send_mediator_result(
                    channel, record, mediator_mention,
                    rating_override=True
                )


# ============================================================
# RESULT LOG
# ============================================================

async def send_mediator_result(
    channel,
    record,
    mediator_mention,
    rating_override=False
):
    ticket_number = record.get("ticket_number")
    mediator_id = record.get("mediator_id")
    p1 = record.get("party1_id")
    p2 = record.get("party2_id")

    # Client shown in the requested format = party 1 by default.
    client_id = p1 or record.get("creator_id")
    client_mention = f"<@{client_id}>" if client_id else "غير محدد"

    item1 = record.get("item1") or "غير محددة"
    item2 = record.get("item2") or "غير محددة"

    ratings_for_ticket = data["ratings"].get(str(ticket_number), {}).get("ratings", [])
    current_ticket_avg = (
        sum(float(r["rating"]) for r in ratings_for_ticket) / len(ratings_for_ticket)
        if ratings_for_ticket else 0
    )
    mediator_avg = average_rating_for_mediator(mediator_id) if mediator_id else 0

    embed = discord.Embed(
        title=f"☑️ | تكت الوسيط رقم `{ticket_number}`",
        description=(
            f"`-` **العميل:** {client_mention}\n"
            f"`-` **الوسيط:** {mediator_mention}\n"
            f"`-` **عدد التذاكر:** `{get_mediator_ticket_count(mediator_id) if mediator_id else 0}`\n"
            f"`-` **رقــم التذكرة:** `{ticket_number}`\n"
            f"`-` **التقييم:** "
            f"`{f'{current_ticket_avg:.1f}/5' if current_ticket_avg else 'في انتظار التقييم'}`\n"
            f"`-` **متوسط تقييم الوسيط:** "
            f"`{f'{mediator_avg:.2f}/5' if mediator_avg else 'لا يوجد'}`\n"
            f"`-` **الأغراض التي تم توسطها:** `{item1}` و `{item2}`"
        ),
        color=discord.Color.gold(),
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text="7R COMMUNITY • Mediator Records")
    await channel.send(embed=embed)
    await send_divider(channel)


# ============================================================
# DELETE / TRANSCRIPT
# ============================================================

async def finalize_ticket(channel, closed_by):
    record = ticket_record(channel)
    if not record or record.get("closed"):
        return

    record["closed"] = True
    record["closed_at"] = datetime.utcnow().isoformat()
    record["closed_by"] = closed_by.id

    # Save transcript before deletion.
    transcript = await create_text_transcript(channel)

    # Send transcript to the specified log room.
    log_channel = channel.guild.get_channel(TICKET_LOG_CHANNEL_ID)
    if log_channel:
        text_file = discord.File(
            io.BytesIO(transcript.encode("utf-8")),
            filename=f"ticket-{record['ticket_number']}.txt"
        )

        mediator_log = (
            f"<@{record.get('mediator_id')}>"
            if record.get("mediator_id") else "غير مستلم"
        )
        party1_log = (
            f"<@{record.get('party1_id')}>"
            if record.get("party1_id") else "غير محدد"
        )
        party2_log = (
            f"<@{record.get('party2_id')}>"
            if record.get("party2_id") else "غير محدد"
        )
        log_embed = discord.Embed(
            title=f"🗃️ سجل تذكرة #{record['ticket_number']}",
            description=(
                f"**النوع:** {record.get('type')}\n"
                f"**صاحب التذكرة:** <@{record.get('creator_id')}>\n"
                f"**الوسيط:** {mediator_log}\n"
                f"**الطرف الأول:** {party1_log}\n"
                f"**الطرف الثاني:** {party2_log}\n"
                f"**أغلق بواسطة:** {closed_by.mention}"
            ),
            color=discord.Color.dark_gold(),
            timestamp=datetime.utcnow()
        )
        await log_channel.send(embed=log_embed, file=text_file)

    # Remove from active tickets but keep permanent record in JSON.
    active_tickets.pop(channel.id, None)
    save_data()

    try:
        await channel.delete(reason=f"7R ticket closed by {closed_by}")
    except Exception as e:
        print(f"Ticket deletion failed: {e}")


@bot.command(name="delete", help="حذف تكت وإرسال سجل كامل لها.")
async def delete_ticket_command(ctx):
    if not is_old_server(ctx):
        return await deny(ctx.message)

    if not ticket_record(ctx.channel):
        return await ctx.send("❌ هذه ليست تذكرة مسجلة.", delete_after=8)

    if not is_admin(ctx.author.id):
        return await ctx.send("❌ هذا الأمر خاص بالمالكَين.", delete_after=8)

    await ctx.send("🗃️ يتم حفظ سجل التكت ثم حذفها...", delete_after=3)
    await asyncio.sleep(2)
    await finalize_ticket(ctx.channel, ctx.author)


# ============================================================
# MEDIATOR MANAGEMENT
# ============================================================

@bot.command(name="reset", help="للمالكَين: تصفير نقاط وسيط.")
async def reset_points(ctx, member: discord.Member):
    if not is_old_server(ctx):
        return await deny(ctx.message)

    if not is_admin(ctx.author.id):
        return await ctx.send("❌ هذا الأمر خاص بالمالكَين.", delete_after=8)

    set_mediator_points(member.id, 0)
    data["mediator_tickets"][str(member.id)] = 0
    save_data()

    await ctx.send(
        f"♻️ تم تصفير نقاط وتذاكر الوسيط {member.mention}.",
        delete_after=10
    )


@bot.command(name="setpoints", help="للمالكَين: تحديد نقاط وسيط.")
async def set_points(ctx, member: discord.Member, amount: int):
    if not is_old_server(ctx):
        return await deny(ctx.message)

    if not is_admin(ctx.author.id):
        return await ctx.send("❌ هذا الأمر خاص بالمالكَين.", delete_after=8)

    if amount < 0:
        return await ctx.send("❌ النقاط لا يمكن أن تكون سالبة.", delete_after=8)

    set_mediator_points(member.id, amount)
    # Keep ticket count aligned with the manually set point count.
    data["mediator_tickets"][str(member.id)] = amount
    save_data()

    await ctx.send(
        f"✅ تم تعديل نقاط {member.mention} إلى **{amount}** نقطة.",
        delete_after=10
    )


@bot.command(name="top", help="لائحة أفضل الوسطاء.")
async def top_mediators(ctx):
    if not is_old_server(ctx):
        return await deny(ctx.message)

    rows = []
    for uid in all_mediator_ids():
        member = await get_member(ctx.guild, uid)
        if member:
            rows.append((
                uid,
                get_mediator_points(uid),
                get_mediator_ticket_count(uid),
                average_rating_for_mediator(uid)
            ))

    rows.sort(key=lambda x: (x[1], x[3]), reverse=True)

    if not rows:
        return await ctx.send("📊 لا توجد نقاط للوسطاء بعد.", delete_after=8)

    description = []
    medals = ["🥇", "🥈", "🥉"]

    for index, (uid, points, tickets, avg) in enumerate(rows[:10], 1):
        prefix = medals[index - 1] if index <= 3 else f"`#{index}`"
        description.append(
            f"{prefix} <@{uid}>\n"
            f"   └ 🎫 التذاكر الناجحة: `{tickets}` | ⭐ النقاط: `{points}` | "
            f"⭐ المتوسط: `{avg:.2f}/5`"
        )

    embed = discord.Embed(
        title="🏆 7R COMMUNITY | TOP MEDIATORS",
        description="\n\n".join(description),
        color=discord.Color.gold()
    )
    embed.set_footer(text="كل تكت وسيط ناجح = نقطة واحدة")
    await ctx.send(embed=embed)


# ============================================================
# ONLINE / DND
# ============================================================

@bot.command(name="online", help="للمالكَين: عرض الأعضاء غير المتصلين أو DND.")
async def online_command(ctx):
    if not is_old_server(ctx):
        return await deny(ctx.message)

    if not is_admin(ctx.author.id):
        return await ctx.send("❌ هذا الأمر خاص بالمالكَين.", delete_after=8)

    members = [
        m for m in ctx.guild.members
        if not m.bot and m.status in (discord.Status.offline, discord.Status.dnd)
    ]

    if not members:
        return await ctx.send(
            "✅ لا يوجد حالياً أعضاء بحالة Offline أو Do Not Disturb.",
            delete_after=10
        )

    # Discord embeds have a practical size limit, so show first 40.
    shown = members[:40]
    lines = []
    for m in shown:
        status = "🔴 Offline" if m.status == discord.Status.offline else "⛔ DND"
        lines.append(f"{status} • {m.mention} (`{m.id}`)")

    embed = discord.Embed(
        title="📡 أعضاء Offline / DND",
        description="\n".join(lines),
        color=discord.Color.orange()
    )
    embed.set_footer(text=f"المجموع: {len(members)} عضو | المعروض: {len(shown)}")
    await ctx.send(embed=embed)


# ============================================================
# OLD COMMANDS
# ============================================================

@bot.command(name="f", aliases=["finish"], help="للمالك فقط: إضافة 1.5 مليون نقطة للزبون.")
async def quick_ticket(ctx, member: discord.Member):
    if not is_owner(ctx.author.id):
        return await ctx.send(
            "❌ عذراً، هذا الأمر مخصص لمالك السيرفر فقط!",
            delete_after=10
        )

    reward_amount = 1500000
    update_store_credit(member.id, reward_amount)

    try:
        await ctx.message.delete()
    except Exception:
        pass

    logs_channel = bot.get_channel(LOGS_CHANNEL_ID)
    if logs_channel:
        embed = discord.Embed(
            title="🎯 إنجاز صفقة تكت جديدة وتسليم الهدية",
            description=(
                f"👤 **الزبون:** {member.mention} (`{member.id}`)\n"
                f"🛠️ **الإداري المشرف:** {ctx.author.mention}\n"
                f"🏛️ **التكت:** {ctx.channel.name}\n\n"
                f"🎁 **الهدية المضافة:** `1,500,000` نقطة\n"
                f"💎 **إجمالي رصيد العضو الحالي:** "
                f"`{get_store_credit(member.id):,}` نقطة"
            ),
            color=discord.Color.green()
        )
        embed.set_footer(text="7R COMMUNITY • Auto Rewards System")
        await logs_channel.send(embed=embed)
        await send_divider(logs_channel)

    await ctx.send(
        f"✅ تم إنهاء التكت، إضافة **1,500,000 نقطة** لـ {member.mention} بنجاح!",
        delete_after=10
    )

    try:
        await member.send(
            embed=discord.Embed(
                title="🎉 مبروك لشراء إيميلك!",
                description=(
                    f"شكراً لتعاملك معنا في سيرفر **{ctx.guild.name}**!\n"
                    f"تمت إضافة **1,500,000 نقطة** إلى رصيدك كهدية ولاء.\n"
                    "يمكنك تفقد رصيدك عبر أمر: `$points`"
                ),
                color=discord.Color.gold()
            )
        )
    except Exception:
        pass


@bot.command(name="setstrat", aliases=["strat", "helpmenu"], help="عرض دليل الأوامر.")
async def setstrat(ctx):
    try:
        await ctx.message.delete()
    except Exception:
        pass

    embed = discord.Embed(
        title="✨ دليل استخدام أوامر 7R COMMUNITY",
        description=(
            "مرحباً بك! 🛒\n"
            "هذه قائمة مختصرة بأهم الأوامر المتاحة لك."
        ),
        color=discord.Color.gold()
    )

    embed.add_field(
        name="💎 النقاط والرصيد",
        value=(
            "`$points` / `$balance` — عرض رصيدك\n"
            "`$transfer @member amount` — تحويل نقاط\n"
            "`$withdraw amount` — طلب سحب"
        ),
        inline=False
    )
    embed.add_field(
        name="🎮 الألعاب",
        value="`$games` • `$xo @member` • `$roulette` • `$rps حجرة/ورقة/مقص`",
        inline=False
    )
    embed.add_field(
        name="🎫 الوسطاء",
        value=(
            "`$وسيط @member` — إضافة طرف للتكت\n"
            "`$طرفين @member1 @member2` — تحديد الطرفين\n"
            "`$سلع item1 | item2` — حفظ الأغراض\n"
            "`$تنبيه` — إرسال التنبيه للطرفين\n"
            "`$تخلي` — التخلي عن التكت\n"
            "`$end` — إنهاء التوسط وإضافة نقطة\n"
            "`$top` — أفضل الوسطاء"
        ),
        inline=False
    )
    embed.add_field(
        name="🛠️ الإدارة",
        value=(
            "`$ticketsetup` — إرسال بانلات التذاكر\n"
            "`$delete` — حذف تكت مع transcript\n"
            "`$reset @member` — تصفير النقاط\n"
            "`$setpoints @member 10` — تعديل النقاط\n"
            "`$online` — Offline / DND\n"
            "`$list` — جميع أوامر البوت"
        ),
        inline=False
    )
    embed.set_footer(text="7R COMMUNITY • تجربة آمنة ومنظمة")
    await ctx.send(embed=embed)
    await send_divider(ctx.channel)


@bot.command(name="say", help="جعل البوت يرسل رسالة رسمية.")
async def say(ctx, *, text: str):
    if not is_admin(ctx.author.id):
        return await ctx.send("❌ للإدارة فقط!", delete_after=8)
    try:
        await ctx.message.delete()
    except Exception:
        pass
    await ctx.send(text)


@bot.command(name="come", help="استدعاء عضو معين إلى الخاص.")
async def come(ctx, member: discord.Member, *, reason: str = "بدون سبب"):
    # User requested mediator usage, but admins can also use it.
    if not (
        is_admin(ctx.author.id)
        or (
            ticket_is_mediator(ctx.channel)
            and user_is_current_mediator(ctx.author, ctx.channel)
        )
    ):
        return await ctx.send("❌ هذا الأمر خاص بالإدارة أو الوسيط المستلم.", delete_after=8)

    try:
        await ctx.message.delete()
    except Exception:
        pass

    embed = discord.Embed(
        title="🚨 استدعاء إداري عاجل",
        description=(
            f"مرحباً {member.mention},\n"
            f"لقد تم استدعاؤك من طرف إدارة/وسيط السيرفر في الروم: "
            f"{ctx.channel.mention}\n\n"
            f"📌 **السبب:** {reason}\n"
            f"🛡️ **السيرفر:** {ctx.guild.name}"
        ),
        color=discord.Color.red()
    )
    embed.set_footer(text="يرجى الاستجابة.")
    try:
        await member.send(embed=embed)
        sent = await ctx.send(
            f"✅ تم إرسال الاستدعاء إلى {member.mention} بنجاح!",
            delete_after=10
        )
    except Exception:
        await ctx.send(
            f"❌ عذراً، خاص العضو {member.mention} مغلق!",
            delete_after=10
        )


@bot.command(name="serverinfo", aliases=["sinfo"], help="معلومات السيرفر.")
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(
        title=f"📊 معلومات سيرفر: {guild.name}",
        color=discord.Color.blue()
    )
    owners_mentions = [f"<@{admin_id}>" for admin_id in ADMIN_IDS]
    embed.add_field(
        name="👑 الإدارة",
        value=", ".join(owners_mentions),
        inline=False
    )
    embed.add_field(name="👥 عدد الأعضاء", value=guild.member_count, inline=True)
    embed.add_field(
        name="📅 تاريخ الإنشاء",
        value=guild.created_at.strftime("%Y-%m-%d"),
        inline=True
    )
    await ctx.send(embed=embed)


# ============================================================
# ADMIN COMMAND LIST
# ============================================================

@bot.command(name="list", aliases=["commands", "cmds"], help="لائحة جميع أوامر البوت.")
async def custom_list(ctx):
    if not is_admin(ctx.author.id):
        return await ctx.send("❌ هذا الأمر خاص بالمالكَين.", delete_after=8)

    commands_list = []

    for c in bot.commands:
        if c.hidden:
            continue

        # Hide aliases from duplicate display.
        aliases = f" | aliases: {', '.join(c.aliases)}" if c.aliases else ""
        commands_list.append(
            f"📌 `${c.name}`{aliases}\n"
            f"   └ {c.help or 'لا يوجد وصف'}"
        )

    commands_list.sort()

    embed = discord.Embed(
        title="📋 7R COMMUNITY | جميع أوامر البوت",
        description="\n\n".join(commands_list),
        color=discord.Color.dark_gold()
    )
    embed.set_footer(
        text="جميع الأوامر العادية في السيرفر الأساسي • tax/massdm في السيرفر الثاني"
    )

    try:
        await ctx.author.send(embed=embed)
        await ctx.send(
            "✅ تم إرسال لائحة الأوامر كاملة إلى الخاص (DM).",
            delete_after=8
        )
    except discord.Forbidden:
        await ctx.send("❌ افتح الخاص (DMs) باش نقدر نصيفطها ليك.", delete_after=8)


# ============================================================
# POINTS / MONEY SYSTEM
# ============================================================

@bot.command(name="points", aliases=["pts", "credit", "balance"], help="عرض رصيد نقاط المتجر.")
async def points(ctx, member: discord.Member = None):
    target = member if member else ctx.author
    bal = get_store_credit(target.id)
    probot_value = bal / EXCHANGE_RATE

    embed = discord.Embed(
        title="💎 رصيد نقاط المتجر",
        description=(
            f"العضو: {target.mention}\n"
            f"🔹 الرصيد: **{bal:,} نقطة**\n"
            f"🔸 تعادل بالبروبوت: **{probot_value:,.1f}**"
        ),
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)


@bot.command(name="transfer", aliases=["pay", "give"], help="تحويل النقاط لعضو.")
async def transfer(ctx, member: discord.Member, amount_str: str):
    amount = parse_amount(amount_str)
    if amount is None or amount <= 0:
        return await ctx.send("❌ يرجى تحديد مبلغ صحيح!", delete_after=10)

    if member.id == ctx.author.id:
        return await ctx.send("❌ لا يمكنك التحويل لنفسك!", delete_after=10)

    if member.bot:
        return await ctx.send("❌ لا يمكنك التحويل لبوت!", delete_after=10)

    sender_bal = get_store_credit(ctx.author.id)
    if sender_bal < amount:
        return await ctx.send(
            f"❌ رصيدك غير كافٍ! رصيدك: `{sender_bal:,}` نقطة.",
            delete_after=10
        )

    update_store_credit(ctx.author.id, -amount)
    update_store_credit(member.id, amount)

    try:
        await ctx.message.delete()
    except Exception:
        pass

    embed = discord.Embed(
        title="💸 عملية تحويل ناجحة",
        description=(
            f"👤 **المحول:** {ctx.author.mention}\n"
            f"🎯 **المستلم:** {member.mention}\n"
            f"💎 **المبلغ:** `{amount:,}` نقطة\n"
            f"📉 **رصيدك الحالي:** `{get_store_credit(ctx.author.id):,}` نقطة"
        ),
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)


@bot.command(name="addpoints", help="للمالك فقط: إضافة نقاط.")
async def addpoints(ctx, member: discord.Member, amount: int):
    if not is_owner(ctx.author.id):
        return await ctx.send("❌ هذا الأمر للمالك فقط!", delete_after=10)

    update_store_credit(member.id, amount)
    await ctx.send(
        f"✅ تمت إضافة `{amount:,}` نقطة لـ {member.mention}",
        delete_after=10
    )


@bot.command(name="removepoints", help="للمالك فقط: خصم نقاط.")
async def removepoints(ctx, member: discord.Member, amount: int):
    if not is_owner(ctx.author.id):
        return await ctx.send("❌ هذا الأمر للمالك فقط!", delete_after=10)

    update_store_credit(member.id, -amount)
    await ctx.send(
        f"✅ تم خصم `{amount:,}` نقطة من {member.mention}",
        delete_after=10
    )


# ============================================================
# TAX / MASSDM - NEW SERVER ONLY
# ============================================================

@bot.command(name="tax", help="حساب الضرائب - يعمل في السيرفر الثاني فقط.")
async def tax(ctx, amount: str):
    parsed = parse_amount(amount)
    if parsed is None or parsed < 0:
        return await ctx.send("❌ الرقم غير صحيح.", delete_after=8)

    t_probot = round(parsed * 0.05)
    total_probot = parsed + t_probot
    mediator_tax_amount = round(parsed * 1.025 * 20 / 19)

    embed = discord.Embed(
        title="🧾 حساب الضرائب والوسيط",
        description=(
            f"🔹 **المبلغ الأصلي:** `{parsed:,}`\n\n"
            f"📊 **ضريبة البروبوت (5%):**\n"
            f"• قيمة الضريبة: `{t_probot:,}`\n"
            f"• المبلغ مع الضريبة: `{total_probot:,}`\n\n"
            f"🤝 **ضريبة الوسيط:**\n"
            f"• المبلغ المطلوب تحويله للوسيط: `{mediator_tax_amount:,}`"
        ),
        color=discord.Color.pink()
    )
    await ctx.send(embed=embed)


@bot.command(
    name="massdm",
    aliases=["broadcast", "dmall"],
    help="للإدارة: إرسال رسالة للأعضاء المتصلين فقط - السيرفر الثاني."
)
async def massdm(ctx, *, message_content: str):
    if ctx.guild.id != NEW_SERVER_ID:
        return await deny(ctx.message)

    if ctx.author.id not in ADMIN_IDS:
        return await ctx.send("❌ للإدارة فقط!", delete_after=8)

    try:
        await ctx.message.delete()
    except Exception:
        pass

    guild = ctx.guild
    active_members = [
        m for m in guild.members
        if not m.bot and m.status != discord.Status.offline
    ]

    if not active_members:
        return await ctx.send(
            "⚠️ حالياً لا يوجد أي عضو متصل!",
            delete_after=10
        )

    total = len(active_members)
    status_msg = await ctx.send(
        f"⏳ جاري بدء الإرسال للأعضاء المتصلين... (0/{total})"
    )

    success_count = 0
    fail_count = 0

    for i, member in enumerate(active_members, 1):
        try:
            embed = discord.Embed(
                title=f"📢 إعلان جديد من سيرفر: {guild.name}",
                description=message_content,
                color=discord.Color.gold()
            )
            embed.set_footer(text="تم الإرسال بواسطة الإدارة")
            await member.send(embed=embed)
            success_count += 1
        except Exception:
            fail_count += 1

        if i % 2 == 0 or i == total:
            percent = int((i / total) * 100)
            filled_blocks = int(percent / 10)
            bar = "🟩" * filled_blocks + "⬛" * (10 - filled_blocks)
            try:
                await status_msg.edit(
                    content=(
                        f"🚀 **جاري الإرسال...**\n"
                        f"[{bar}] `{percent}%`\n"
                        f"📊 المنجز: `{i}` من `{total}`\n"
                        f"✅ نجاح: `{success_count}` | ❌ فشل: `{fail_count}`"
                    )
                )
            except Exception:
                pass

        if i < total:
            await asyncio.sleep(random.uniform(6.0, 12.0))

    final_embed = discord.Embed(
        title="📊 تقرير البرودكاست",
        description=(
            f"✅ **نجاح:** `{success_count}`\n"
            f"❌ **فشل:** `{fail_count}`\n"
            f"👥 **المجموع المستهدف:** `{total}`"
        ),
        color=discord.Color.green() if success_count > 0 else discord.Color.red()
    )
    await status_msg.edit(content=None, embed=final_embed)


# ============================================================
# GAMES
# ============================================================

@bot.command(name="games", aliases=["play"], help="قائمة الألعاب.")
async def games_list(ctx):
    embed = discord.Embed(
        title="🎮 قائمة ألعاب المتجر",
        description=(
            "🔹 `$xo @العضو` - تحدي X-O\n"
            "🔹 `$roulette` - روليت السيرفر\n"
            "🔹 `$rps [حجرة/ورقة/مقص]` - حجرة ورقة مقص"
        ),
        color=discord.Color.blurple()
    )
    await ctx.send(embed=embed)


class TicTacToeButton(discord.ui.Button):
    def __init__(self, x, y):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="\u200e",
            row=x
        )
        self.x = x
        self.y = y

    async def callback(self, interaction):
        view = self.view
        if interaction.user != view.current_player:
            return await interaction.response.send_message(
                "❌ ليس دورك الآن!", ephemeral=True
            )
        if view.board[self.x][self.y] != 0:
            return await interaction.response.send_message(
                "❌ الخانة ممتلئة!", ephemeral=True
            )

        if view.current_player == view.playerX:
            self.style = discord.ButtonStyle.danger
            self.label = "X"
            view.board[self.x][self.y] = 1
            view.current_player = view.playerO
        else:
            self.style = discord.ButtonStyle.success
            self.label = "O"
            view.board[self.x][self.y] = -1
            view.current_player = view.playerX

        self.disabled = True
        winner = view.check_winner()

        if winner is not None:
            if winner == 1:
                description = f"🎉 الفائز {view.playerX.mention}!"
            elif winner == -1:
                description = f"🎉 الفائز {view.playerO.mention}!"
            else:
                description = "🤝 تعادل!"

            embed = discord.Embed(
                title="🎮 X-O",
                description=description,
                color=discord.Color.green()
            )
            for child in view.children:
                child.disabled = True
            await interaction.response.edit_message(embed=embed, view=view)
            view.stop()
            return

        embed = discord.Embed(
            title="🎮 X-O",
            description=f"دور: {view.current_player.mention}",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=view)


class TicTacToeView(discord.ui.View):
    def __init__(self, playerX, playerO):
        super().__init__()
        self.playerX = playerX
        self.playerO = playerO
        self.current_player = playerX
        self.board = [[0, 0, 0] for _ in range(3)]
        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y))

    def check_winner(self):
        for row in self.board:
            if row[0] == row[1] == row[2] != 0:
                return row[0]
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] != 0:
                return self.board[0][col]
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != 0:
            return self.board[0][0]
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != 0:
            return self.board[0][2]
        if all(self.board[r][c] != 0 for r in range(3) for c in range(3)):
            return 0
        return None


@bot.command(name="xo", help="تحدي X-O.")
async def xo(ctx, member: discord.Member):
    if member == ctx.author or member.bot:
        return await ctx.send("❌ لا يمكنك اللعب لوحدك!")
    view = TicTacToeView(ctx.author, member)
    embed = discord.Embed(
        title="🎮 X-O",
        description=f"تحدٍ بين {ctx.author.mention} و {member.mention}",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=view)


@bot.command(name="roulette", help="روليت السيرفر.")
async def roulette(ctx):
    class RouletteJoinView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            self.players = set()

        @discord.ui.button(label="🟢 انضمام", style=discord.ButtonStyle.green)
        async def join(self, interaction, button):
            self.players.add(interaction.user.id)
            await interaction.response.send_message(
                "✅ تم انضمامك!",
                ephemeral=True
            )

    embed = discord.Embed(
        title="🎲 روليت",
        description="⏳ 60 ثانية للانضمام عبر الزر أدناه!",
        color=discord.Color.gold()
    )
    view = RouletteJoinView()
    msg = await ctx.send(embed=embed, view=view)
    await asyncio.sleep(60)

    for child in view.children:
        child.disabled = True

    if not view.players:
        return await msg.edit(
            content="❌ انتهى الوقت ولم يشارك أحد!",
            embed=None,
            view=view
        )

    winner_id = random.choice(list(view.players))
    await msg.edit(
        content=f"🎉 الفائز هو: <@{winner_id}>!",
        view=view
    )


@bot.command(name="rps", help="حجرة ورقة مقص.")
async def rps(ctx, choice: str):
    choices = ["حجرة", "ورقة", "مقص"]
    choice = choice.lower().strip()
    if choice not in choices:
        return await ctx.send("❌ اختر: حجرة، ورقة، مقص")

    bot_choice = random.choice(choices)

    if choice == bot_choice:
        result = "🤝 تعادل!"
    elif (
        (choice == "حجرة" and bot_choice == "مقص")
        or (choice == "ورقة" and bot_choice == "حجرة")
        or (choice == "مقص" and bot_choice == "ورقة")
    ):
        result = "🎉 فزت!"
    else:
        result = "🤖 خسرت!"

    await ctx.send(
        embed=discord.Embed(
            title="✂️ حجرة ورقة مقص",
            description=(
                f"اختيارك: {choice}\n"
                f"اختيار البوت: {bot_choice}\n\n"
                f"**{result}**"
            ),
            color=discord.Color.purple()
        )
    )


# ============================================================
# SUGGEST / REMIND
# ============================================================

@bot.command(name="suggest", help="إرسال اقتراح.")
async def suggest(ctx, *, suggestion: str):
    try:
        await ctx.message.delete()
    except Exception:
        pass

    ch = bot.get_channel(FEEDBACK_CHANNEL_ID)
    embed = discord.Embed(
        title="💡 اقتراح جديد",
        description=suggestion,
        color=discord.Color.blue()
    )

    if ch:
        msg = await ch.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
        await send_divider(ch)

    await ctx.send("✅ تم إرسال اقتراحك!", delete_after=10)


@bot.command(name="remind", help="تذكير شخصي.")
async def remind(ctx, time_str: str, *, reminder: str):
    seconds = parse_time(time_str)
    if not seconds:
        return await ctx.send("❌ صيغة الوقت خاطئة.")

    await ctx.send(f"✅ تذكير بعد `{time_str}`.")
    await asyncio.sleep(seconds)

    try:
        await ctx.author.send(f"⏰ تذكير: {reminder}")
    except Exception:
        pass


# ============================================================
# ERROR HANDLING
# ============================================================

@bot.event
async def on_disconnect():
    save_data()


@bot.event
async def on_close():
    save_data()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    load_data()
    token = os.environ.get("DISCORD_TOKEN")

    if not token:
        raise RuntimeError(
            "DISCORD_TOKEN is missing. Set your bot token as an environment variable."
        )

    try:
        bot.run(token)
    except Exception:
        print("\n[!] خطأ في التشغيل:")
        traceback.print_exc()
