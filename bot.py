import discord
from discord.ext import commands
import asyncio
import random
import traceback
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="$", intents=intents)

store_credits = {}
EXCHANGE_RATE = 10  

# الآيدي الخاص بك بوحدك (صاحب السيرفر / المالك - التحكم الكامل في النقاط)
OWNER_ID = 1021501331636244490  

# الإدارة العامة (باقي الأوامر مثل come, massdm, say, الخ)
ADMIN_IDS = [1021501331636244490, 1133434766738329640]

FEEDBACK_CHANNEL_ID = 1541011452037439489  
REPORTS_CHANNEL_ID = 1540809388800081941
WELCOME_CHANNEL_ID = 1538994818150170714  
LOGS_CHANNEL_ID = 1538994821455282197  
DIVIDER_IMAGE_URL = "https://cdn.discordapp.com/attachments/1336759214378582066/1539262263893037086/Gemini_Generated_Image_97gvdg97gvdg97gv.jfif?ex=6a8af331&is=6a89a1b1&hm=d057e94d76fb45c269c7262846cd27c363f1b88d8868586b0aa01121d28e2933"

TICKET_CATEGORY_ID = 1538994815902154852
TICKET_PANEL_CHANNEL_ID = 1540797737438810172

rated_users = set()

SENSITIVE_WORDS = {
    "متوفر": "مـتـوفــر", "متوفره": "مـتـوفــرة", "متوفرة": "مـتـوفــرة", "توفر": "تـو_فُـر",
    "حسابات": "حـس_ابـات", "حساب": "حـس_اب", "ايميل": "ايـم___يل", "إيميل": "إيـم___يل",
    "ايميلات": "ايـم_يــلات", "إيميلات": "إيـم_يــلات", "جيميل": "جـيـمــيل", "gmail": "g_m_a_i_l",
    "نيترو": "نـيـتـــرو", "نايترو": "نـايـتـــرو", "nitro": "n_i_t_r_o", "بوت": "بـو_ت",
    "توكن": "تـوكــن", "token": "t_o_k_e_n", "بيع": "بـيـــع", "شراء": "شــــراء",
    "سعر": "سـعـــر", "اسعار": "أسـعـــار", "أسعار": "أسـعـــار", "ثمن": "ثـمــــن",
    "رخيص": "ر_خـيـص", "متجر": "مـت-جـــر", "عروضكم": "عـرو_ضـكم", "عروض": "عـرُو_ض",
    "عرض": "عَـرْ_ض", "طلب": "طـلـــب", "طلبات": "طـلــبات", "تسليم": "ت-س-ل-يــم",
    "ضمان": "ضـمـــان", "وسيط": "وسـيـــط", "كريديت": "كـرِيـدِيـت", "كريديتات": "كـري-ديــتات",
    "كرديت": "كـرديــت", "كردت": "كـر_دت", "بروبوت": "بـروبـوت", "probot": "p_r_o_b_o_t",
    "بايبال": "بـايـبــال", "paypal": "p_a_y_p_a_l", "رصيد": "ر_صـيـد", "فلوس": "فـلــوس",
    "مبلغ": "مـبـلـــغ", "تحويل": "ت-ح-ويــل", "كاش": "كــاش", "درهم": "در_هـم",
    "دولار": "دو_لار", "خاص": "خ_اص", "الخاص": "الـخ_اص", "خاصك": "خـاصـك",
    "دي ام": "دي_ام", "dm": "d_m", "خاصي": "خ_اصي", "تواصل": "ت-واصــل",
    "واتساب": "واتسـاب", "تيليجرام": "تيليـجرام", "telegram": "t_e_l_e_g_ر_a_m"
}

def get_store_credit(user_id):
    return store_credits.get(user_id, 0)

def update_store_credit(user_id, amount):
    current = get_store_credit(user_id)
    store_credits[user_id] = current + amount

def parse_time(time_str):
    time_str = time_str.lower().strip()
    try:
        if time_str.endswith('s'):
            return int(time_str[:-1])
        elif time_str.endswith('m'):
            return int(time_str[:-1]) * 60
        elif time_str.endswith('h'):
            return int(time_str[:-1]) * 3600
        else:
            return int(time_str) * 60
    except ValueError:
        return None

def parse_amount(amount_str):
    amount_str = amount_str.lower().replace(',', '').strip()
    try:
        if amount_str.endswith('k'):
            return int(float(amount_str[:-1]) * 1000)
        elif amount_str.endswith('m'):
            return int(float(amount_str[:-1]) * 1000000)
        else:
            return int(float(amount_str))
    except ValueError:
        return None

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print('Bot is ready with full features and strict point controls!')

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
                "👉 اضغط الزر أدناه للانتقال المباشر للقناة المخصصة.\n\n"
                "نتمنى لك وقتاً ممتعاً معنا!"
            ),
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Made with ❤️ by kaizencredits")
        
        await member.send(embed=embed, view=WelcomeView())
    except Exception as e:
        print(f"Could not send welcome DM to {member}: {e}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if isinstance(message.channel, discord.DMChannel) and not message.content.startswith("$"):
        for admin_id in ADMIN_IDS:
            try:
                admin_user = await bot.fetch_user(admin_id)
                if admin_user:
                    embed = discord.Embed(
                        title="📩 رسالة جديدة في خاص البوت (DM)",
                        description=f"👤 **من العضو:** {message.author.mention} (`{message.author.id}`)\n\n💬 **النص:**\n{message.content}",
                        color=discord.Color.blurple()
                    )
                    await admin_user.send(embed=embed)
            except Exception as e:
                print(f"Error: {e}")

    if message.guild and not message.content.startswith("$"):
        content_lower = message.content.lower()
        if any(w in content_lower for w in ["كيف اصنع", "كيف أنشئ", "كيف اسوي", "صنع ايميل", "طريقة صنع", "كيفاش نسوي"]):
            await message.reply(f"أهلاً بك يا بطل! 🌟 طريقتنا سهلة، زُر الروم المخصص هنا:\n👉 <#{WELCOME_CHANNEL_ID}>")
            return

    if not message.content.startswith("$") and message.guild:
        content = message.content
        contains_sensitive = False
        for word, replacement in SENSITIVE_WORDS.items():
            if word in content.lower():
                content = content.replace(word, replacement)
                contains_sensitive = True

        if contains_sensitive:
            try:
                await message.delete()
            except:
                pass
            try:
                dm_embed = discord.Embed(
                    title="⚠️ تنبيه أمني: تم حذف رسالتك",
                    description=f"مرحباً يا {message.author.mention}, تم حذف رسالتك لتفادي البلاغات.",
                    color=discord.Color.orange()
                )
                await message.author.send(embed=dm_embed)
                await message.author.send(f"```{content}```")
            except:
                pass
            return

    await bot.process_commands(message)

# ================= 📢 أمر البرودكاست =================
@bot.command(name="massdm", aliases=["broadcast", "dmall"], help="(للإدارة) لإرسال رسالة للأعضاء المتصلين فقط.")
async def massdm(ctx, *, message_content: str):
    if ctx.author.id not in ADMIN_IDS:
        return await ctx.send("❌ عذراً، هذا الأمر مخصص للإدارة فقط!")

    try:
        await ctx.message.delete()
    except:
        pass

    guild = ctx.guild
    active_members = [
        m for m in guild.members 
        if not m.bot and m.status != discord.Status.offline
    ]

    if not active_members:
        return await ctx.send("⚠️ حالياً لا يوجد أي عضو متصل (Online) في السيرفر!", delete_after=10)

    total = len(active_members)
    status_msg = await ctx.send(f"⏳ جاري بدء الإرسال للأعضاء المتصلين... (0/{total})")

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
            
        except discord.Forbidden:
            fail_count += 1
        except Exception:
            fail_count += 1

        if i % 2 == 0 or i == total:
            percent = int((i / total) * 100)
            filled_blocks = int(percent / 10)
            bar = "🟩" * filled_blocks + "⬛" * (10 - filled_blocks)
            
            progress_text = (
                f"🚀 **جاري الإرسال للأعضاء المتصلين...**\n"
                f"[{bar}] `{percent}%`\n"
                f"📊 المنجز: `{i}` من `{total}`\n"
                f"✅ نجاح: `{success_count}` | ❌ فشل: `{fail_count}`"
            )
            try:
                await status_msg.edit(content=progress_text)
            except:
                pass

        delay = random.uniform(6.0, 12.0)
        if i < total:
            await asyncio.sleep(delay)

    final_embed = discord.Embed(
        title="📊 تقرير البرودكاست للأعضاء المتصلين",
        description=(
            f"✅ **تم بنجاح:** `{success_count}` عضو\n"
            f"❌ **فشل (خاص مغلق):** `{fail_count}` عضو\n"
            f"👥 **المجموع المستهدف (Online):** `{total}` عضو"
        ),
        color=discord.Color.green() if success_count > 0 else discord.Color.red()
    )
    
    await status_msg.edit(content=None, embed=final_embed)

# ================= 🎟️ الأمر المختصر ($f @member) - خاص بالمالك فقط =================
@bot.command(name="f", aliases=["finish"], help="(للمالك فقط) لإنهاء التكت وإضافة 1.5 مليون نقطة للزبون.")
async def quick_ticket(ctx, member: discord.Member):
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ عذراً، هذا الأمر مخصص لمالك السيرفر (Owner) فقط!", delete_after=10)

    reward_amount = 1500000  # 1.5 مليون نقطة هدية
    update_store_credit(member.id, reward_amount)

    try:
        await ctx.message.delete()
    except:
        pass

    logs_channel = bot.get_channel(LOGS_CHANNEL_ID)
    if logs_channel:
        embed = discord.Embed(
            title="🎯 إنجاز صفقة تكت جديدة وتسليم الهدية",
            description=(
                f"👤 **الزبون:** {member.mention} (`{member.id}`)\n"
                f"🛠️ **الإداري المشرف:** {ctx.author.mention}\n"
                f"🏛️ **التكت:** {ctx.channel.name}\n\n"
                f"🎁 **الهدية المضافة:** `1,500,000` نقطة (استرداد نقدي Cashback)\n"
                f"💎 **إجمالي رصيد العضو الحالي:** `{get_store_credit(member.id):,}` نقطة"
            ),
            color=discord.Color.green()
        )
        embed.set_footer(text="Email Factory - Auto Rewards System")
        await logs_channel.send(embed=embed)
        if DIVIDER_IMAGE_URL:
            await logs_channel.send(DIVIDER_IMAGE_URL)

    await ctx.send(f"✅ تم إنهاء التكت، إضافة **1,500,000 نقطة** لـ {member.mention} بنجاح!", delete_after=10)
    
    try:
        dm_embed = discord.Embed(
            title="🎉 مبروك لشراء إيميلك!",
            description=(
                f"شكراً لتعاملك معنا في سيرفر **{ctx.guild.name}**!\n"
                f"تمت إضافة **1,500,000 نقطة** إلى رصيدك كهدية ولاء (Cashback).\n"
                f"يمكنك تفقد رصيدك دائماً عبر أمر: `$points`"
            ),
            color=discord.Color.gold()
        )
        await member.send(embed=dm_embed)
    except:
        pass

# ================= 📖 قائمة أوامر (Strat Menu المحدثة) =================
@bot.command(name="setstrat", aliases=["strat", "helpmenu"], help="لعرض واجهة شرح أوامر المتجر والأعضاء.")
async def setstrat(ctx):
    try:
        await ctx.message.delete()
    except:
        pass

    embed = discord.Embed(
        title="✨ دليل استخدام أوامر بوت المتجر",
        description=(
            "مرحباً بك أيها العضو الكريم في متجرنا! 🛒\n"
            "هذه قائمة شاملة بجميع الأوامر المتاحة لك:\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
        ),
        color=discord.Color.gold()
    )

    embed.add_field(
        name="💎 نظام النقاط والرصيد",
        value=(
            "🔹 `$points` (أو `$balance`)\n"
            "   └ **لعرض رصيدك الحالي من النقاط وما يعادلها بالبروبوت.**\n"
            "🔹 `$transfer [@العضو] [المبلغ]` (أو `$pay`)\n"
            "   └ ** لتحويل النقاط الخاصة بك لأي عضو آخر بكل سهولة.**\n"
            "🔹 `$withdraw [المبلغ]`\n"
            "   └ **لطلب سحب نقاطك وتحويلها إلى كريديت بروبوت.**"
        ),
        inline=False
    )

    embed.add_field(
        name="🧾 الحسابات والماليات",
        value=(
            "🔹 `$tax [المبلغ]`\n"
            "   └ **لحساب نسبة الضريبة وضريبة الوسيط بدقة متناهية.**"
        ),
        inline=False
    )

    embed.set_footer(
        text="نتمنى لك تجربة ممتعة وآمنة في متجرنا 🛡️", 
        icon_url=ctx.guild.icon.url if ctx.guild.icon else None
    )

    await ctx.send(embed=embed)
    if DIVIDER_IMAGE_URL:
        await ctx.send(DIVIDER_IMAGE_URL)

# ================= 🛠️ أوامر الإدارة الباقية =================
@bot.command(name="say", help="لجعل البوت يرسل رسالة رسمية.")
async def say(ctx, *, text: str):
    if ctx.author.id not in ADMIN_IDS: return await ctx.send("❌ للإدارة فقط!")
    try: await ctx.message.delete()
    except: pass
    await ctx.send(text)

@bot.command(name="come", help="لاستدعاء عضو معين.")
async def come(ctx, member: discord.Member, *, reason: str = "بدون سبب"):
    if ctx.author.id not in ADMIN_IDS: 
        return await ctx.send("❌ للإدارة فقط!")
    
    try:
        await ctx.message.delete()
    except:
        pass

    embed = discord.Embed(
        title="🚨 استدعاء إداري عاجل",
        description=(
            f"مرحباً {member.mention},\n"
            f"لقد تم استدعاؤك من طرف إدارة السيرفر في الروم: {ctx.channel.mention}\n\n"
            f"📌 **السبب:** {reason}\n"
            f"🛡️ **السيرفر:** {ctx.guild.name}"
        ),
        color=discord.Color.red()
    )
    embed.set_footer(text="يرجى الاستجابة الفورية لتفادي العقوبات.")
    
    try:
        await member.send(embed=embed)
        sent_msg = await ctx.send(f"✅ تم إرسال استدعاء رسمي إلى {member.mention} بنجاح!")
        await asyncio.sleep(10)
        await sent_msg.delete()
    except:
        sent_msg = await ctx.send(f"❌ عذراً، خاص العضو {member.mention} مغلق!")
        await asyncio.sleep(10)
        await sent_msg.delete()

@bot.command(name="serverinfo", aliases=["sinfo"], help="لعرض معلومات وتفاصيل سيرفر المتجر.")
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=f"📊 معلومات سيرفر: {guild.name}", color=discord.Color.blue())
    owners_mentions = [f"<@{admin_id}>" for admin_id in ADMIN_IDS]
    owners_str = ", ".join(owners_mentions) if owners_mentions else str(guild.owner)

    embed.add_field(name="👑 صناع السيرفر", value=owners_str, inline=False)
    embed.add_field(name="👥 عدد الأعضاء", value=guild.member_count, inline=True)
    embed.add_field(name="📅 تاريخ الإنشاء", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
    await ctx.send(embed=embed)

@bot.command(name="list", aliases=["commands", "cmds"], help="لعرض جميع أوامر البوت.")
async def custom_list(ctx):
    if ctx.author.id not in ADMIN_IDS: return await ctx.send("❌ للإدارة فقط!")
    commands_list = [f"📌 `${c.name}`\n    └ الوصف: {c.help or 'لا يوجد وصف'}" for c in bot.commands if not c.hidden]
    embed = discord.Embed(title="📋 لائحة أوامر البوت الشاملة", description="هذه قائمة بجميع الأوامر النشطة حالياً:\n\n" + "\n\n".join(commands_list), color=discord.Color.dark_gold())
    try:
        await ctx.author.send(embed=embed)
        await ctx.send("✅ تم إرسال لائحة الأوامر إلى رسائلك الخاصة (DM)! 📬", delete_after=10)
    except discord.Forbidden:
        await ctx.send("❌ يرجى فتح الخاص (DMs).", delete_after=10)

# ================= 💰 نظام النقاط، التحويل، والسحب =================
@bot.command(name="points", aliases=["pts", "credit", "balance"], help="لعرض رصيدك من نقاط المتجر.")
async def points(ctx, member: discord.Member = None):
    target = member if member else ctx.author
    bal = get_store_credit(target.id)
    probot_value = bal / EXCHANGE_RATE
    embed = discord.Embed(
        title="💎 رصيد نقاط المتجر",
        description=f"العضو: {target.mention}\n🔹 رصيدك: **{bal:,} نقطة**\n🔸 تعادل بالبروبوت: **{probot_value:,.1f}**",
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)

@bot.command(name="transfer", aliases=["pay", "give"], help="لتسهيل تحويل النقاط لعضو آخر.")
async def transfer(ctx, member: discord.Member, amount_str: str):
    amount = parse_amount(amount_str)
    if amount is None or amount <= 0:
        return await ctx.send("❌ يرجى تحديد مبلغ صحيح لتحويله!", delete_after=10)

    if member.id == ctx.author.id:
        return await ctx.send("❌ لا يمكنك تحويل النقاط لنفسك!", delete_after=10)

    if member.bot:
        return await ctx.send("❌ لا يمكنك تحويل النقاط لبوت!", delete_after=10)

    sender_bal = get_store_credit(ctx.author.id)
    if sender_bal < amount:
        return await ctx.send(f"❌ عذراً، رصيدك غير كافٍ لإتمام عملية التحويل! رصيدك الحالي: `{sender_bal:,}` نقطة.", delete_after=10)

    # خصم الرقم من حساب المرسل وإضافته للمستلم بدقة
    update_store_credit(ctx.author.id, -amount)
    update_store_credit(member.id, amount)

    try:
        await ctx.message.delete()
    except:
        pass

    embed = discord.Embed(
        title="💸 عملية تحويل ناجحة",
        description=(
            f"👤 **المحول:** {ctx.author.mention}\n"
            f"🎯 **المستلم:** {member.mention}\n"
            f"💎 **المبلغ المحول:** `{amount:,}` نقطة\n"
            f"📉 **رصيدك الحالي بعد الخصم:** `{get_store_credit(ctx.author.id):,}` نقطة"
        ),
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command(name="addpoints", help="(خاص بالمالك فقط) لإضافة نقاط للزبون.")
async def addpoints(ctx, member: discord.Member, amount: int):
    if ctx.author.id != OWNER_ID: 
        return await ctx.send("❌ عذراً، هذا الأمر مخصص لمالك السيرفر (Owner) فقط!", delete_after=10)
    
    update_store_credit(member.id, amount)
    await ctx.send(f"✅ تمت إضافة `{amount:,}` نقطة لـ {member.mention}")

@bot.command(name="removepoints", help="(خاص بالمالك فقط) لخصم النقاط من العضو.")
async def removepoints(ctx, member: discord.Member, amount: int):
    if ctx.author.id != OWNER_ID: 
        return await ctx.send("❌ عذراً، هذا الأمر مخصص لمالك السيرفر (Owner) فقط!", delete_after=10)
    
    update_store_credit(member.id, -amount)
    await ctx.send(f"✅ تم خصم `{amount:,}` نقطة من {member.mention}")

@bot.command(name="tax", help="لحساب نسبة الضريبة وضريبة الوسيط.")
async def tax(ctx, amount: str):
    parsed = parse_amount(amount)
    if parsed is None or parsed < 0: return await ctx.send("❌ الرقم غير صحيح.")
    
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
            f"🤝 **ضريبة الوسيط الرسمية:**\n"
            f"• المبلغ المطلوب تحويله للوسيط: `{mediator_tax_amount:,}`"
        ),
        color=discord.Color.pink()
    )
    await ctx.send(embed=embed)

@bot.command(name="profit", help="لحساب صافي الربح.")
async def profit(ctx, price: int, cost: int):
    p = price - cost
    await ctx.send(embed=discord.Embed(title="📈 حساب الأرباح", description=f"💰 صافي الربح: `{p:,}`", color=discord.Color.green()))

@bot.command(name="withdraw", help="لطلب سحب الأرباح والنقاط.")
async def withdraw(ctx, amount_str: str):
    amount = parse_amount(amount_str)
    if amount is None or amount <= 0:
        return await ctx.send("❌ يرجى تحديد مبلغ صحيح للسحب!", delete_after=10)

    user_bal = get_store_credit(ctx.author.id)
    if user_bal < amount:
        return await ctx.send(f"❌ عذراً، رصيدك غير كافٍ! رصيدك: `{user_bal:,}` نقطة.", delete_after=10)

    update_store_credit(ctx.author.id, -amount)
    credit_to_transfer = amount / EXCHANGE_RATE

    try:
        await ctx.message.delete()
    except:
        pass

    for admin_id in ADMIN_IDS:
        try:
            admin_user = await bot.fetch_user(admin_id)
            if admin_user:
                embed = discord.Embed(
                    title="📥 طلب سحب كريديت جديد",
                    description=(
                        f"👤 **العضو:** {ctx.author.mention} (`{ctx.author.id}`)\n"
                        f"📉 **النقاط المسحوبة:** `{amount:,}` نقطة\n"
                        f"💲 **الكريديت الواجب تحويله:** `{credit_to_transfer:,.1f}`\n\n"
                        f"🛠️ **الأمر الجاهز للبروبوت:**\n"
                        f"```c {ctx.author.id} {int(credit_to_transfer)}```"
                    ),
                    color=discord.Color.green()
                )
                await admin_user.send(embed=embed)
        except Exception as e:
            print(f"Error: {e}")

    await ctx.send(f"✅ تم تقديم طلب السحب بنجاح وخصمه من رصيدك!", delete_after=10)

# ================= 🎮 الألعاب التفاعلية =================
@bot.command(name="games", aliases=["play"], help="لعرض قائمة الألعاب.")
async def games_list(ctx):
    embed = discord.Embed(title="🎮 قائمة ألعاب المتجر", description="🔹 `$xo @العضو` - تحدي X-O\n🔹 `$roulette` - روليت السيرفر\n🔹 `$rps [حجرة/ورقة/مقص]` - حجرة ورقة مقص", color=discord.Color.blurple())
    await ctx.send(embed=embed)

class TicTacToeButton(discord.ui.Button):
    def __init__(self, x, y):
        super().__init__(style=discord.ButtonStyle.secondary, label="‎", row=x)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        view: TicTacToeView = self.view
        if interaction.user != view.current_player:
            return await interaction.response.send_message("❌ ليس دورك الآن!", ephemeral=True)
        if view.board[self.x][self.y] != 0:
            return await interaction.response.send_message("❌ الخانة ممتلئة!", ephemeral=True)

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
                embed = discord.Embed(title="🎮 X-O", description=f"🎉 الفائز {view.playerX.mention}!", color=discord.Color.green())
            elif winner == -1:
                embed = discord.Embed(title="🎮 X-O", description=f"🎉 الفائز {view.playerO.mention}!", color=discord.Color.green())
            else:
                embed = discord.Embed(title="🎮 X-O", description="🤝 تعادل!", color=discord.Color.orange())
            
            for child in view.children: child.disabled = True
            await interaction.response.edit_message(embed=embed, view=view)
            view.stop()
            return

        embed = discord.Embed(title="🎮 X-O", description=f"دور: {view.current_player.mention}", color=discord.Color.blue())
        await interaction.response.edit_message(embed=embed, view=view)

class TicTacToeView(discord.ui.View):
    def __init__(self, playerX, playerO):
        super().__init__()
        self.playerX = playerX
        self.playerO = playerO
        self.current_player = playerX
        self.board = [[0, 0, 0] for _ in range(3)]
        for x in range(3):
            for y in range(3): self.add_item(TicTacToeButton(x, y))

    def check_winner(self):
        for row in self.board:
            if row[0] == row[1] == row[2] != 0: return row[0]
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] != 0: return self.board[0][col]
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != 0: return self.board[0][0]
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != 0: return self.board[0][2]
        if all(self.board[r][c] != 0 for r in range(3) for c in range(3)): return 0
        return None

@bot.command(name="xo", help="تحدي X-O.")
async def xo(ctx, member: discord.Member):
    if member == ctx.author or member.bot: return await ctx.send("❌ لا يمكنك اللعب لوحدك!")
    view = TicTacToeView(ctx.author, member)
    embed = discord.Embed(title="🎮 X-O", description=f"تحدٍّ بين {ctx.author.mention} و {member.mention}", color=discord.Color.blue())
    await ctx.send(embed=embed, view=view)

@bot.command(name="roulette", help="روليت السيرفر.")
async def roulette(ctx):
    class RouletteJoinView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            self.players = set()
        @discord.ui.button(label="🟢 انضمام", style=discord.ButtonStyle.green)
        async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.players.add(interaction.user)
            await interaction.response.send_message("✅ تم انضمامك!", ephemeral=True)

    embed = discord.Embed(title="🎲 روليت", description="⏳ 60 ثانية للانضمام عبر الزر أدناه!", color=discord.Color.gold())
    view = RouletteJoinView()
    msg = await ctx.send(embed=embed, view=view)
    await asyncio.sleep(60)
    for child in view.children: child.disabled = True
    if not view.players: return await msg.edit(content="❌ انتهى الوقت ولم يشارك أحد!", embed=None, view=view)
    winner = random.choice(list(view.players))
    await msg.edit(content=f"🎉 الفائز هو: {winner.mention}!", view=view)

@bot.command(name="rps", help="حجرة ورقة مقص.")
async def rps(ctx, choice: str):
    choices = ["حجرة", "ورقة", "مقص"]
    choice = choice.lower().strip()
    if choice not in choices: return await ctx.send("❌ اختر: حجرة، ورقة، مقص")
    bot_choice = random.choice(choices)
    if choice == bot_choice: result = "🤝 تعادل!"
    elif (choice == "حجرة" and bot_choice == "مقص") or (choice == "ورقة" and bot_choice == "حجرة") or (choice == "مقص" and bot_choice == "ورقة"):
        result = "🎉 فزت!"
    else: result = "🤖 خسرت!"
    await ctx.send(embed=discord.Embed(title="✂️ حجرة ورقة مقص", description=f"اختيارك: {choice}\nاختيار البوت: {bot_choice}\n\n**{result}**", color=discord.Color.purple()))

# ================= 📋 اقتراحات وبلاغات =================
@bot.command(name="suggest", help="لإرسال اقتراح.")
async def suggest(ctx, *, suggestion: str):
    try: await ctx.message.delete()
    except: pass
    ch = bot.get_channel(FEEDBACK_CHANNEL_ID)
    embed = discord.Embed(title="💡 اقتراح جديد", description=suggestion, color=discord.Color.blue())
    if ch:
        msg = await ch.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
        if DIVIDER_IMAGE_URL: await ch.send(DIVIDER_IMAGE_URL)
    await ctx.send("✅ تم إرسال اقتراحك!", delete_after=10)

@bot.command(name="report", help="لإرسال بلاغ.")
async def report_cmd(ctx, *, reason: str):
    try: await ctx.message.delete()
    except: pass
    ch = bot.get_channel(REPORTS_CHANNEL_ID)
    embed = discord.Embed(title="🚨 بلاغ جديد", description=reason, color=discord.Color.red())
    if ch:
        await ch.send(embed=embed)
        if DIVIDER_IMAGE_URL: await ch.send(DIVIDER_IMAGE_URL)
    await ctx.send("✅ تم إرسال بلاغك!", delete_after=10)

@bot.command(name="remind", help="تذكير شخصي.")
async def remind(ctx, time_str: str, *, reminder: str):
    seconds = parse_time(time_str)
    if not seconds: return await ctx.send("❌ صيغة الوقت خاطئة.")
    await ctx.send(f"✅ تذكير بعد `{time_str}`.")
    await asyncio.sleep(seconds)
    try: await ctx.author.send(f"⏰ تذكير: {reminder}")
    except: pass

# ================= ⭐ نظام التقييم =================
class RatingView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id

    async def handle_rating(self, interaction: discord.Interaction, stars: str):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ ليست مخصصة لك!", ephemeral=True)
        if interaction.user.id in rated_users:
            return await interaction.response.send_message("❌ قيّمت مسبقاً!", ephemeral=True)

        rated_users.add(interaction.user.id)
        ch = bot.get_channel(FEEDBACK_CHANNEL_ID)
        embed = discord.Embed(title="⭐ تقييم جديد", description=f"👤 **العميل:** {interaction.user.mention}\n⭐ **التقييم:** {stars}", color=discord.Color.gold())
        if ch:
            await ch.send(embed=embed)
            if DIVIDER_IMAGE_URL: await ch.send(DIVIDER_IMAGE_URL)
        for child in self.children: child.disabled = True
        await interaction.response.edit_message(content="❤️ شكراً لتقييمك!", view=self)

    @discord.ui.button(label="⭐ 1", style=discord.ButtonStyle.danger)
    async def s1(self, i: discord.Interaction, b: discord.ui.Button): await self.handle_rating(i, "⭐ (1/5)")
    @discord.ui.button(label="⭐ 2", style=discord.ButtonStyle.secondary)
    async def s2(self, i: discord.Interaction, b: discord.ui.Button): await self.handle_rating(i, "⭐⭐ (2/5)")
    @discord.ui.button(label="⭐ 3", style=discord.ButtonStyle.primary)
    async def s3(self, i: discord.Interaction, b: discord.ui.Button): await self.handle_rating(i, "⭐⭐⭐ (3/5)")
    @discord.ui.button(label="⭐ 4", style=discord.ButtonStyle.success)
    async def s4(self, i: discord.Interaction, b: discord.ui.Button): await self.handle_rating(i, "⭐⭐⭐⭐ (4/5)")
    @discord.ui.button(label="⭐ 5", style=discord.ButtonStyle.success)
    async def s5(self, i: discord.Interaction, b: discord.ui.Button): await self.handle_rating(i, "⭐⭐⭐⭐⭐ (5/5)")

@bot.command(name="rate", help="إرسال تقييم للزبون.")
async def rate(ctx, member: discord.Member):
    if ctx.author.id not in ADMIN_IDS: return await ctx.send("❌ للإدارة فقط!")
    if member.id in rated_users: return await ctx.send("❌ قيّمت مسبقاً!")
    try:
        await member.send(embed=discord.Embed(title="⭐ تقييم الخدمة", description="قيّم تجربتك معنا:", color=discord.Color.gold()), view=RatingView(member.id))
        await ctx.send(f"✅ تم إرسال أزرار التقييم لـ {member.mention}", delete_after=10)
    except:
        await ctx.send("❌ خاص العضو مغلق!", delete_after=10)

try:
    bot.run(os.environ.get("DISCORD_TOKEN"))
except Exception as e:
    print("\n[!] خطأ:")
    traceback.print_exc()
    input("\nاضغط Enter للإغلاق...")