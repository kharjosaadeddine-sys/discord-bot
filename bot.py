# ============================================================
# 7R COMMUNITY - FULL DISCORD BOT
# ============================================================
# pip install -U discord.py
#
# SERVER RULES
# ------------------------------------------------------------
# OLD SERVER  : 1300210023275827291
# NEW SERVER  : 1404871303340621996
#
# OLD commands -> ONLY OLD SERVER
# NEW mediator/support commands -> ONLY NEW SERVER
# $tax + $massdm -> ONLY NEW SERVER
#
# Admins with full NEW-SERVER control:
# 1021501331636244490
# 1133434766738329640
#
# Put your token in:
# DISCORD_TOKEN
#
# Enable in Developer Portal:
# - Message Content Intent
# - Server Members Intent
# - Presence Intent
# ============================================================

import discord
from discord.ext import commands
import asyncio
import json
import os
import random
import traceback
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================

OLD_GUILD_ID = 1300210023275827291
NEW_GUILD_ID = 1404871303340621996

OWNER_ID = 1021501331636244490
ADMIN_IDS = {
    1021501331636244490,
    1133434766738329640
}

# NEW SERVER
SUPPORT_CATEGORY_ID = 1540776948954038452
MEDIATOR_CATEGORY_ID = 1540776952787632220

SUPPORT_ROLE_ID = 1543149771299094650
MEDIATOR_ROLE_ID = 1543142907958001768

MEDIATOR_CLIENT_ROLE_ID = 1543276152951414885
VIP_CLIENT_ROLE_ID = 1543276454895161455

TRANSCRIPT_CHANNEL_ID = 1543277110951678155
RATING_CHANNEL_ID = 1540776982265073765

EXCHANGE_RATE = 10
DATA_FILE = "7r_data.json"

# ============================================================
# BOT
# ============================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.guilds = True

bot = commands.Bot(
    command_prefix="$",
    intents=intents,
    help_command=None
)

# ============================================================
# DATABASE
# ============================================================

def default_database():
    return {
        "store_credits": {},
        "mediator_points": {},
        "mediator_tickets": {},
        "ratings": {},
        "ticket_counter": 0,
        "tickets": {}
    }


def load_database():
    if not os.path.exists(DATA_FILE):
        return default_database()

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)

        db = default_database()
        db.update(saved)
        return db

    except Exception:
        return default_database()


DB = load_database()


def save_database():
    temp = DATA_FILE + ".tmp"

    with open(temp, "w", encoding="utf-8") as f:
        json.dump(DB, f, ensure_ascii=False, indent=2)

    os.replace(temp, DATA_FILE)


# ============================================================
# DATABASE HELPERS
# ============================================================

def get_credit(user_id):
    return int(DB["store_credits"].get(str(user_id), 0))


def update_credit(user_id, amount):
    key = str(user_id)
    DB["store_credits"][key] = get_credit(user_id) + int(amount)
    save_database()


def get_points(user_id):
    return int(DB["mediator_points"].get(str(user_id), 0))


def set_points(user_id, amount):
    DB["mediator_points"][str(user_id)] = max(0, int(amount))
    save_database()


def add_mediator_point(user_id):
    set_points(user_id, get_points(user_id) + 1)


def get_mediator_ticket_count(user_id):
    return int(DB["mediator_tickets"].get(str(user_id), 0))


def add_mediator_ticket(user_id):
    key = str(user_id)
    DB["mediator_tickets"][key] = get_mediator_ticket_count(user_id) + 1
    save_database()


def get_ratings(user_id):
    return DB["ratings"].get(str(user_id), [])


def add_rating(user_id, stars):
    key = str(user_id)

    if key not in DB["ratings"]:
        DB["ratings"][key] = []

    DB["ratings"][key].append(int(stars))
    save_database()


def get_average_rating(user_id):
    ratings = get_ratings(user_id)

    if not ratings:
        return 0.0

    return round(sum(ratings) / len(ratings), 2)


def next_ticket_number():
    DB["ticket_counter"] = int(DB.get("ticket_counter", 0)) + 1
    save_database()
    return DB["ticket_counter"]


# ============================================================
# PARSERS
# ============================================================

def parse_amount(value):
    value = value.lower().replace(",", "").strip()

    try:
        if value.endswith("k"):
            return int(float(value[:-1]) * 1000)

        if value.endswith("m"):
            return int(float(value[:-1]) * 1_000_000)

        return int(float(value))

    except ValueError:
        return None


def parse_time(value):
    value = value.lower().strip()

    try:
        if value.endswith("s"):
            return int(value[:-1])

        if value.endswith("m"):
            return int(value[:-1]) * 60

        if value.endswith("h"):
            return int(value[:-1]) * 3600

        return int(value) * 60

    except ValueError:
        return None


# ============================================================
# SERVER / PERMISSION CHECKS
# ============================================================

def old_only():
    async def predicate(ctx):
        return (
            ctx.guild is not None
            and ctx.guild.id == OLD_GUILD_ID
        )

    return commands.check(predicate)


def new_only():
    async def predicate(ctx):
        return (
            ctx.guild is not None
            and ctx.guild.id == NEW_GUILD_ID
        )

    return commands.check(predicate)


def new_admin_only():
    async def predicate(ctx):
        return (
            ctx.guild is not None
            and ctx.guild.id == NEW_GUILD_ID
            and ctx.author.id in ADMIN_IDS
        )

    return commands.check(predicate)


def is_admin(member):
    return member.id in ADMIN_IDS


def is_mediator(member):
    if member.id in ADMIN_IDS:
        return True

    return any(
        role.id == MEDIATOR_ROLE_ID
        for role in member.roles
    )


def get_ticket(channel_id):
    return DB["tickets"].get(str(channel_id))


# ============================================================
# GENERAL HELPERS
# ============================================================

async def safe_delete(message):
    try:
        await message.delete()
    except Exception:
        pass


async def add_role(member, role_id):
    role = member.guild.get_role(role_id)

    if role:
        try:
            await member.add_roles(role)
        except Exception:
            pass


async def remove_role(member, role_id):
    role = member.guild.get_role(role_id)

    if role:
        try:
            await member.remove_roles(role)
        except Exception:
            pass


async def send_new_log(guild, embed=None, content=None):
    channel = guild.get_channel(TRANSCRIPT_CHANNEL_ID)

    if not channel:
        return

    try:
        await channel.send(
            content=content,
            embed=embed
        )
    except Exception:
        pass


# ============================================================
# OLD BOT - ORIGINAL FEATURES
# ============================================================

SENSITIVE_WORDS = {
    "متوفر": "مـتـوفــر",
    "متوفره": "مـتـوفــرة",
    "متوفرة": "مـتـوفــرة",
    "توفر": "تـو_فُـر",
    "حسابات": "حـس_ابـات",
    "حساب": "حـس_اب",
    "ايميل": "ايـم___يل",
    "إيميل": "إيـم___يل",
    "ايميلات": "ايـم_يــلات",
    "إيميلات": "إيـم_يــلات",
    "جيميل": "جـيـمــيل",
    "gmail": "g_m_a_i_l",
    "نيترو": "نـيـتـــرو",
    "نايترو": "نـايـتـــرو",
    "nitro": "n_i_t_r_o",
    "بوت": "بـو_ت",
    "توكن": "تـوكــن",
    "token": "t_o_k_e_n",
    "بيع": "بـيـــع",
    "شراء": "شــــراء",
    "سعر": "سـعـــر",
    "اسعار": "أسـعـــار",
    "أسعار": "أسـعـــار",
    "ثمن": "ثـمــــن",
    "رخيص": "ر_خـيـص",
    "متجر": "مـت-جـــر",
    "عروضكم": "عـرو_ضـكم",
    "عروض": "عـرُو_ض",
    "عرض": "عَـرْ_ض",
    "طلب": "طـلـــب",
    "طلبات": "طـلــبات",
    "تسليم": "ت-س-ل-يــم",
    "ضمان": "ضـمـــان",
    "وسيط": "وسـيـــط",
    "كريديت": "كـرِيـدِيـت",
    "كريديتات": "كـرِي-ديــتات",
    "كرديت": "كـرديــت",
    "كردت": "كـر_دت",
    "بروبوت": "بـروبـوت",
    "probot": "p_r_o_b_o_t",
    "بايبال": "بـايـبــال",
    "paypal": "p_a_y_p_a_l",
    "رصيد": "ر_صـيـد",
    "فلوس": "فـلــوس",
    "مبلغ": "مـبـلـــغ",
    "تحويل": "ت-ح-ويــل",
    "كاش": "كــاش",
    "درهم": "در_هـم",
    "دولار": "دو_لار",
    "خاص": "خ_اص",
    "الخاص": "الـخ_اص",
    "خاصك": "خـاصـك",
    "دي ام": "دي_ام",
    "dm": "d_m",
    "خاصي": "خ_اصي",
    "تواصل": "ت-واصــل",
    "واتساب": "واتسـاب",
    "تيليجرام": "تيليـجرام",
    "telegram": "t_e_l_e_ج_a_m"
}

FEEDBACK_CHANNEL_ID = 1541011452037439489
WELCOME_CHANNEL_ID = 1538994818150170714
LOGS_CHANNEL_ID = 1538994821455282197

DIVIDER_IMAGE_URL = (
    "https://cdn.discordapp.com/attachments/"
    "1336759214378582066/"
    "1539262263893037086/"
    "Gemini_Generated_Image_97gvdg97gvdg97gv.jfif"
    "?ex=6a8af331&is=6a89a1b1"
    "&hm=d057e94d76fb45c269c7262846cd27c363f1b88d8868586b0aa01121d28e2933"
)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print("7R COMMUNITY BOT is online.")


@bot.event
async def on_member_join(member):
    # Welcome system belongs to the OLD server.
    if member.guild.id != OLD_GUILD_ID:
        return

    try:
        class WelcomeView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)

                self.add_item(
                    discord.ui.Button(
                        label="اضغط هنا للانتقال إلى القناة المخصصة",
                        style=discord.ButtonStyle.link,
                        url=(
                            f"https://discord.com/channels/"
                            f"{member.guild.id}/{WELCOME_CHANNEL_ID}"
                        )
                    )
                )

        embed = discord.Embed(
            title="✨ مرحباً بك في سيرفرنا!",
            description=(
                f"مرحباً بك يا {member.mention} في سيرفر "
                f"**{member.guild.name}**!\n\n"
                "نحن سعداء بانضمامك إلينا 🚀.\n"
                "للبدء، ندعوك لزيارة هذه الروم المهمة."
            ),
            color=discord.Color.gold()
        )

        embed.set_footer(text="Made with ❤️ by kaizencredits")

        await member.send(
            embed=embed,
            view=WelcomeView()
        )

    except Exception as error:
        print(f"Welcome DM error: {error}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Old server sensitive-word system ONLY.
    if (
        message.guild
        and message.guild.id == OLD_GUILD_ID
        and not message.content.startswith("$")
    ):
        lower = message.content.lower()

        if any(
            word in lower
            for word in [
                "كيف اصنع",
                "كيف أنشئ",
                "كيف اسوي",
                "صنع ايميل",
                "طريقة صنع",
                "كيفاش نسوي"
            ]
        ):
            await message.reply(
                f"أهلاً بك يا بطل! 🌟\n"
                f"زُر الروم المخصص هنا: <#{WELCOME_CHANNEL_ID}>"
            )
            return

        content = message.content
        changed = False

        for word, replacement in SENSITIVE_WORDS.items():
            if word in content.lower():
                content = content.replace(word, replacement)
                changed = True

        if changed:
            await safe_delete(message)

            try:
                await message.author.send(
                    embed=discord.Embed(
                        title="⚠️ تنبيه أمني: تم حذف رسالتك",
                        description=(
                            "تم حذف رسالتك لتفادي البلاغات.\n"
                            "النص بعد التعديل:"
                        ),
                        color=discord.Color.orange()
                    )
                )

                await message.author.send(
                    f"```{content}```"
                )

            except Exception:
                pass

            return

    # DM relay from the old bot.
    if isinstance(message.channel, discord.DMChannel):
        if not message.content.startswith("$"):
            for admin_id in ADMIN_IDS:
                try:
                    admin = await bot.fetch_user(admin_id)

                    if admin:
                        embed = discord.Embed(
                            title="📩 رسالة جديدة في خاص البوت",
                            description=(
                                f"👤 **من:** {message.author} "
                                f"(`{message.author.id}`)\n\n"
                                f"💬 **النص:**\n{message.content}"
                            ),
                            color=discord.Color.blurple()
                        )

                        await admin.send(embed=embed)

                except Exception:
                    pass

    await bot.process_commands(message)


# ============================================================
# OLD SERVER: TICKET SYSTEM
# ============================================================

class OldTicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="استفسار عام",
                description="لأي سؤال أو استفسار بخصوص السيرفر",
                emoji="❓",
                value="inquiry"
            ),
            discord.SelectOption(
                label="إعلانات وشراكات",
                description="لطلب الإعلانات أو الشراكات",
                emoji="📢",
                value="ads"
            ),
            discord.SelectOption(
                label="مشكلة ودعم فني",
                description="إذا واجهتك مشكلة وتحتاج مساعدة",
                emoji="🛠️",
                value="support"
            )
        ]

        super().__init__(
            placeholder="اختر نوع التذكرة...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="old_ticket_select"
        )

    async def callback(self, interaction):
        guild = interaction.guild

        category_id = 1538994814404792480
        category = guild.get_channel(category_id)

        names = {
            "inquiry": "استفسار",
            "ads": "إعلانات",
            "support": "دعم-فني"
        }

        ticket_type = names.get(
            self.values[0],
            "تذكرة"
        )

        overwrites = {
            guild.default_role:
                discord.PermissionOverwrite(view_channel=False),

            interaction.user:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True
                )
        }

        try:
            channel = await guild.create_text_channel(
                name=f"{ticket_type}-{interaction.user.name}",
                overwrites=overwrites,
                category=category
                if isinstance(category, discord.CategoryChannel)
                else None
            )

            embed = discord.Embed(
                title=f"🎫 تذكرة جديدة: {ticket_type}",
                description=(
                    f"مرحباً {interaction.user.mention}!\n"
                    "تم فتح التذكرة بنجاح.\n"
                    "يرجى شرح طلبك بالتفصيل."
                ),
                color=discord.Color.blue()
            )

            await channel.send(
                embed=embed,
                view=OldCloseTicketView()
            )

            await interaction.response.send_message(
                f"✅ تم إنشاء التذكرة: {channel.mention}",
                ephemeral=True
            )

        except Exception as error:
            await interaction.response.send_message(
                f"❌ حدث خطأ: {error}",
                ephemeral=True
            )


class OldTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(OldTicketSelect())


class OldCloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="إغلاق التذكرة 🔒",
        style=discord.ButtonStyle.danger,
        custom_id="old_close_ticket"
    )
    async def close(
        self,
        interaction,
        button
    ):
        await interaction.response.send_message(
            "⚠️ سيتم حذف التذكرة خلال ثانيتين..."
        )

        await asyncio.sleep(2)

        try:
            await interaction.channel.delete()
        except Exception:
            pass


@bot.command(
    name="setup_tickets",
    help="إرسال لوحة التذاكر القديمة."
)
@old_only()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    await safe_delete(ctx.message)

    embed = discord.Embed(
        title="🎫 نظام التذاكر والدعم الفني",
        description=(
            "إذا كنت بحاجة إلى مساعدة أو استفسار، "
            "اختر القسم المناسب من القائمة."
        ),
        color=discord.Color.gold()
    )

    embed.set_footer(
        text="يرجى عدم فتح تذكرة بدون سبب."
    )

    await ctx.send(
        embed=embed,
        view=OldTicketView()
    )


# ============================================================
# OLD SERVER: POINTS
# ============================================================

@bot.command(
    name="points",
    aliases=["pts", "credit", "balance"],
    help="عرض رصيد نقاط المتجر."
)
@old_only()
async def points(ctx, member: discord.Member = None):
    target = member or ctx.author
    balance = get_credit(target.id)
    probot = balance / EXCHANGE_RATE

    embed = discord.Embed(
        title="💎 رصيد نقاط المتجر",
        description=(
            f"العضو: {target.mention}\n"
            f"🔹 الرصيد: **{balance:,} نقطة**\n"
            f"🔸 يعادل بالبروبوت: **{probot:,.1f}**"
        ),
        color=discord.Color.gold()
    )

    await ctx.send(embed=embed)


@bot.command(
    name="transfer",
    aliases=["pay", "give"],
    help="تحويل نقاط لعضو."
)
@old_only()
async def transfer(ctx, member: discord.Member, amount_str: str):
    amount = parse_amount(amount_str)

    if amount is None or amount <= 0:
        return await ctx.send(
            "❌ يرجى تحديد مبلغ صحيح.",
            delete_after=10
        )

    if member.id == ctx.author.id:
        return await ctx.send(
            "❌ لا يمكنك التحويل لنفسك.",
            delete_after=10
        )

    if member.bot:
        return await ctx.send(
            "❌ لا يمكنك التحويل لبوت.",
            delete_after=10
        )

    balance = get_credit(ctx.author.id)

    if balance < amount:
        return await ctx.send(
            f"❌ رصيدك غير كافٍ. رصيدك: `{balance:,}`",
            delete_after=10
        )

    update_credit(ctx.author.id, -amount)
    update_credit(member.id, amount)

    await safe_delete(ctx.message)

    embed = discord.Embed(
        title="💸 عملية تحويل ناجحة",
        description=(
            f"👤 **المحول:** {ctx.author.mention}\n"
            f"🎯 **المستلم:** {member.mention}\n"
            f"💎 **المبلغ:** `{amount:,}` نقطة\n"
            f"📉 **رصيدك:** `{get_credit(ctx.author.id):,}` نقطة"
        ),
        color=discord.Color.green()
    )

    await ctx.send(embed=embed)


@bot.command(
    name="addpoints",
    help="إضافة نقاط للعضو."
)
@old_only()
async def addpoints(ctx, member: discord.Member, amount: int):
    if ctx.author.id != OWNER_ID:
        return await ctx.send(
            "❌ هذا الأمر للمالك فقط.",
            delete_after=10
        )

    update_credit(member.id, amount)

    await ctx.send(
        f"✅ تمت إضافة `{amount:,}` نقطة لـ {member.mention}"
    )


@bot.command(
    name="removepoints",
    help="خصم نقاط من العضو."
)
@old_only()
async def removepoints(ctx, member: discord.Member, amount: int):
    if ctx.author.id != OWNER_ID:
        return await ctx.send(
            "❌ هذا الأمر للمالك فقط.",
            delete_after=10
        )

    update_credit(member.id, -amount)

    await ctx.send(
        f"✅ تم خصم `{amount:,}` نقطة من {member.mention}"
    )


@bot.command(
    name="withdraw",
    help="طلب سحب النقاط."
)
@old_only()
async def withdraw(ctx, amount_str: str):
    amount = parse_amount(amount_str)

    if amount is None or amount <= 0:
        return await ctx.send(
            "❌ المبلغ غير صحيح.",
            delete_after=10
        )

    balance = get_credit(ctx.author.id)

    if balance < amount:
        return await ctx.send(
            f"❌ رصيدك غير كافٍ: `{balance:,}`",
            delete_after=10
        )

    update_credit(ctx.author.id, -amount)

    credit = amount / EXCHANGE_RATE

    await safe_delete(ctx.message)

    for admin_id in ADMIN_IDS:
        try:
            admin = await bot.fetch_user(admin_id)

            await admin.send(
                embed=discord.Embed(
                    title="📥 طلب سحب كريديت",
                    description=(
                        f"👤 **العضو:** {ctx.author.mention}\n"
                        f"📉 **النقاط:** `{amount:,}`\n"
                        f"💲 **الكريديت:** `{credit:,.1f}`\n\n"
                        f"```c {ctx.author.id} {int(credit)}```"
                    ),
                    color=discord.Color.green()
                )
            )

        except Exception:
            pass

    await ctx.send(
        "✅ تم تقديم طلب السحب.",
        delete_after=10
    )


# ============================================================
# OLD SERVER: TAX / PROFIT
# NOTE: $tax is intentionally NOT here.
# It is implemented ONLY in NEW SERVER below.
# ============================================================

@bot.command(
    name="profit",
    help="حساب صافي الربح."
)
@old_only()
async def profit(ctx, price: int, cost: int):
    result = price - cost

    await ctx.send(
        embed=discord.Embed(
            title="📈 حساب الأرباح",
            description=f"💰 صافي الربح: `{result:,}`",
            color=discord.Color.green()
        )
    )


# ============================================================
# OLD SERVER: GAMES
# ============================================================

class TicTacToeButton(discord.ui.Button):
    def __init__(self, x, y):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="\u200b",
            row=x
        )

        self.x = x
        self.y = y

    async def callback(self, interaction):
        view = self.view

        if interaction.user != view.current_player:
            return await interaction.response.send_message(
                "❌ ليس دورك.",
                ephemeral=True
            )

        if view.board[self.x][self.y] != 0:
            return await interaction.response.send_message(
                "❌ الخانة ممتلئة.",
                ephemeral=True
            )

        if interaction.user == view.player_x:
            self.label = "X"
            self.style = discord.ButtonStyle.danger
            view.board[self.x][self.y] = 1
            view.current_player = view.player_o

        else:
            self.label = "O"
            self.style = discord.ButtonStyle.success
            view.board[self.x][self.y] = -1
            view.current_player = view.player_x

        self.disabled = True

        winner = view.check_winner()

        if winner is not None:
            if winner == 1:
                text = f"🎉 الفائز: {view.player_x.mention}"

            elif winner == -1:
                text = f"🎉 الفائز: {view.player_o.mention}"

            else:
                text = "🤝 تعادل!"

            for child in view.children:
                child.disabled = True

            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="🎮 X-O",
                    description=text,
                    color=discord.Color.green()
                ),
                view=view
            )

            view.stop()
            return

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="🎮 X-O",
                description=(
                    f"دور: {view.current_player.mention}"
                ),
                color=discord.Color.blue()
            ),
            view=view
        )


class TicTacToeView(discord.ui.View):
    def __init__(self, player_x, player_o):
        super().__init__(timeout=300)

        self.player_x = player_x
        self.player_o = player_o
        self.current_player = player_x
        self.board = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0]
        ]

        for x in range(3):
            for y in range(3):
                self.add_item(
                    TicTacToeButton(x, y)
                )

    def check_winner(self):
        for row in self.board:
            if row[0] == row[1] == row[2] != 0:
                return row[0]

        for col in range(3):
            if (
                self.board[0][col]
                == self.board[1][col]
                == self.board[2][col]
                != 0
            ):
                return self.board[0][col]

        if (
            self.board[0][0]
            == self.board[1][1]
            == self.board[2][2]
            != 0
        ):
            return self.board[0][0]

        if (
            self.board[0][2]
            == self.board[1][1]
            == self.board[2][0]
            != 0
        ):
            return self.board[0][2]

        if all(
            self.board[r][c] != 0
            for r in range(3)
            for c in range(3)
        ):
            return 0

        return None


@bot.command(
    name="xo",
    help="لعب X-O."
)
@old_only()
async def xo(ctx, member: discord.Member):
    if member == ctx.author or member.bot:
        return await ctx.send(
            "❌ لا يمكنك اللعب مع نفسك أو بوت."
        )

    view = TicTacToeView(
        ctx.author,
        member
    )

    await ctx.send(
        embed=discord.Embed(
            title="🎮 X-O",
            description=(
                f"{ctx.author.mention} ضد "
                f"{member.mention}\n"
                f"الدور: {ctx.author.mention}"
            ),
            color=discord.Color.blue()
        ),
        view=view
    )


@bot.command(
    name="roulette",
    help="روليت السيرفر."
)
@old_only()
async def roulette(ctx):

    class RouletteView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            self.players = set()

        @discord.ui.button(
            label="🟢 انضمام",
            style=discord.ButtonStyle.success
        )
        async def join(self, interaction, button):
            self.players.add(interaction.user)
            await interaction.response.send_message(
                "✅ تم انضمامك!",
                ephemeral=True
            )

    view = RouletteView()

    message = await ctx.send(
        embed=discord.Embed(
            title="🎲 روليت",
            description="⏳ لديك 60 ثانية للانضمام.",
            color=discord.Color.gold()
        ),
        view=view
    )

    await asyncio.sleep(60)

    for child in view.children:
        child.disabled = True

    if not view.players:
        return await message.edit(
            content="❌ لم يشارك أحد.",
            embed=None,
            view=view
        )

    winner = random.choice(list(view.players))

    await message.edit(
        content=f"🎉 الفائز: {winner.mention}",
        view=view
    )


@bot.command(
    name="rps",
    help="حجرة ورقة مقص."
)
@old_only()
async def rps(ctx, choice: str):
    choices = ["حجرة", "ورقة", "مقص"]
    choice = choice.lower().strip()

    if choice not in choices:
        return await ctx.send(
            "❌ اختر: حجرة، ورقة، مقص"
        )

    bot_choice = random.choice(choices)

    if choice == bot_choice:
        result = "🤝 تعادل!"

    elif (
        (choice == "حجرة" and bot_choice == "مقص")
        or
        (choice == "ورقة" and bot_choice == "حجرة")
        or
        (choice == "مقص" and bot_choice == "ورقة")
    ):
        result = "🎉 فزت!"

    else:
        result = "🤖 خسرت!"

    await ctx.send(
        embed=discord.Embed(
            title="✂️ حجرة ورقة مقص",
            description=(
                f"اختيارك: **{choice}**\n"
                f"اختيار البوت: **{bot_choice}**\n\n"
                f"**{result}**"
            ),
            color=discord.Color.purple()
        )
    )


@bot.command(
    name="games",
    aliases=["play"],
    help="قائمة الألعاب."
)
@old_only()
async def games(ctx):
    await ctx.send(
        embed=discord.Embed(
            title="🎮 ألعاب المتجر",
            description=(
                "🔹 `$xo @العضو`\n"
                "🔹 `$roulette`\n"
                "🔹 `$rps حجرة/ورقة/مقص`"
            ),
            color=discord.Color.blurple()
        )
    )


# ============================================================
# OLD SERVER: SUGGEST / REMIND / RATE / INFO
# ============================================================

@bot.command(
    name="suggest",
    help="إرسال اقتراح."
)
@old_only()
async def suggest(ctx, *, suggestion: str):
    await safe_delete(ctx.message)

    channel = bot.get_channel(FEEDBACK_CHANNEL_ID)

    if channel:
        embed = discord.Embed(
            title="💡 اقتراح جديد",
            description=suggestion,
            color=discord.Color.blue()
        )

        message = await channel.send(embed=embed)
        await message.add_reaction("👍")
        await message.add_reaction("👎")

        if DIVIDER_IMAGE_URL:
            await channel.send(DIVIDER_IMAGE_URL)

    await ctx.send(
        "✅ تم إرسال اقتراحك!",
        delete_after=10
    )


@bot.command(
    name="remind",
    help="تذكير شخصي."
)
@old_only()
async def remind(ctx, time_str: str, *, reminder: str):
    seconds = parse_time(time_str)

    if not seconds:
        return await ctx.send(
            "❌ صيغة الوقت خاطئة."
        )

    await ctx.send(
        f"✅ سأذكرك بعد `{time_str}`."
    )

    await asyncio.sleep(seconds)

    try:
        await ctx.author.send(
            f"⏰ تذكير: {reminder}"
        )
    except Exception:
        pass


@bot.command(
    name="serverinfo",
    aliases=["sinfo"],
    help="معلومات السيرفر."
)
@old_only()
async def serverinfo(ctx):
    guild = ctx.guild

    owners = ", ".join(
        f"<@{admin_id}>"
        for admin_id in ADMIN_IDS
    )

    embed = discord.Embed(
        title=f"📊 معلومات: {guild.name}",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="👑 الإدارة",
        value=owners,
        inline=False
    )

    embed.add_field(
        name="👥 الأعضاء",
        value=str(guild.member_count),
        inline=True
    )

    embed.add_field(
        name="📅 الإنشاء",
        value=guild.created_at.strftime("%Y-%m-%d"),
        inline=True
    )

    await ctx.send(embed=embed)


@bot.command(
    name="rate",
    help="إرسال تقييم للزبون."
)
@old_only()
async def old_rate(ctx, member: discord.Member):
    if ctx.author.id not in ADMIN_IDS:
        return await ctx.send(
            "❌ للإدارة فقط."
        )

    class OldRatingView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=300)

        async def process(self, interaction, stars):
            embed = discord.Embed(
                title="⭐ تقييم جديد",
                description=(
                    f"👤 **العميل:** {interaction.user.mention}\n"
                    f"⭐ **التقييم:** {stars}/5"
                ),
                color=discord.Color.gold()
            )

            channel = bot.get_channel(FEEDBACK_CHANNEL_ID)

            if channel:
                await channel.send(embed=embed)

            for child in self.children:
                child.disabled = True

            await interaction.response.edit_message(
                content="❤️ شكراً لتقييمك!",
                view=self
            )

        @discord.ui.button(label="⭐ 1", style=discord.ButtonStyle.danger)
        async def one(self, i, b):
            await self.process(i, 1)

        @discord.ui.button(label="⭐ 2", style=discord.ButtonStyle.secondary)
        async def two(self, i, b):
            await self.process(i, 2)

        @discord.ui.button(label="⭐ 3", style=discord.ButtonStyle.primary)
        async def three(self, i, b):
            await self.process(i, 3)

        @discord.ui.button(label="⭐ 4", style=discord.ButtonStyle.success)
        async def four(self, i, b):
            await self.process(i, 4)

        @discord.ui.button(label="⭐ 5", style=discord.ButtonStyle.success)
        async def five(self, i, b):
            await self.process(i, 5)

    try:
        await member.send(
            embed=discord.Embed(
                title="⭐ تقييم الخدمة",
                description="قيّم تجربتك معنا:",
                color=discord.Color.gold()
            ),
            view=OldRatingView()
        )

        await ctx.send(
            f"✅ تم إرسال التقييم لـ {member.mention}",
            delete_after=10
        )

    except Exception:
        await ctx.send(
            "❌ خاص العضو مغلق.",
            delete_after=10
        )


@bot.command(
    name="f",
    aliases=["finish"],
    help="إضافة 1.5 مليون نقطة."
)
@old_only()
async def finish_old(ctx, member: discord.Member):
    if ctx.author.id != OWNER_ID:
        return await ctx.send(
            "❌ هذا الأمر للمالك فقط.",
            delete_after=10
        )

    reward = 1_500_000

    update_credit(
        member.id,
        reward
    )

    await safe_delete(ctx.message)

    logs = bot.get_channel(LOGS_CHANNEL_ID)

    if logs:
        await logs.send(
            embed=discord.Embed(
                title="🎯 إنجاز صفقة وتسلّيم الهدية",
                description=(
                    f"👤 **الزبون:** {member.mention}\n"
                    f"🛠️ **الإداري:** {ctx.author.mention}\n"
                    f"🎁 **الهدية:** `{reward:,}` نقطة\n"
                    f"💎 **الرصيد:** `{get_credit(member.id):,}`"
                ),
                color=discord.Color.green()
            )
        )

        if DIVIDER_IMAGE_URL:
            await logs.send(DIVIDER_IMAGE_URL)

    await ctx.send(
        f"✅ تمت إضافة `{reward:,}` نقطة لـ {member.mention}",
        delete_after=10
    )


@bot.command(
    name="setstrat",
    aliases=["strat", "helpmenu"],
    help="قائمة أوامر المتجر."
)
@old_only()
async def setstrat(ctx):
    await safe_delete(ctx.message)

    embed = discord.Embed(
        title="✨ دليل أوامر المتجر",
        description=(
            "💎 **نظام النقاط**\n"
            "`$points` / `$balance`\n"
            "`$transfer @member amount`\n"
            "`$withdraw amount`\n\n"
            "🧾 **الحسابات**\n"
            "`$profit price cost`\n\n"
            "🎮 **الألعاب**\n"
            "`$games`"
        ),
        color=discord.Color.gold()
    )

    await ctx.send(embed=embed)


# ============================================================
# OLD SERVER: ADMIN COMMANDS
# ============================================================

@bot.command(
    name="say",
    help="إرسال رسالة باسم البوت."
)
@old_only()
async def say(ctx, *, text: str):
    if ctx.author.id not in ADMIN_IDS:
        return await ctx.send("❌ للإدارة فقط.")

    await safe_delete(ctx.message)
    await ctx.send(text)


@bot.command(
    name="come",
    help="استدعاء عضو في الخاص."
)
@old_only()
async def come_old(ctx, member: discord.Member, *, reason="بدون سبب"):
    if ctx.author.id not in ADMIN_IDS:
        return await ctx.send("❌ للإدارة فقط.")

    await safe_delete(ctx.message)

    embed = discord.Embed(
        title="🚨 استدعاء إداري",
        description=(
            f"مرحباً {member.mention}\n"
            f"تم استدعاؤك من إدارة **{ctx.guild.name}**.\n\n"
            f"📌 السبب: {reason}\n"
            f"📍 الروم: {ctx.channel.mention}"
        ),
        color=discord.Color.red()
    )

    try:
        await member.send(embed=embed)
        await ctx.send(
            f"✅ تم استدعاء {member.mention}",
            delete_after=10
        )

    except Exception:
        await ctx.send(
            "❌ خاص العضو مغلق.",
            delete_after=10
        )


# ============================================================
# OLD SERVER: $list
# ============================================================

OLD_COMMANDS = [
    "$points / $pts / $credit / $balance",
    "$transfer / $pay / $give",
    "$withdraw",
    "$profit",
    "$games / $play",
    "$xo",
    "$roulette",
    "$rps",
    "$suggest",
    "$remind",
    "$rate",
    "$f / $finish",
    "$setstrat / $strat / $helpmenu",
    "$say",
    "$come",
    "$serverinfo / $sinfo",
    "$setup_tickets"
]


@bot.command(
    name="list",
    aliases=["commands", "cmds"],
    help="عرض أوامر السيرفر القديم."
)
@old_only()
async def old_list(ctx):
    if ctx.author.id not in ADMIN_IDS:
        return await ctx.send(
            "❌ للإدارة فقط."
        )

    embed = discord.Embed(
        title="📋 أوامر البوت - السيرفر القديم",
        description="\n".join(
            f"🔹 `{command}`"
            for command in OLD_COMMANDS
        ),
        color=discord.Color.dark_gold()
    )

    try:
        await ctx.author.send(embed=embed)
        await ctx.send(
            "✅ تم إرسال القائمة في الخاص.",
            delete_after=10
        )
    except Exception:
        await ctx.send(
            "❌ افتح الخاص DM.",
            delete_after=10
        )


# ============================================================
# NEW SERVER - MEDIATOR TICKET SYSTEM
# ============================================================

MEDIATOR_NOTICE = """- **االسيرفر و الوسطاء يختلي مسؤولية تماما ولا يتحمل اي تعويض اذا تم سحب الحساب اثناء او بعد التوسط**
**السبب :**
**`#` اللعبة شددت على حماية الحسابات و قد اصبحت الحسابات في خطر لتقفيل الحساب اثناء التوسط او ترجيعه من الطرف الثاني**
__** مثلا **__
**`#` قام الطرف تاني بسحب الحساب عن طريق دعم اللعبة ف الوسيط  و السيرفر ليس لهم دخل في  امر الحساب الذي تم استرجاعه **
**__هل انتم موافقون؟__**"""


class MediatorClaimView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="استلام التكت",
        emoji="📥",
        style=discord.ButtonStyle.success,
        custom_id="7r_mediator_claim"
    )
    async def claim(self, interaction, button):
        if interaction.guild_id != NEW_GUILD_ID:
            return await interaction.response.send_message(
                "❌ هذا الزر للسيرفر الجديد فقط.",
                ephemeral=True
            )

        if not is_mediator(interaction.user):
            return await interaction.response.send_message(
                "❌ هذا الزر للوسطاء فقط.",
                ephemeral=True
            )

        record = get_ticket(interaction.channel.id)

        if not record or record.get("type") != "mediator":
            return await interaction.response.send_message(
                "❌ هذه ليست تذكرة وساطة.",
                ephemeral=True
            )

        if record.get("claimed_by"):
            return await interaction.response.send_message(
                f"❌ التكت مستلم من <@{record['claimed_by']}>.",
                ephemeral=True
            )

        record["claimed_by"] = interaction.user.id
        DB["tickets"][str(interaction.channel.id)] = record
        save_database()

        button.disabled = True
        button.label = "تم الاستلام"
        button.emoji = "✅"

        await interaction.response.edit_message(
            view=self
        )

        await interaction.channel.send(
            f"🛡️ تم استلام التكت بواسطة {interaction.user.mention}\n\n"
            "**- سلعه الطرف الاول : **\n"
            "**- سلعه الطرف الثاني : **\n"
            "**- يوزر الطرف الثاني :**\n\n"
            f"👤 الطرف الذي فتح التكت: <@{record['opened_by']}>"
        )


class SupportCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="إغلاق التكت 🔒",
        style=discord.ButtonStyle.danger,
        custom_id="7r_support_close"
    )
    async def close(self, interaction, button):
        if not is_admin(interaction.user):
            return await interaction.response.send_message(
                "❌ الإدارة فقط.",
                ephemeral=True
            )

        await interaction.response.send_message(
            "⚠️ سيتم حذف التكت بعد ثانيتين."
        )

        await asyncio.sleep(2)
        await delete_new_ticket(
            interaction.channel,
            actor=interaction.user
        )


class MediatorPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="فتح تكت وسيط",
        emoji="🤝",
        style=discord.ButtonStyle.success,
        custom_id="7r_open_mediator"
    )
    async def mediator(self, interaction, button):
        await open_new_ticket(
            interaction,
            "mediator"
        )


class SupportPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="فتح تكت دعم فني",
        emoji="🛠️",
        style=discord.ButtonStyle.primary,
        custom_id="7r_open_support"
    )
    async def support(self, interaction, button):
        await open_new_ticket(
            interaction,
            "support"
        )


async def open_new_ticket(interaction, ticket_type):
    guild = interaction.guild
    member = interaction.user

    if guild.id != NEW_GUILD_ID:
        return await interaction.response.send_message(
            "❌ هذا النظام للسيرفر الجديد فقط.",
            ephemeral=True
        )

    existing = None

    for channel in guild.text_channels:
        record = get_ticket(channel.id)

        if (
            record
            and record.get("opened_by") == member.id
            and record.get("type") == ticket_type
        ):
            existing = channel
            break

    if existing:
        return await interaction.response.send_message(
            f"❌ عندك تكت مفتوح بالفعل: {existing.mention}",
            ephemeral=True
        )

    if ticket_type == "mediator":
        category = guild.get_channel(
            MEDIATOR_CATEGORY_ID
        )
        role_id = MEDIATOR_ROLE_ID
        title = "🤝 تكت وساطة"
    else:
        category = guild.get_channel(
            SUPPORT_CATEGORY_ID
        )
        role_id = SUPPORT_ROLE_ID
        title = "🛠️ تكت دعم فني"

    ticket_number = next_ticket_number()

    overwrites = {
        guild.default_role:
            discord.PermissionOverwrite(view_channel=False),

        member:
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )
    }

    role = guild.get_role(role_id)

    if role:
        overwrites[role] = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True
        )

    try:
        channel = await guild.create_text_channel(
            name=(
                f"ticket-{ticket_number}-"
                f"{member.name}"
            )[:100],
            category=(
                category
                if isinstance(category, discord.CategoryChannel)
                else None
            ),
            overwrites=overwrites,
            topic=f"7R Ticket #{ticket_number}"
        )

    except Exception as error:
        return await interaction.response.send_message(
            f"❌ لم أستطع إنشاء التكت: `{error}`",
            ephemeral=True
        )

    DB["tickets"][str(channel.id)] = {
        "ticket_number": ticket_number,
        "type": ticket_type,
        "opened_by": member.id,
        "claimed_by": None,
        "party_one": member.id,
        "party_two": None,
        "item_one": "",
        "item_two": "",
        "created_at": datetime.utcnow().isoformat(),
        "ended": False
    }

    save_database()

    if ticket_type == "mediator":
        await add_role(
            member,
            MEDIATOR_CLIENT_ROLE_ID
        )

        embed = discord.Embed(
            title=title,
            description=(
                f"مرحباً {member.mention}\n\n"
                f"رقم التكت: `#{ticket_number}`\n\n"
                f"<@&{MEDIATOR_ROLE_ID}> "
                "يوجد تكت وساطة جديد.\n\n"
                "اضغط **استلام التكت** عندما تكون جاهزاً."
            ),
            color=discord.Color.gold()
        )

        await channel.send(
            content=(
                f"{member.mention} "
                f"<@&{MEDIATOR_ROLE_ID}>"
            ),
            embed=embed,
            view=MediatorClaimView()
        )

    else:
        embed = discord.Embed(
            title=title,
            description=(
                f"مرحباً {member.mention}\n"
                f"رقم التكت: `#{ticket_number}`\n\n"
                "اكتب مشكلتك بالتفصيل، وسيقوم فريق الدعم بمساعدتك."
            ),
            color=discord.Color.blue()
        )

        await channel.send(
            content=f"{member.mention} <@&{SUPPORT_ROLE_ID}>",
            embed=embed,
            view=SupportCloseView()
        )

    await interaction.response.send_message(
        f"✅ تم فتح التكت: {channel.mention}",
        ephemeral=True
    )


# ============================================================
# NEW SERVER - PANEL COMMANDS
# ============================================================

@bot.command(
    name="ticketsetup",
    help="إرسال بانلات الوساطة والدعم."
)
@new_admin_only()
async def ticketsetup(ctx):
    await safe_delete(ctx.message)

    mediator_embed = discord.Embed(
        title="🤝 7R COMMUNITY | نظام الوسطاء",
        description=(
            "مرحباً بك في نظام الوساطة.\n\n"
            "للطلب من وسيط، اضغط الزر أدناه لفتح تكت خاصة.\n\n"
            "🛡️ جميع عمليات الوساطة تتم داخل التكت."
        ),
        color=discord.Color.gold()
    )

    mediator_embed.set_footer(
        text="7R COMMUNITY • MEDIATOR SYSTEM"
    )

    support_embed = discord.Embed(
        title="🛠️ 7R COMMUNITY | الدعم الفني",
        description=(
            "واجهتك مشكلة؟\n"
            "تحتاج مساعدة من الإدارة؟\n\n"
            "اضغط الزر أدناه لفتح تكت دعم فني."
        ),
        color=discord.Color.blue()
    )

    await ctx.send(
        embed=mediator_embed,
        view=MediatorPanelView()
    )

    await ctx.send(
        embed=support_embed,
        view=SupportPanelView()
    )

    await ctx.send(
        "☑️ **7R COMMUNITY**\n"
        "نظام التذاكر مفعل بنجاح."
    )


# ============================================================
# NEW SERVER - SET PARTIES
# ============================================================

@bot.command(
    name="تحديد",
    aliases=["تحديد_الطرفين", "parties"],
    help="تحديد الطرف الأول والثاني في تكت الوساطة."
)
@new_only()
async def set_parties(
    ctx,
    party_one: discord.Member,
    party_two: discord.Member
):
    if not is_mediator(ctx.author):
        return await ctx.send(
            "❌ هذا الأمر للوسيط فقط."
        )

    record = get_ticket(ctx.channel.id)

    if not record or record.get("type") != "mediator":
        return await ctx.send(
            "❌ هذا الأمر يعمل داخل تكت وساطة فقط."
        )

    record["party_one"] = party_one.id
    record["party_two"] = party_two.id

    DB["tickets"][str(ctx.channel.id)] = record
    save_database()

    await ctx.send(
        "✅ **تم تحديد الطرفين:**\n"
        f"- الطرف الأول: {party_one.mention}\n"
        f"- الطرف الثاني: {party_two.mention}"
    )


# ============================================================
# NEW SERVER - ADD SECOND PARTY
# ============================================================

@bot.command(
    name="وسيط",
    aliases=["ضيف", "addparty"],
    help="إضافة عضو إلى تكت الوساطة."
)
@new_only()
async def add_party(ctx, member: discord.Member):
    if not is_mediator(ctx.author):
        return await ctx.send(
            "❌ هذا الأمر للوسيط فقط."
        )

    record = get_ticket(ctx.channel.id)

    if not record or record.get("type") != "mediator":
        return await ctx.send(
            "❌ هذا الأمر يعمل داخل تكت وساطة فقط."
        )

    try:
        await ctx.channel.set_permissions(
            member,
            view_channel=True,
            send_messages=True,
            read_message_history=True
        )

    except Exception as error:
        return await ctx.send(
            f"❌ تعذر إضافة العضو: `{error}`"
        )

    record["party_two"] = member.id
    DB["tickets"][str(ctx.channel.id)] = record
    save_database()

    await ctx.send(
        f"✅ تمت إضافة {member.mention} إلى التكت."
    )


# ============================================================
# NEW SERVER - NOTICE
# ============================================================

@bot.command(
    name="تنبيه",
    help="إرسال تنبيه الوساطة."
)
@new_only()
async def notice(ctx):
    if not is_mediator(ctx.author):
        return await ctx.send(
            "❌ هذا الأمر للوسيط فقط."
        )

    record = get_ticket(ctx.channel.id)

    if not record or record.get("type") != "mediator":
        return await ctx.send(
            "❌ هذا الأمر داخل تكت وساطة فقط."
        )

    mentions = []

    if record.get("party_one"):
        mentions.append(
            f"<@{record['party_one']}>"
        )

    if record.get("party_two"):
        mentions.append(
            f"<@{record['party_two']}>"
        )

    await ctx.send(
        content=" ".join(mentions) if mentions else None
    )

    await ctx.send(
        MEDIATOR_NOTICE
    )


# ============================================================
# NEW SERVER - ABANDON / RELEASE
# ============================================================

@bot.command(
    name="تخلي",
    aliases=["release", "unclaim"],
    help="تخلي الوسيط عن التكت."
)
@new_only()
async def release_ticket(ctx):
    if not is_mediator(ctx.author):
        return await ctx.send(
            "❌ الوسطاء فقط."
        )

    record = get_ticket(ctx.channel.id)

    if not record or record.get("type") != "mediator":
        return await ctx.send(
            "❌ هذه ليست تكت وساطة."
        )

    if (
        record.get("claimed_by")
        and record["claimed_by"] != ctx.author.id
        and ctx.author.id not in ADMIN_IDS
    ):
        return await ctx.send(
            "❌ هذا التكت مستلم من وسيط آخر."
        )

    record["claimed_by"] = None
    DB["tickets"][str(ctx.channel.id)] = record
    save_database()

    await ctx.send(
        f"🔄 {ctx.author.mention} تخلى عن التكت.\n"
        f"<@&{MEDIATOR_ROLE_ID}> يمكن الآن استلامه من جديد.",
        view=MediatorClaimView()
    )


# ============================================================
# NEW SERVER - COME
# ============================================================

@bot.command(
    name="come",
    help="استدعاء عضو في الخاص."
)
@new_only()
async def come_new(ctx, member: discord.Member, *, reason="بدون سبب"):
    if not is_mediator(ctx.author):
        return await ctx.send(
            "❌ هذا الأمر للوسطاء والإدارة فقط."
        )

    embed = discord.Embed(
        title="🚨 استدعاء من وسيط",
        description=(
            f"مرحباً {member.mention}\n\n"
            f"الوسيط: {ctx.author.mention}\n"
            f"السيرفر: **{ctx.guild.name}**\n"
            f"الروم: {ctx.channel.mention}\n\n"
            f"📌 **السبب:** {reason}"
        ),
        color=discord.Color.red()
    )

    try:
        await member.send(embed=embed)

        await ctx.send(
            f"✅ تم استدعاء {member.mention} في الخاص.",
            delete_after=10
        )

    except Exception:
        await ctx.send(
            "❌ خاص العضو مغلق.",
            delete_after=10
        )


# ============================================================
# NEW SERVER - END MEDIATION
# ============================================================

END_MESSAGE = """- **تمت عملية التوسط بنجاح من الطرف الوسيط {mediator}**
- **يرجة كتابة تم و تقييم الوسيط من طرف رسالة بتوصلك بلخاص **
- **احنا مش مسؤولين على اي شي يحصل بعد 5 دقايق من انتهاء التبادل **
- **لو عجبتك خدمه سيرفرنا لا تنسى تعيد تطلب مننا مره ثانية  **
- **لي للحصول على رتبة عميل مميز (<@1543276454895161455>) يرجى طلب وسيط 10 مرات و ان يتم التوسط بنجاح صور دلائلك و تعال تستلم رتبتك **"""


@bot.command(
    name="end",
    help="إنهاء عملية الوساطة + نقطة."
)
@new_only()
async def end_mediation(ctx):
    if not is_mediator(ctx.author):
        return await ctx.send(
            "❌ هذا الأمر للوسطاء فقط."
        )

    record = get_ticket(ctx.channel.id)

    if not record or record.get("type") != "mediator":
        return await ctx.send(
            "❌ هذا الأمر يعمل داخل تكت وساطة فقط."
        )

    if record.get("claimed_by") not in (
        None,
        ctx.author.id
    ) and ctx.author.id not in ADMIN_IDS:
        return await ctx.send(
            "❌ أنت لست الوسيط المستلم لهذا التكت."
        )

    if record.get("ended"):
        return await ctx.send(
            "❌ هذا التكت تم إنهاؤه مسبقاً."
        )

    record["claimed_by"] = ctx.author.id
    record["ended"] = True
    record["ended_at"] = datetime.utcnow().isoformat()

    DB["tickets"][str(ctx.channel.id)] = record

    add_mediator_point(ctx.author.id)
    add_mediator_ticket(ctx.author.id)

    save_database()

    await ctx.send(
        END_MESSAGE.format(
            mediator=ctx.author.mention
        )
    )

    # Send a separate rating request to both parties.
    party_ids = []

    if record.get("party_one"):
        party_ids.append(record["party_one"])

    if record.get("party_two"):
        party_ids.append(record["party_two"])

    # Remove duplicates.
    party_ids = list(dict.fromkeys(party_ids))

    for user_id in party_ids:
        member = ctx.guild.get_member(user_id)

        if member:
            await send_new_rating_dm(
                member,
                record["ticket_number"],
                ctx.author.id
            )

    # VIP eligibility notification after successful mediation.
    await ctx.send(
        f"🎫 تكت `{record['ticket_number']}` مكتملة.\n"
        f"⭐ نقاط الوسيط: `{get_points(ctx.author.id)}`"
    )


# ============================================================
# NEW SERVER - DELETE + TRANSCRIPT
# ============================================================

async def create_transcript(channel):
    lines = []

    try:
        async for message in channel.history(
            limit=None,
            oldest_first=True
        ):
            timestamp = message.created_at.strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            content = message.clean_content or "[بدون نص]"

            if message.attachments:
                content += (
                    " | "
                    + " ".join(
                        attachment.url
                        for attachment in message.attachments
                    )
                )

            lines.append(
                f"[{timestamp}] "
                f"{message.author} ({message.author.id}): "
                f"{content}"
            )

    except Exception as error:
        lines.append(
            f"[ERROR] {error}"
        )

    if not lines:
        lines.append("لا توجد رسائل.")

    return "\n".join(lines)


async def send_transcript(guild, channel, record):
    log_channel = guild.get_channel(
        TRANSCRIPT_CHANNEL_ID
    )

    if not log_channel:
        return

    transcript = await create_transcript(channel)

    path = (
        f"ticket_"
        f"{record.get('ticket_number', 'unknown')}.txt"
    )

    try:
        with open(
            path,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(transcript)

        embed = discord.Embed(
            title="🗃️ سجل تكت 7R COMMUNITY",
            description=(
                f"🎫 رقم التكت: "
                f"`#{record.get('ticket_number')}`\n"
                f"👤 الفاتح: "
                f"<@{record.get('opened_by')}>\n"
                f"🛡️ الوسيط: "
                f"<@{record.get('claimed_by')}>"
                if record.get("claimed_by")
                else
                f"🎫 رقم التكت: "
                f"`#{record.get('ticket_number')}`\n"
                f"👤 الفاتح: "
                f"<@{record.get('opened_by')}>"
            ),
            color=discord.Color.dark_gold()
        )

        await log_channel.send(
            embed=embed,
            file=discord.File(path)
        )

    except Exception as error:
        await log_channel.send(
            f"⚠️ تعذر إرسال transcript: `{error}`"
        )

    finally:
        try:
            os.remove(path)
        except Exception:
            pass


async def delete_new_ticket(channel, actor):
    record = get_ticket(channel.id)

    if not record:
        return

    guild = channel.guild

    # Save transcript BEFORE deleting.
    await send_transcript(
        guild,
        channel,
        record
    )

    # Remove client role from ticket opener.
    opener = guild.get_member(
        record.get("opened_by")
    )

    if opener:
        await remove_role(
            opener,
            MEDIATOR_CLIENT_ROLE_ID
        )

    DB["tickets"].pop(
        str(channel.id),
        None
    )

    save_database()

    try:
        await channel.delete(
            reason=f"Ticket deleted by {actor}"
        )
    except Exception:
        pass


@bot.command(
    name="delete",
    help="حذف تكت وإرسال transcript."
)
@new_admin_only()
async def delete_command(ctx):
    record = get_ticket(ctx.channel.id)

    if not record:
        return await ctx.send(
            "❌ هذه ليست تكت مسجلة."
        )

    await ctx.send(
        "🗃️ يتم حفظ transcript وحذف التكت..."
    )

    await asyncio.sleep(1)

    await delete_new_ticket(
        ctx.channel,
        ctx.author
    )


# ============================================================
# NEW SERVER - RATING
# ============================================================

class RatingView(discord.ui.View):
    def __init__(self, ticket_number, mediator_id):
        super().__init__(timeout=86400)

        self.ticket_number = ticket_number
        self.mediator_id = mediator_id

    async def rate(self, interaction, stars):
        if not self.mediator_id:
            return await interaction.response.send_message(
                "❌ لا يوجد وسيط مسجل.",
                ephemeral=True
            )

        add_rating(
            self.mediator_id,
            stars
        )

        # Disable all buttons.
        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(
            content=(
                f"❤️ شكراً لك على تقييمك: "
                f"`{'⭐' * stars}`"
            ),
            view=self
        )

        channel = interaction.guild.get_channel(
            RATING_CHANNEL_ID
        )

        # DM rating has no direct guild, so fetch guilds.
        if channel:
            await channel.send(
                embed=discord.Embed(
                    title="⭐ تقييم جديد",
                    description=(
                        f"🎫 **التكت:** `#{self.ticket_number}`\n"
                        f"👤 **العميل:** {interaction.user.mention}\n"
                        f"🛡️ **الوسيط:** <@{self.mediator_id}>\n"
                        f"⭐ **التقييم:** "
                        f"{'⭐' * stars}\n"
                        f"📊 **متوسط الوسيط:** "
                        f"`{get_average_rating(self.mediator_id)}/5`"
                    ),
                    color=discord.Color.gold()
                )
            )

    @discord.ui.button(
        label="⭐ 1",
        style=discord.ButtonStyle.danger
    )
    async def one(self, interaction, button):
        await self.rate(interaction, 1)

    @discord.ui.button(
        label="⭐ 2",
        style=discord.ButtonStyle.secondary
    )
    async def two(self, interaction, button):
        await self.rate(interaction, 2)

    @discord.ui.button(
        label="⭐ 3",
        style=discord.ButtonStyle.primary
    )
    async def three(self, interaction, button):
        await self.rate(interaction, 3)

    @discord.ui.button(
        label="⭐ 4",
        style=discord.ButtonStyle.success
    )
    async def four(self, interaction, button):
        await self.rate(interaction, 4)

    @discord.ui.button(
        label="⭐ 5",
        style=discord.ButtonStyle.success
    )
    async def five(self, interaction, button):
        await self.rate(interaction, 5)


async def send_new_rating_dm(
    member,
    ticket_number,
    mediator_id
):
    try:
        embed = discord.Embed(
            title="⭐ قيّم الوسيط",
            description=(
                f"تكت الوساطة `#{ticket_number}` انتهت.\n\n"
                "اختار عدد النجوم لتقييم الوسيط."
            ),
            color=discord.Color.gold()
        )

        await member.send(
            embed=embed,
            view=RatingView(
                ticket_number,
                mediator_id
            )
        )

    except Exception:
        pass


# ============================================================
# NEW SERVER - TOP
# ============================================================

@bot.command(
    name="top",
    help="Top الوسطاء."
)
@new_only()
async def top(ctx):
    # Combine users that have points/tickets.
    user_ids = set(
        list(DB["mediator_points"].keys())
        + list(DB["mediator_tickets"].keys())
    )

    ranking = []

    for user_id in user_ids:
        uid = int(user_id)

        ranking.append(
            (
                get_points(uid),
                get_mediator_ticket_count(uid),
                average_rating(uid),
                uid
            )
        )

    ranking.sort(
        key=lambda x: (
            x[0],
            x[1],
            x[2]
        ),
        reverse=True
    )

    if not ranking:
        return await ctx.send(
            "📊 لا توجد بيانات للوسطاء بعد."
        )

    lines = []

    for index, (
        points_value,
        tickets,
        rating,
        user_id
    ) in enumerate(ranking[:10], 1):

        member = ctx.guild.get_member(user_id)
        name = member.mention if member else f"<@{user_id}>"

        lines.append(
            f"**#{index}** {name}\n"
            f"   🎫 التذاكر: `{tickets}` | "
            f"⭐ النقاط: `{points_value}` | "
            f"📊 التقييم: `{rating}/5`"
        )

    embed = discord.Embed(
        title="🏆 7R COMMUNITY | TOP MEDIATORS",
        description="\n\n".join(lines),
        color=discord.Color.gold()
    )

    await ctx.send(embed=embed)


# ============================================================
# NEW SERVER - RESET / SETPOINTS
# ============================================================

@bot.command(
    name="reset",
    help="تصفير نقاط وسيط."
)
@new_admin_only()
async def reset_points(ctx, member: discord.Member):
    old = get_points(member.id)

    set_points(
        member.id,
        0
    )

    await ctx.send(
        f"♻️ تم تصفير نقاط {member.mention}.\n"
        f"قبل: `{old}` → بعد: `0`"
    )


@bot.command(
    name="setpoints",
    help="تحديد نقاط وسيط."
)
@new_admin_only()
async def set_mediator_points(
    ctx,
    member: discord.Member,
    amount: int
):
    if amount < 0:
        return await ctx.send(
            "❌ لا يمكن وضع نقاط سالبة."
        )

    old = get_points(member.id)

    set_points(
        member.id,
        amount
    )

    await ctx.send(
        f"🛠️ تم تعديل نقاط {member.mention}.\n"
        f"قبل: `{old}` → بعد: `{amount}`"
    )


# ============================================================
# NEW SERVER - ONLINE / DND
# ============================================================

@bot.command(
    name="online",
    help="عرض الوسطاء Offline / DND."
)
@new_admin_only()
async def online(ctx):
    offline = []
    dnd = []

    role = ctx.guild.get_role(
        MEDIATOR_ROLE_ID
    )

    if not role:
        return await ctx.send(
            "❌ رتبة الوسطاء غير موجودة."
        )

    for member in role.members:
        if member.bot:
            continue

        status = member.status

        if status == discord.Status.offline:
            offline.append(member)

        elif status == discord.Status.dnd:
            dnd.append(member)

    lines = [
        "🔴 **Offline:**",
        (
            "\n".join(
                f"• {m.mention}"
                for m in offline
            )
            or "لا يوجد"
        ),
        "",
        "⛔ **Do Not Disturb:**",
        (
            "\n".join(
                f"• {m.mention}"
                for m in dnd
            )
            or "لا يوجد"
        )
    ]

    await ctx.send(
        embed=discord.Embed(
            title="🛡️ حالة الوسطاء",
            description="\n".join(lines),
            color=discord.Color.red()
        )
    )


# ============================================================
# NEW SERVER - TAX
# ONLY NEW SERVER
# ============================================================

@bot.command(
    name="tax",
    help="حساب الضريبة."
)
@new_only()
async def tax(ctx, amount: str):
    parsed = parse_amount(amount)

    if parsed is None or parsed < 0:
        return await ctx.send(
            "❌ الرقم غير صحيح."
        )

    probot_tax = round(parsed * 0.05)
    total = parsed + probot_tax

    mediator_tax = round(
        parsed * 1.025 * 20 / 19
    )

    embed = discord.Embed(
        title="🧾 حساب الضرائب والوسيط",
        description=(
            f"🔹 **المبلغ الأصلي:** `{parsed:,}`\n\n"
            f"📊 **ضريبة البروبوت 5%:** "
            f"`{probot_tax:,}`\n"
            f"💰 **مع الضريبة:** `{total:,}`\n\n"
            f"🤝 **المبلغ المطلوب للوسيط:** "
            f"`{mediator_tax:,}`"
        ),
        color=discord.Color.pink()
    )

    await ctx.send(embed=embed)


# ============================================================
# NEW SERVER - MASSDM
# ONLY NEW SERVER
# ============================================================

@bot.command(
    name="massdm",
    aliases=["broadcast", "dmall"],
    help="إرسال إعلان للأعضاء المتصلين."
)
@new_admin_only()
async def massdm(ctx, *, message_content: str):
    await safe_delete(ctx.message)

    guild = ctx.guild

    members = [
        member
        for member in guild.members
        if (
            not member.bot
            and member.status != discord.Status.offline
        )
    ]

    if not members:
        return await ctx.send(
            "⚠️ لا يوجد أعضاء Online.",
            delete_after=10
        )

    total = len(members)

    progress = await ctx.send(
        f"⏳ جاري الإرسال... `0/{total}`"
    )

    success = 0
    failed = 0

    for index, member in enumerate(
        members,
        1
    ):
        try:
            embed = discord.Embed(
                title=f"📢 إعلان من {guild.name}",
                description=message_content,
                color=discord.Color.gold()
            )

            await member.send(embed=embed)
            success += 1

        except Exception:
            failed += 1

        if (
            index % 5 == 0
            or index == total
        ):
            percent = int(
                index / total * 100
            )

            try:
                await progress.edit(
                    content=(
                        f"🚀 **جاري الإرسال**\n"
                        f"`{percent}%` — "
                        f"`{index}/{total}`\n"
                        f"✅ نجاح: `{success}`\n"
                        f"❌ فشل: `{failed}`"
                    )
                )
            except Exception:
                pass

        # Small delay to reduce burst.
        if index < total:
            await asyncio.sleep(
                random.uniform(2.0, 4.0)
            )

    await progress.edit(
        content=(
            "📊 **انتهى البرودكاست**\n"
            f"✅ نجاح: `{success}`\n"
            f"❌ فشل: `{failed}`\n"
            f"👥 المجموع: `{total}`"
        )
    )


# ============================================================
# NEW SERVER - LIST
# ============================================================

NEW_COMMANDS = [
    "$ticketsetup",
    "$تحديد @الطرف1 @الطرف2",
    "$وسيط @العضو",
    "$تنبيه",
    "$تخلي",
    "$end",
    "$delete",
    "$top",
    "$reset @الوسيط",
    "$setpoints @الوسيط العدد",
    "$online",
    "$come @العضو السبب",
    "$tax المبلغ",
    "$massdm النص",
    "$list"
]


@bot.command(
    name="newlist",
    aliases=["listnew"],
    help="قائمة أوامر السيرفر الجديد."
)
@new_admin_only()
async def new_list(ctx):
    embed = discord.Embed(
        title="📋 7R COMMUNITY | أوامر الإدارة",
        description="\n".join(
            f"🔹 `{command}`"
            for command in NEW_COMMANDS
        ),
        color=discord.Color.gold()
    )

    await ctx.author.send(embed=embed)

    await ctx.send(
        "✅ تم إرسال قائمة الأوامر إلى الخاص.",
        delete_after=10
    )


# IMPORTANT:
# $list itself must also work on the NEW server.
@bot.command(
    name="list",
    help="قائمة أوامر السيرفر."
)
async def universal_list(ctx):
    if ctx.guild is None:
        return

    if ctx.guild.id == OLD_GUILD_ID:
        if ctx.author.id not in ADMIN_IDS:
            return await ctx.send(
                "❌ للإدارة فقط."
            )

        embed = discord.Embed(
            title="📋 أوامر السيرفر القديم",
            description="\n".join(
                f"🔹 `{x}`"
                for x in OLD_COMMANDS
            ),
            color=discord.Color.dark_gold()
        )

        try:
            await ctx.author.send(embed=embed)
            await ctx.send(
                "✅ أرسلت لك القائمة في الخاص.",
                delete_after=10
            )
        except Exception:
            await ctx.send(
                "❌ افتح الخاص DM.",
                delete_after=10
            )

    elif ctx.guild.id == NEW_GUILD_ID:
        if ctx.author.id not in ADMIN_IDS:
            return await ctx.send(
                "❌ هذا الأمر للإدارة فقط."
            )

        embed = discord.Embed(
            title="📋 7R COMMUNITY | أوامر السيرفر الجديد",
            description="\n".join(
                f"🔹 `{x}`"
                for x in NEW_COMMANDS
            ),
            color=discord.Color.gold()
        )

        try:
            await ctx.author.send(embed=embed)
            await ctx.send(
                "✅ أرسلت لك القائمة في الخاص.",
                delete_after=10
            )
        except Exception:
            await ctx.send(
                "❌ افتح الخاص DM.",
                delete_after=10
            )


# ============================================================
# ERROR HANDLING
# ============================================================

@bot.event
async def on_command_error(ctx, error):
    if isinstance(
        error,
        commands.CommandNotFound
    ):
        return

    if isinstance(
        error,
        commands.MissingRequiredArgument
    ):
        return await ctx.send(
            "❌ ناقصك argument في الأمر.",
            delete_after=10
        )

    if isinstance(
        error,
        commands.MemberNotFound
    ):
        return await ctx.send(
            "❌ ما لقيتش العضو.",
            delete_after=10
        )

    if isinstance(
        error,
        commands.BadArgument
    ):
        return await ctx.send(
            "❌ تأكد من طريقة استعمال الأمر.",
            delete_after=10
        )

    if isinstance(
        error,
        commands.CheckFailure
    ):
        # Silently reject commands in the wrong server.
        # This is intentional for server separation.
        return

    print(
        f"Command error in {ctx.command}:"
    )
    traceback.print_exception(
        type(error),
        error,
        error.__traceback__
    )


# ============================================================
# REGISTER PERSISTENT VIEWS
# ============================================================

@bot.event
async def setup_hook():
    bot.add_view(MediatorPanelView())
    bot.add_view(SupportPanelView())
    bot.add_view(MediatorClaimView())
    bot.add_view(SupportCloseView())


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    token = os.environ.get("DISCORD_TOKEN")

    if not token:
        print(
            "ERROR: DISCORD_TOKEN is not set."
        )
        raise SystemExit(1)

    try:
        bot.run(token)

    except Exception:
        print("\n[!] Bot startup error:")
        traceback.print_exc()
