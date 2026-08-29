import discord
from discord.ext import commands
import asyncio
import random
import datetime
import os

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

email_stock = []  # مخزن الإيمايلات

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("Bot is ready and online for hosting!")

# تحقق من أن المستخدم هو المسؤول الوحيد
def is_owner():
    def predicate(ctx):
        return ctx.author.id == OWNER_ID
    return commands.check(predicate)

# --- أوامر الإدارة والمخزن ---
@bot.command(name="add")
@is_owner()
async def add_emails(ctx, *, emails: str):
    count = 0
    for em in emails.split():
        email_stock.append(em)
        count += 1
    await ctx.send(f"✅ تمت إضافة {count} إيمايل للمخزن بنجاح.")

@bot.command(name="stock")
@is_owner()
async def view_stock(ctx):
    await ctx.send(f"📦 عدد الإيمايلات المتبقية في المخزن: **{len(email_stock)}**")

@bot.command(name="reset")
@is_owner()
async def reset_stock(ctx):
    email_stock.clear()
    await ctx.send("🔄 تم إعادة تعيين وتفريغ المخزن بنجاح.")

@bot.command(name="paybot")
async def paybot(ctx, member: discord.Member, amount: int):
    tax_amount = int(amount / 0.95) + 1
    await ctx.send(f"c {member.mention} {tax_amount}")

# --- نظام التقييم التلقائي ---
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

# --- بانل فتح التذاكر ---
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
        
        embed = discord.Embed(title="اختر الكمية المطلوبة", description="يرجى اختيار عدد الإيمايلات (1, 5, 10, 15):", color=discord.Color.blurple())
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
            await interaction.response.send_message("❌ عذراً، الإيمايلات في المخزن لا تكفي.", ephemeral=True)
            return
        
        french_names = ["jean", "pierre", "luc", "marie", "sophie", "thomas", "camille", "antoine", "nicolas", "julien"]
        mock_email = f"{random.choice(french_names)}{random.randint(100,999)}@gmail.com"
        
        embed = discord.Embed(title=f"تفاصيل الحساب (الكمية: {qty})", color=discord.Color.green())
        embed.add_field(name="البريد الإلكتروني", value=f"`{mock_email}`", inline=False)
        embed.add_field(name="كلمة المرور", value="`1122mhdg`", inline=False)
        embed.add_field(name="عمر الحساب", value="1/1/1999", inline=False)
        embed.set_footer(text="أمامك 15 دقيقة للصنع.")

        view = AccountActionsView(mock_email, qty, self.payment_method)
        await interaction.response.edit_message(embed=embed, view=view)

class AccountActionsView(discord.ui.View):
    def __init__(self, email, qty, payment_method):
        super().__init__(timeout=900)
        self.email = email
        self.qty = qty
        self.payment_method = payment_method

    @discord.ui.button(label="تم الصنع", style=discord.ButtonStyle.success)
    async def done_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        exists = True
        if not exists:
            await interaction.response.send_message("❌ أنك ما صنعتي والو!", ephemeral=True)
            return

        delivery_ch = interaction.guild.get_channel(DELIVERY_CHANNEL_ID)
        if delivery_ch:
            await delivery_ch.send(f"📦 تم تسليم الإيمايل: `{self.email}` | بواسطة العضو {interaction.user.mention} في روم <#{interaction.channel.id}>")

        try:
            await interaction.channel.edit(name=f"{self.qty}-{self.payment_method}")
        except Exception:
            pass

        embed = discord.Embed(title="تم بنجاح!", description="هل تبغي تكمل تصنع أو تنتظر تتسلم على الإيمايل؟", color=discord.Color.gold())
        view = PostCreationView(self.email)
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
    def __init__(self, email):
        super().__init__(timeout=None)
        self.email = email

    @discord.ui.button(label="إكمال الصنع", style=discord.ButtonStyle.success)
    async def continue_making(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔄 جاري إعداد إيمايل جديد...", ephemeral=True)

    @discord.ui.button(label="انتظار التسليم", style=discord.UI.Button, style=discord.ButtonStyle.primary) # تم تعديلها للتأكيد
    async def wait_delivery(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⏳ تم تفعيل وضع الانتظار. لا يمكنك طلب إيمايل جديد حتى الاستلام.", ephemeral=True)

class CancelChoiceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="صنع المزيد", style=discord.ButtonStyle.primary)
    async def more(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="اختر طريقة الدفع", description="يرجى اختيار طريقة الدفع:", color=discord.Color.blurple())
        await interaction.response.edit_message(embed=embed, view=PaymentSelectView())

    @discord.ui.button(label="قفل التكت", style=discord.ButtonStyle.danger)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        log_ch = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log_ch:
            await log_ch.send(f"📁 تم إغلاق تذكرة بواسطة {interaction.user.mention} (الروم: {interaction.channel.name})")
        await interaction.channel.delete()

# تشغيل البوت باستخدام متغير البيئة للاستضافة الآمنة
bot.run(os.getenv("DISCORD_TOKEN"))
