import discord
from discord.ext import commands
import asyncio
import random
import datetime
import os
import aiohttp
import re

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="$", intents=intents)

OWNER_ID = 1021501331636244490
CATEGORY_ID = 1539000813794627664
ROLE_15_ID = 1539281206741569546
TUTORIAL_CHANNEL_ID = 1538994818150170714
DELIVERY_CHANNEL_ID = 1538994824584110120
LOG_CHANNEL_ID = 1543347188317298729
LINE_IMAGE_URL = "https://cdn.discordapp.com/attachments/1336759214378582066/1539262263893037086/Gemini_Generated_Image_97gvdg97gvdg97gv.jfif"

email_stock = []  
email_price = 1   

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("Bot is ready and online!")

def is_owner():
    def predicate(ctx):
        return ctx.author.id == OWNER_ID
    return commands.check(predicate)

def parse_number(amount_str: str) -> int:
    amount_str = amount_str.lower().replace(",", "").strip()
    match = re.match(r"^([\d.]+)([kmb]?)$", amount_str)
    if not match:
        return 0
    
    number, suffix = match.groups()
    number = float(number)
    
    if suffix == "k":
        return int(number * 1_000)
    elif suffix == "m":
        return int(number * 1_000_000)
    elif suffix == "b":
        return int(number * 1_000_000_000)
    return int(number)

@bot.command(name="tax", aliases=["t", "paybot"])
async def tax_calc(ctx, amount_str: str):
    amount = parse_number(amount_str)
    if amount <= 0:
        await ctx.send("❌ يرجى إدخال مبلغ صحيح (مثال: `35m` أو `5000`).")
        return
    
    tax_amount = int(amount / 0.95) + 1
    await ctx.send(f"c {ctx.author.mention} {tax_amount}")

@bot.command(name="adminlist")
@is_owner()
async def admin_list(ctx):
    embed = discord.Embed(title="👑 دليل أوامر المسؤول الخاصة بك", color=discord.Color.gold())
    embed.add_field(name="$add [الإيمايلات]", value="إضافة إيمايلات حقيقية للمخزن", inline=False)
    embed.add_field(name="$stock", value="عرض المخزن مع زر التحديث", inline=False)
    embed.add_field(name="$reset", value="تفريغ وإعادة تعيين المخزن", inline=False)
    embed.add_field(name="$setprice [السعر]", value="تحديد سعر الإيمايل بكردت (يدعم 35m)", inline=False)
    embed.add_field(name="$panel", value="إرسال بانل فتح التذاكر", inline=False)
    embed.add_field(name="$delete", value="قفل وحذف التذكرة مع إرسال الترانسكريبت للوج", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="add")
@is_owner()
async def add_emails(ctx, *, emails: str):
    count = 0
    for em in emails.split():
        email_stock.append(em)
        count += 1
    await ctx.send(f"✅ تمت إضافة {count} إيمايل حقيقي للمخزن بنجاح.")

@bot.command(name="setprice")
@is_owner()
async def set_price(ctx, price_str: str):
    global email_price
    price = parse_number(price_str)
    if price <= 0:
        await ctx.send("❌ يرجى تحديد سعر صحيح.")
        return
    email_price = price
    await ctx.send(f"💰 تم تحديث سعر الإيمايل ليصبح: **{email_price:,}** كردت.")

@bot.command(name="stock")
@is_owner()
async def view_stock(ctx):
    embed = discord.Embed(title="📦 مخزن الإيمايلات", description=f"عدد الإيمايلات المتاحة: **{len(email_stock):,}**\nسعر الإيمايل: **{email_price:,}** كردت", color=discord.Color.dark_grey())
    embed.set_image(url=LINE_IMAGE_URL)
    view = StockRefreshView()
    await ctx.send(embed=embed, view=view)

class StockRefreshView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="تحديث", style=discord.ButtonStyle.primary, emoji="🔄")
    async def refresh_stock(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="📦 مخزن الإيمايلات", description=f"عدد الإيمايلات المتاحة: **{len(email_stock):,}**\nسعر الإيمايل: **{email_price:,}** كردت", color=discord.Color.dark_grey())
        embed.set_image(url=LINE_IMAGE_URL)
        await interaction.response.edit_message(embed=embed, view=self)

@bot.command(name="reset")
@is_owner()
async def reset_stock(ctx):
    email_stock.clear()
    await ctx.send("🔄 تم إعادة تعيين وتفريغ المخزن بنجاح.")

# --- أمر حذف وقفل التكت لك وحدك ---
@bot.command(name="delete")
@is_owner()
async def delete_ticket(ctx):
    channel = ctx.channel
    messages_logs = []
    async for msg in channel.history(limit=100, oldest_first=True):
        messages_logs.append(f"[{msg.created_at.strftime('%Y-%m-%d %H:%M')}] {msg.author.name}: {msg.content}")
    
    transcript_text = "\n".join(messages_logs)
    if len(transcript_text) > 1900:
        transcript_text = transcript_text[:1900] + "\n... (تم الاختصار)"

    log_ch = ctx.guild.get_channel(LOG_CHANNEL_ID)
    if log_ch:
        embed = discord.Embed(title=f"📁 ترانسكريبت تذكرة: {channel.name}", description=f"أغلق بواسطة المسؤول: {ctx.author.mention}\n\n**محتوى التذكرة:**\n```text\n{transcript_text}\n```", color=discord.Color.orange())
        await log_ch.send(embed=embed)
        
    await channel.delete()

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if "تقييم" in message.content.lower() or "feedback" in message.channel.name.lower() or "تقيب" in message.channel.name.lower():
        try:
            await message.add_reaction("❤️")
            await message.channel.send(LINE_IMAGE_URL)
        except Exception:
            pass

    await bot.process_commands(message)

@bot.command(name="panel")
@is_owner()
async def ticket_panel(ctx):
    embed = discord.Embed(title="🎫 نظام تذاكر الإيمايلات", description="اضغط على الزر أدناه لفتح تذكرة جديدة واختيار طريقة الدفع.", color=discord.Color.teal())
    view = TicketOpenView()
    await ctx.send(embed=embed, view=view)

class TicketOpenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="فتح تذكرة 🎫", style=discord.ButtonStyle.green)
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        category = guild.get_channel(CATEGORY_ID)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        ticket_channel = await guild.create_text_channel(name=f"ticket-{interaction.user.name}", category=category, overwrites=overwrites)
        
        embed = discord.Embed(title="أهلاً بك في التذكرة", description="يرجى اختيار طريقة الدفع المناسبة لك:\n• روب (Robux)\n• كردت (Credit)\n• دولارات (USD)\n• أدم سي (ADM-C)", color=discord.Color.blue())
        await ticket_channel.send(content=interaction.user.mention, embed=embed, view=PaymentSelectView())
        await interaction.response.send_message(f"✅ تم فتح تذكرتك بنجاح: {ticket_channel.mention}", ephemeral=True)

class PaymentSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="روب", style=discord.ButtonStyle.primary, emoji="🤖")
    async def robux(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_payment(interaction, "robux")

    @discord.ui.button(label="كردت", style=discord.ButtonStyle.success, emoji="💳")
    async def credit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_payment(interaction, "credit")

    @discord.ui.button(label="دولارات", style=discord.ButtonStyle.secondary, emoji="💵")
    async def usd(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_payment(interaction, "usd")

    @discord.ui.button(label="أدم سي", style=discord.ButtonStyle.danger, emoji="⚡")
    async def admc(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_payment(interaction, "admc")

    async def process_payment(self, interaction: discord.Interaction, payment_method: str):
        new_name = f"{interaction.user.name}-{payment_method}".lower()
        await interaction.channel.edit(name=new_name)
        
        embed = discord.Embed(title="اختر الكمية المطلوبة", description=f"السعر الحالي للإيمايل: {email_price:,} كردت\nيرجى اختيار عدد الإيمايلات (1, 5, 10, 15):", color=discord.Color.blurple())
        view = QuantitySelectView(payment_method)
        await interaction.response.edit_message(embed=embed, view=view)

class QuantitySelectView(discord.ui.View):
    def __init__(self, payment_method):
        super().__init__(timeout=None)
        self.payment_method = payment_method

    @discord.ui.button(label="1", style=discord.ButtonStyle.primary)
    async def q1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_quantity(interaction, 1)

    @discord.ui.button(label="5", style=discord.ButtonStyle.primary)
    async def q5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_quantity(interaction, 5)

    @discord.ui.button(label="10", style=discord.ButtonStyle.primary)
    async def q10(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_quantity(interaction, 10)

    @discord.ui.button(label="15 (خاص بالرتبة)", style=discord.ButtonStyle.danger)
    async def q15(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(ROLE_15_ID)
        if (role not in interaction.user.roles) and (interaction.user.id != OWNER_ID):
            await interaction.response.send_message("❌ لست من الرتب المسموح لها باختيار كمية 15!", ephemeral=True)
            return
        await self.handle_quantity(interaction, 15)

    async def handle_quantity(self, interaction: discord.Interaction, qty: int):
        if len(email_stock) < qty:
            await interaction.response.send_message("❌ عذراً، الإيمايلات في المخزن لا تكفي حالياً.", ephemeral=True)
            return
        
        real_email = email_stock.pop(0)
        
        embed = discord.Embed(title=f"تفاصيل الحساب (الكمية: {qty})", color=discord.Color.green())
        embed.add_field(name="البريد الإلكتروني", value=f"`{real_email}`", inline=False)
        embed.add_field(name="كلمة المرور", value="`1122mhdg`", inline=False)
        embed.add_field(name="عمر الحساب", value="1/1/1999", inline=False)
        embed.set_footer(text="أمامك 15 دقيقة للصنع.")

        view = AccountActionsView(real_email, qty, self.payment_method)
        await interaction.response.edit_message(embed=embed, view=view)

class AccountActionsView(discord.ui.View):
    def __init__(self, email, qty, payment_method):
        super().__init__(timeout=900)
        self.email = email
        self.qty = qty
        self.payment_method = payment_method

    @discord.ui.button(label="تم الصنع", style=discord.ButtonStyle.success)
    async def done_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        delivery_ch = interaction.guild.get_channel(DELIVERY_CHANNEL_ID)
        if delivery_ch:
            await delivery_ch.send(f"📦 تم تسليم الإيمايل: `{self.email}` | بواسطة العضو {interaction.user.mention} في روم <#{interaction.channel.id}>")

        try:
            await interaction.channel.edit(name=f"{self.qty}-{self.payment_method}")
        except Exception:
            pass

        embed = discord.Embed(title="تم بنجاح!", description="هل تبغي تكمل تصنع أو تنتظر تتسلم على الإيمايل؟", color=discord.Color.gold())
        view = PostCreationView(self.email, self.payment_method)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="كيفية الصنع", style=discord.ButtonStyle.secondary)
    async def tutorial_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"📌 توجه إلى روم الشرح: <#{TUTORIAL_CHANNEL_ID}>", ephemeral=True)

    @discord.ui.button(label="وقت إضافي (10 د)", style=discord.ButtonStyle.primary)
    async def extra_time(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⏱️ تم إضافة 10 دقائق إضافية.", ephemeral=True)

    @discord.ui.button(label="إلغاء العملية", style=discord.ButtonStyle.danger)
    async def cancel_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        email_stock.append(self.email)
        embed = discord.Embed(title="تم إلغاء العملية وإعادة الإيمايل للمخزن", description="هل تريد صنع المزيد أم قفل التكت؟", color=discord.Color.red())
        view = CancelChoiceView()
        await interaction.response.edit_message(embed=embed, view=view)

class PostCreationView(discord.ui.View):
    def __init__(self, email, payment_method):
        super().__init__(timeout=None)
        self.email = email
        self.payment_method = payment_method

    @discord.ui.button(label="إكمال الصنع", style=discord.ButtonStyle.success)
    async def continue_making(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(email_stock) < 1:
            await interaction.response.send_message("❌ عذراً، مخزن الإيمايلات نفد تماماً!", ephemeral=True)
            return
        
        real_email = email_stock.pop(0)
        embed = discord.Embed(title="تفاصيل الحساب الجديد", color=discord.Color.green())
        embed.add_field(name="البريد الإلكتروني", value=f"`{real_email}`", inline=False)
        embed.add_field(name="كلمة المرور", value="`1122mhdg`", inline=False)
        embed.add_field(name="عمر الحساب", value="1/1/1999", inline=False)
        
        view = AccountActionsView(real_email, 1, self.payment_method)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="انتظار التسليم", style=discord.ButtonStyle.primary)
    async def wait_delivery(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⏳ تم تفعيل وضع الانتظار بنجاح.", ephemeral=True)

class CancelChoiceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="صنع المزيد", style=discord.ButtonStyle.primary)
    async def more(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="اختر طريقة الدفع", description="يرجى اختيار طريقة الدفع:", color=discord.Color.blurple())
        await interaction.response.edit_message(embed=embed, view=PaymentSelectView())

    @discord.ui.button(label="قفل التكت", style=discord.ButtonStyle.danger)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel
        messages_logs = []
        async for msg in channel.history(limit=100, oldest_first=True):
            messages_logs.append(f"[{msg.created_at.strftime('%Y-%m-%d %H:%M')}] {msg.author.name}: {msg.content}")
        
        transcript_text = "\n".join(messages_logs)
        if len(transcript_text) > 1900:
            transcript_text = transcript_text[:1900] + "\n... (تم الاختصار)"

        log_ch = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log_ch:
            embed = discord.Embed(title=f"📁 ترانسكريبت تذكرة: {channel.name}", description=f"أغلق بواسطة: {interaction.user.mention}\n\n**محتوى التذكرة:**\n```text\n{transcript_text}\n```", color=discord.Color.orange())
            await log_ch.send(embed=embed)
            
        await interaction.channel.delete()

bot.run(os.getenv("DISCORD_TOKEN"))
