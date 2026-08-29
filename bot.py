import asyncio
import os
import random
import json
import traceback
from datetime import datetime

import discord
from discord.ext import commands


# ============================================================
# 7R COMMUNITY - FULL DISCORD BOT
# ============================================================

INTENTS = discord.Intents.default()
INTENTS.members = True
INTENTS.message_content = True
INTENTS.presences = True

bot = commands.Bot(
    command_prefix="$",
    intents=INTENTS,
    help_command=None
)


# ============================================================
# IDS
# ============================================================

OWNER_IDS = {
    1021501331636244490,
    1133434766738329640
}

ADMIN_ROLE_ID = 1543149771299094650
MEDIATOR_ROLE_ID = 1543142907958001768

MEDIATOR_CATEGORY_ID = 1540776952787632220
SUPPORT_CATEGORY_ID = 1540776960500699167

TRANSCRIPT_CHANNEL_ID = 1543277110951678155
RATING_CHANNEL_ID = 1540776982265073765

MEDIATOR_CLIENT_ROLE_ID = 1543275873426342039


# ============================================================
# DATABASE
# ============================================================

DB_FILE = "7r_database.json"

DB = {
    "credits": {},
    "tickets": {},
    "mediator_points": {},
    "mediator_tickets": {},
    "ratings": {},
    "ticket_counter": 0
}


def load_database():
    global DB

    if not os.path.exists(DB_FILE):
        save_database()
        return

    try:
        with open(DB_FILE, "r", encoding="utf-8") as file:
            loaded = json.load(file)

        if isinstance(loaded, dict):
            for key in DB:
                if key in loaded:
                    DB[key] = loaded[key]

    except Exception:
        print("⚠️ تعذر تحميل قاعدة البيانات.")


def save_database():
    try:
        with open(
            DB_FILE,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                DB,
                file,
                ensure_ascii=False,
                indent=4
            )
    except Exception as error:
        print(f"❌ Database save error: {error}")


load_database()


# ============================================================
# BASIC FUNCTIONS
# ============================================================

def update_credit(user_id, amount):
    uid = str(user_id)

    DB["credits"][uid] = (
        DB["credits"].get(uid, 0) + amount
    )

    save_database()


def get_credit(user_id):
    return DB["credits"].get(
        str(user_id),
        0
    )


def get_ticket(channel_id):
    return DB["tickets"].get(
        str(channel_id)
    )


def next_ticket_number():
    DB["ticket_counter"] = (
        DB.get("ticket_counter", 0) + 1
    )

    save_database()

    return DB["ticket_counter"]


def is_owner(member):
    return member.id in OWNER_IDS


def is_admin(member):
    if member.id in OWNER_IDS:
        return True

    if member.guild_permissions.administrator:
        return True

    role = member.guild.get_role(
        ADMIN_ROLE_ID
    )

    return bool(
        role and role in member.roles
    )


def is_mediator(member):
    if is_admin(member):
        return True

    role = member.guild.get_role(
        MEDIATOR_ROLE_ID
    )

    return bool(
        role and role in member.roles
    )


def add_mediator_point(user_id):
    uid = str(user_id)

    DB["mediator_points"][uid] = (
        DB["mediator_points"].get(uid, 0) + 1
    )

    save_database()


def add_mediator_ticket(user_id):
    uid = str(user_id)

    DB["mediator_tickets"][uid] = (
        DB["mediator_tickets"].get(uid, 0) + 1
    )

    save_database()


def get_points(user_id):
    return DB["mediator_points"].get(
        str(user_id),
        0
    )


def set_points(user_id, amount):
    DB["mediator_points"][str(user_id)] = amount
    save_database()


def get_mediator_ticket_count(user_id):
    return DB["mediator_tickets"].get(
        str(user_id),
        0
    )


def add_rating(user_id, stars):
    uid = str(user_id)

    if uid not in DB["ratings"]:
        DB["ratings"][uid] = []

    DB["ratings"][uid].append(stars)

    save_database()


def get_average_rating(user_id):
    ratings = DB["ratings"].get(
        str(user_id),
        []
    )

    if not ratings:
        return 0.0

    return round(
        sum(ratings) / len(ratings),
        1
    )


def average_rating(user_id):
    return get_average_rating(user_id)


def parse_amount(amount_str):
    try:
        cleaned = (
            amount_str
            .replace(",", "")
            .replace("_", "")
            .strip()
        )

        lower = cleaned.lower()

        if lower.endswith("k"):
            return int(
                float(lower[:-1]) * 1_000
            )

        if lower.endswith("m"):
            return int(
                float(lower[:-1]) * 1_000_000
            )

        return int(float(cleaned))

    except Exception:
        return None


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


async def require_admin(ctx):
    if not is_admin(ctx.author):
        await ctx.send(
            "❌ هذا الأمر للإدارة فقط.",
            delete_after=10
        )
        return False

    return True


async def require_mediator(ctx):
    if not is_mediator(ctx.author):
        await ctx.send(
            "❌ هذا الأمر للوسطاء والإدارة فقط.",
            delete_after=10
        )
        return False

    return True


# ============================================================
# MEDIATOR NOTICE
# ============================================================

MEDIATOR_NOTICE = """- **السيرفر والوسطاء يخترون المسؤولية تماما ولا يتحمل أي تعويض إذا تم سحب الحساب أثناء أو بعد التوسط**
**السبب :**
**`#` اللعبة شددت على حماية الحسابات وقد أصبحت الحسابات في خطر لتقفيل الحساب أثناء التوسط أو ترجيعه من الطرف الثاني**
__**مثلا**__
**`#` قام الطرف الثاني بسحب الحساب عن طريق دعم اللعبة فالوسيط والسيرفر ليس لهم دخل في أمر الحساب الذي تم استرجاعه**
**__هل أنتم موافقون؟__**"""


END_MESSAGE = """- **تمت عملية التوسط بنجاح من الطرف الوسيط {mediator}**
- **يرجى كتابة تم وتقييم الوسيط من طرف رسالة بتوصلك بالخاص**
- **احنا مش مسؤولين على أي شيء يحصل بعد 5 دقائق من انتهاء التبادل**
- **لو عجبتك خدمة سيرفرنا لا تنسى تعيد تطلب مننا مرة ثانية**
- **للحصول على رتبة عميل مميز (<@1543275873426342039>) يرجى طلب وسيط 10 مرات وأن يتم التوسط بنجاح، صور دلائلك وتعال تستلم رتبتك**"""


# ============================================================
# RATING VIEW
# ============================================================

class RatingView(discord.ui.View):

    def __init__(self, ticket_number, mediator_id):
        super().__init__(timeout=86400)

        self.ticket_number = ticket_number
        self.mediator_id = mediator_id
        self.rated = False

    async def rate(self, interaction, stars):

        if self.rated:
            return await interaction.response.send_message(
                "❌ لقد قمت بالتقييم من قبل.",
                ephemeral=True
            )

        if not self.mediator_id:
            return await interaction.response.send_message(
                "❌ لا يوجد وسيط مسجل.",
                ephemeral=True
            )

        self.rated = True

        add_rating(
            self.mediator_id,
            stars
        )

        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(
            content=(
                "❤️ شكراً لك على تقييمك!\n"
                f"تقييمك: `{'⭐' * stars}`"
            ),
            view=self
        )

        channel = interaction.client.get_channel(
            RATING_CHANNEL_ID
        )

        if channel:
            try:
                await channel.send(
                    embed=discord.Embed(
                        title="⭐ تقييم جديد",
                        description=(
                            f"🎫 **التكت:** `#{self.ticket_number}`\n"
                            f"👤 **العميل:** {interaction.user.mention}\n"
                            f"🛡️ **الوسيط:** <@{self.mediator_id}>\n"
                            f"⭐ **التقييم:** {'⭐' * stars}\n"
                            f"📊 **المتوسط:** "
                            f"`{get_average_rating(self.mediator_id)}/5`"
                        ),
                        color=discord.Color.gold()
                    )
                )
            except Exception:
                pass

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
# MEDIATOR CLAIM VIEW
# ============================================================

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

        if not is_mediator(interaction.user):
            return await interaction.response.send_message(
                "❌ هذا الزر للوسطاء فقط.",
                ephemeral=True
            )

        record = get_ticket(
            interaction.channel.id
        )

        if not record or record.get("type") != "mediator":
            return await interaction.response.send_message(
                "❌ هذه ليست تذكرة وساطة.",
                ephemeral=True
            )

        if record.get("ended"):
            return await interaction.response.send_message(
                "❌ هذه التذكرة منتهية.",
                ephemeral=True
            )

        if record.get("claimed_by"):
            return await interaction.response.send_message(
                f"❌ التكت مستلم من <@{record['claimed_by']}>.",
                ephemeral=True
            )

        record["claimed_by"] = interaction.user.id

        DB["tickets"][
            str(interaction.channel.id)
        ] = record

        save_database()

        button.disabled = True
        button.label = "تم الاستلام"
        button.emoji = "✅"

        await interaction.response.edit_message(
            view=self
        )

        await interaction.channel.send(
            f"🛡️ **تم استلام التكت بواسطة "
            f"{interaction.user.mention}**\n\n"
            "**- سلعة الطرف الأول :**\n"
            "**- سلعة الطرف الثاني :**\n"
            "**- يوزر الطرف الثاني :**\n\n"
            f"👤 الطرف الذي فتح التكت: "
            f"<@{record['opened_by']}>"
        )


# ============================================================
# SUPPORT CLOSE VIEW
# ============================================================

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

        await delete_ticket(
            interaction.channel,
            interaction.user
        )


# ============================================================
# TICKET PANELS
# ============================================================

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
        await open_ticket(
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
        await open_ticket(
            interaction,
            "support"
        )


# ============================================================
# OPEN TICKET
# ============================================================

async def open_ticket(
    interaction,
    ticket_type
):

    guild = interaction.guild
    member = interaction.user

    existing = None

    for channel in guild.text_channels:

        record = get_ticket(channel.id)

        if (
            record
            and record.get("opened_by") == member.id
            and record.get("type") == ticket_type
            and not record.get("ended")
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

        role_id = ADMIN_ROLE_ID

        title = "🛠️ تكت دعم فني"

    ticket_number = next_ticket_number()

    overwrites = {

        guild.default_role:
            discord.PermissionOverwrite(
                view_channel=False
            ),

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
                if isinstance(
                    category,
                    discord.CategoryChannel
                )
                else None
            ),

            overwrites=overwrites,

            topic=(
                f"7R Ticket #{ticket_number} | "
                f"{ticket_type}"
            )
        )

    except Exception as error:

        return await interaction.response.send_message(
            f"❌ لم أستطع إنشاء التكت:\n`{error}`",
            ephemeral=True
        )

    DB["tickets"][
        str(channel.id)
    ] = {

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

        embed.set_footer(
            text="7R COMMUNITY • MEDIATOR SYSTEM"
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
                f"مرحباً {member.mention}\n\n"
                f"رقم التكت: `#{ticket_number}`\n\n"
                "اكتب مشكلتك بالتفصيل، "
                "وسيقوم فريق الإدارة بمساعدتك."
            ),
            color=discord.Color.blue()
        )

        await channel.send(
            content=(
                f"{member.mention} "
                f"<@&{ADMIN_ROLE_ID}>"
            ),
            embed=embed,
            view=SupportCloseView()
        )

    await interaction.response.send_message(
        f"✅ تم فتح التكت: {channel.mention}",
        ephemeral=True
    )


# ============================================================
# TICKET SETUP
# ============================================================

@bot.command(
    name="ticketsetup"
)
async def ticketsetup(ctx):

    if not await require_admin(ctx):
        return

    await safe_delete(ctx.message)

    mediator_embed = discord.Embed(
        title="🤝 7R COMMUNITY | نظام الوسطاء",
        description=(
            "مرحباً بك في نظام الوساطة.\n\n"
            "للطلب من وسيط، اضغط الزر أدناه "
            "لفتح تكت خاصة.\n\n"
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
# تحديد الطرفين
# ============================================================

@bot.command(
    name="تحديد",
    aliases=[
        "تحديد_الطرفين",
        "parties"
    ]
)
async def set_parties(
    ctx,
    party_one: discord.Member,
    party_two: discord.Member
):

    if not await require_mediator(ctx):
        return

    record = get_ticket(
        ctx.channel.id
    )

    if not record or record.get("type") != "mediator":
        return await ctx.send(
            "❌ هذا الأمر يعمل داخل تكت وساطة فقط."
        )

    record["party_one"] = party_one.id
    record["party_two"] = party_two.id

    DB["tickets"][
        str(ctx.channel.id)
    ] = record

    save_database()

    await ctx.send(
        "✅ **تم تحديد الطرفين:**\n"
        f"- الطرف الأول: {party_one.mention}\n"
        f"- الطرف الثاني: {party_two.mention}"
    )


# ============================================================
# وسيط / إضافة عضو
# ============================================================

@bot.command(
    name="وسيط",
    aliases=[
        "ضيف",
        "addparty"
    ]
)
async def add_party(
    ctx,
    member: discord.Member
):

    if not await require_mediator(ctx):
        return

    record = get_ticket(
        ctx.channel.id
    )

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

    DB["tickets"][
        str(ctx.channel.id)
    ] = record

    save_database()

    await ctx.send(
        f"✅ تمت إضافة {member.mention} إلى التكت."
    )


# ============================================================
# تنبيه
# ============================================================

@bot.command(
    name="تنبيه"
)
async def notice(ctx):

    if not await require_mediator(ctx):
        return

    record = get_ticket(
        ctx.channel.id
    )

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

    if mentions:

        await ctx.send(
            content=" ".join(mentions)
        )

    await ctx.send(
        MEDIATOR_NOTICE
    )


# ============================================================
# تخلي
# ============================================================

@bot.command(
    name="تخلي",
    aliases=[
        "release",
        "unclaim"
    ]
)
async def release_ticket(ctx):

    if not await require_mediator(ctx):
        return

    record = get_ticket(
        ctx.channel.id
    )

    if not record or record.get("type") != "mediator":
        return await ctx.send(
            "❌ هذه ليست تكت وساطة."
        )

    if (
        record.get("claimed_by")
        and record["claimed_by"] != ctx.author.id
        and not is_admin(ctx.author)
    ):
        return await ctx.send(
            "❌ هذا التكت مستلم من وسيط آخر."
        )

    record["claimed_by"] = None

    DB["tickets"][
        str(ctx.channel.id)
    ] = record

    save_database()

    await ctx.send(
        f"🔄 {ctx.author.mention} تخلى عن التكت.\n"
        f"<@&{MEDIATOR_ROLE_ID}> "
        "يمكن الآن استلامه من جديد.",
        view=MediatorClaimView()
    )


# ============================================================
# COME
# ============================================================

@bot.command(
    name="come"
)
async def come(ctx, member: discord.Member, *, reason="بدون سبب"):

    if not await require_mediator(ctx):
        return

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

        await member.send(
            embed=embed
        )

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
# END MEDIATION
# ============================================================

@bot.command(
    name="end"
)
async def end_mediation(ctx):

    if not await require_mediator(ctx):
        return

    record = get_ticket(
        ctx.channel.id
    )

    if not record or record.get("type") != "mediator":
        return await ctx.send(
            "❌ هذا الأمر يعمل داخل تكت وساطة فقط."
        )

    claimed_by = record.get(
        "claimed_by"
    )

    if (
        claimed_by
        and claimed_by != ctx.author.id
        and not is_admin(ctx.author)
    ):
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

    DB["tickets"][
        str(ctx.channel.id)
    ] = record

    add_mediator_point(
        ctx.author.id
    )

    add_mediator_ticket(
        ctx.author.id
    )

    save_database()

    await ctx.send(
        END_MESSAGE.format(
            mediator=ctx.author.mention
        )
    )

    party_ids = []

    if record.get("party_one"):
        party_ids.append(
            record["party_one"]
        )

    if record.get("party_two"):
        party_ids.append(
            record["party_two"]
        )

    party_ids = list(
        dict.fromkeys(party_ids)
    )

    for user_id in party_ids:

        member = ctx.guild.get_member(
            user_id
        )

        if member:

            await send_new_rating_dm(
                member,
                record["ticket_number"],
                ctx.author.id
            )

    await ctx.send(
        f"🎫 تكت `{record['ticket_number']}` مكتملة.\n"
        f"⭐ نقاط الوسيط: `{get_points(ctx.author.id)}`"
    )


# ============================================================
# TRANSCRIPT
# ============================================================

async def create_transcript(channel):

    lines = []

    try:

        async for message in channel.history(
            limit=None,
            oldest_first=True
        ):

            timestamp = (
                message.created_at
                .strftime("%Y-%m-%d %H:%M:%S")
            )

            content = (
                message.clean_content
                or "[بدون نص]"
            )

            if message.attachments:

                content += (
                    " | "
                    + " ".join(
                        attachment.url
                        for attachment
                        in message.attachments
                    )
                )

            lines.append(
                f"[{timestamp}] "
                f"{message.author} "
                f"({message.author.id}): "
                f"{content}"
            )

    except Exception as error:

        lines.append(
            f"[ERROR] {error}"
        )

    if not lines:
        lines.append(
            "لا توجد رسائل."
        )

    return "\n".join(lines)


async def send_transcript(
    guild,
    channel,
    record
):

    log_channel = guild.get_channel(
        TRANSCRIPT_CHANNEL_ID
    )

    if not log_channel:
        return

    transcript = await create_transcript(
        channel
    )

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

            file.write(
                transcript
            )

        description = (
            f"🎫 رقم التكت: "
            f"`#{record.get('ticket_number')}`\n"
            f"📁 النوع: "
            f"`{record.get('type')}`\n"
            f"👤 الفاتح: "
            f"<@{record.get('opened_by')}>\n"
        )

        if record.get("claimed_by"):

            description += (
                f"🛡️ الوسيط: "
                f"<@{record.get('claimed_by')}>"
            )

        embed = discord.Embed(
            title="🗃️ سجل تكت 7R COMMUNITY",
            description=description,
            color=discord.Color.dark_gold()
        )

        await log_channel.send(
            embed=embed,
            file=discord.File(path)
        )

    except Exception as error:

        try:
            await log_channel.send(
                f"⚠️ تعذر إرسال transcript: `{error}`"
            )
        except Exception:
            pass

    finally:

        try:
            os.remove(path)
        except Exception:
            pass


# ============================================================
# DELETE TICKET
# ============================================================

async def delete_ticket(
    channel,
    actor
):

    record = get_ticket(
        channel.id
    )

    if not record:
        return

    guild = channel.guild

    await send_transcript(
        guild,
        channel,
        record
    )

    opener = guild.get_member(
        record.get("opened_by")
    )

    if opener and record.get("type") == "mediator":

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
            reason=(
                f"Ticket deleted by "
                f"{actor}"
            )
        )

    except Exception:
        pass


# ============================================================
# DELETE COMMAND
# ============================================================

@bot.command(
    name="delete"
)
async def delete_command(ctx):

    if not await require_admin(ctx):
        return

    record = get_ticket(
        ctx.channel.id
    )

    if not record:
        return await ctx.send(
            "❌ هذه ليست تكت مسجلة."
        )

    await ctx.send(
        "🗃️ يتم حفظ transcript وحذف التكت..."
    )

    await asyncio.sleep(1)

    await delete_ticket(
        ctx.channel,
        ctx.author
    )


# ============================================================
# TOP MEDIATORS
# ============================================================

@bot.command(
    name="top"
)
async def top(ctx):

    user_ids = set(
        list(
            DB["mediator_points"].keys()
        )
        +
        list(
            DB["mediator_tickets"].keys()
        )
    )

    ranking = []

    for user_id in user_ids:

        try:
            uid = int(user_id)
        except Exception:
            continue

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
    ) in enumerate(
        ranking[:10],
        1
    ):

        member = ctx.guild.get_member(
            user_id
        )

        name = (
            member.mention
            if member
            else f"<@{user_id}>"
        )

        lines.append(
            f"**#{index}** {name}\n"
            f"🎫 التذاكر: `{tickets}` | "
            f"⭐ النقاط: `{points_value}` | "
            f"📊 التقييم: `{rating}/5`"
        )

    embed = discord.Embed(
        title="🏆 7R COMMUNITY | TOP MEDIATORS",
        description="\n\n".join(lines),
        color=discord.Color.gold()
    )

    await ctx.send(
        embed=embed
    )


# ============================================================
# RESET POINTS
# ============================================================

@bot.command(
    name="reset"
)
async def reset_points(
    ctx,
    member: discord.Member
):

    if not await require_admin(ctx):
        return

    old = get_points(
        member.id
    )

    set_points(
        member.id,
        0
    )

    await ctx.send(
        f"♻️ تم تصفير نقاط {member.mention}.\n"
        f"قبل: `{old}` → بعد: `0`"
    )


# ============================================================
# SET POINTS
# ============================================================

@bot.command(
    name="setpoints"
)
async def set_mediator_points(
    ctx,
    member: discord.Member,
    amount: int
):

    if not await require_admin(ctx):
        return

    if amount < 0:

        return await ctx.send(
            "❌ لا يمكن وضع نقاط سالبة."
        )

    old = get_points(
        member.id
    )

    set_points(
        member.id,
        amount
    )

    await ctx.send(
        f"🛠️ تم تعديل نقاط {member.mention}.\n"
        f"قبل: `{old}` → بعد: `{amount}`"
    )


# ============================================================
# ONLINE / OFFLINE / DND
# ============================================================

@bot.command(
    name="online"
)
async def online(ctx):

    if not await require_admin(ctx):
        return

    role = ctx.guild.get_role(
        MEDIATOR_ROLE_ID
    )

    if not role:

        return await ctx.send(
            "❌ رتبة الوسطاء غير موجودة."
        )

    offline = []
    dnd = []

    for member in role.members:

        if member.bot:
            continue

        if member.status == discord.Status.offline:

            offline.append(member)

        elif member.status == discord.Status.dnd:

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
# TAX
# ============================================================

@bot.command(
    name="tax"
)
async def tax(
    ctx,
    amount: str
):

    parsed = parse_amount(
        amount
    )

    if parsed is None or parsed < 0:

        return await ctx.send(
            "❌ الرقم غير صحيح."
        )

    probot_tax = round(
        parsed * 0.05
    )

    total = parsed + probot_tax

    mediator_tax = round(
        parsed * 1.025 * 20 / 19
    )

    embed = discord.Embed(
        title="🧾 حساب الضرائب والوسيط",
        description=(
            f"🔹 **المبلغ الأصلي:** "
            f"`{parsed:,}`\n\n"

            f"📊 **ضريبة البروبوت 5%:** "
            f"`{probot_tax:,}`\n"

            f"💰 **مع الضريبة:** "
            f"`{total:,}`\n\n"

            f"🤝 **المبلغ المطلوب للوسيط:** "
            f"`{mediator_tax:,}`"
        ),
        color=discord.Color.pink()
    )

    await ctx.send(
        embed=embed
    )


# ============================================================
# MASS DM
# ============================================================

@bot.command(
    name="massdm",
    aliases=[
        "broadcast",
        "dmall"
    ]
)
async def massdm(
    ctx,
    *,
    message_content: str
):

    if not await require_admin(ctx):
        return

    await safe_delete(
        ctx.message
    )

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

            await member.send(
                embed=embed
            )

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

        if index < total:

            await asyncio.sleep(
                random.uniform(
                    2.0,
                    4.0
                )
            )

    await progress.edit(
        content=(
            "📊 **انتهى البرودكاست**\n"
            f"✅ نجاح: `{success}`\n"
            f"❌فشل: `{failed}`\n"
            f"👥 المجموع: `{total}`"
        )
    )


# ============================================================
# NEW SERVER COMMANDS LIST
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
    help="قائمة أوامر الإدارة."
)
async def new_list(ctx):

    embed = discord.Embed(
        title="📋 7R COMMUNITY | أوامر الإدارة",
        description="\n".join(
            f"🔹 `{command}`"
            for command in NEW_COMMANDS
        ),
        color=discord.Color.gold()
    )

    try:
        await ctx.author.send(
            embed=embed
        )

        await ctx.send(
            "✅ تم إرسال قائمة الأوامر إلى الخاص.",
            delete_after=10
        )

    except Exception:
        await ctx.send(
            "❌ افتح الخاص DM.",
            delete_after=10
        )


# ============================================================
# UNIVERSAL LIST
# يعمل في السيرفرين
# ============================================================

@bot.command(
    name="list",
    aliases=["commands", "cmds"],
    help="عرض قائمة أوامر البوت."
)
async def universal_list(ctx):

    if ctx.guild is None:
        return

    all_commands = [
        "💎 **نظام النقاط**",
        "`$points` / `$pts` / `$credit` / `$balance`",
        "`$transfer @member amount`",
        "`$withdraw amount`",
        "`$profit price cost`",
        "",
        "🎮 **الألعاب**",
        "`$games` / `$play`",
        "`$xo`",
        "`$roulette`",
        "`$rps`",
        "",
        "🎫 **التذاكر والوساطة**",
        "`$ticketsetup`",
        "`$تحديد @الطرف1 @الطرف2`",
        "`$وسيط @العضو`",
        "`$تنبيه`",
        "`$تخلي`",
        "`$end`",
        "`$delete`",
        "",
        "🛡️ **الإدارة**",
        "`$top`",
        "`$reset @الوسيط`",
        "`$setpoints @الوسيط العدد`",
        "`$online`",
        "`$come @العضو السبب`",
        "`$say النص`",
        "`$massdm النص`",
        "",
        "🧾 **أخرى**",
        "`$tax المبلغ`",
        "`$suggest`",
        "`$remind`",
        "`$rate`",
        "`$serverinfo` / `$sinfo`"
    ]

    embed = discord.Embed(
        title="📋 7R COMMUNITY | أوامر البوت",
        description="\n".join(all_commands),
        color=discord.Color.gold()
    )

    try:

        await ctx.author.send(
            embed=embed
        )

        await ctx.send(
            "✅ أرسلت لك قائمة الأوامر في الخاص.",
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
        await ctx.send(
            "❌ ناقصك argument في الأمر.",
            delete_after=10
        )
        return

    if isinstance(
        error,
        commands.MemberNotFound
    ):
        await ctx.send(
            "❌ ما لقيتش العضو.",
            delete_after=10
        )
        return

    if isinstance(
        error,
        commands.BadArgument
    ):
        await ctx.send(
            "❌ تأكد من طريقة استعمال الأمر.",
            delete_after=10
        )
        return

    if isinstance(
        error,
        commands.CheckFailure
    ):
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
# BOT READY
# ============================================================

@bot.event
async def on_ready():

    print(
        "=================================================="
    )

    print(
        f"✅ 7R COMMUNITY BOT ONLINE"
    )

    print(
        f"🤖 Bot: {bot.user}"
    )

    print(
        f"🆔 Bot ID: {bot.user.id}"
    )

    print(
        f"🌐 Servers: {len(bot.guilds)}"
    )

    print(
        "=================================================="
    )


# ============================================================
# REGISTER PERSISTENT VIEWS
# ============================================================

@bot.event
async def setup_hook():

    bot.add_view(
        MediatorPanelView()
    )

    bot.add_view(
        SupportPanelView()
    )

    bot.add_view(
        MediatorClaimView()
    )

    bot.add_view(
        SupportCloseView()
    )


# ============================================================
# START BOT
# ============================================================

if __name__ == "__main__":

    token = os.environ.get(
        "DISCORD_TOKEN"
    )

    if not token:

        print(
            "❌ ERROR: DISCORD_TOKEN is not set."
        )

        raise SystemExit(1)

    try:

        bot.run(
            token
        )

    except Exception:

        print(
            "\n[!] Bot startup error:"
        )

        traceback.print_exc()
