"""
===========================================
  AVIATOR SIGNAL BOT - Telegram
  Autor: Void Partners
===========================================
Dependências: pip install python-telegram-bot schedule requests python-dotenv pytz
"""

import os
import asyncio
import schedule
import time
import random
import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

load_dotenv()

# ─── CONFIG ───────────────────────────────────────────────────────────────────
BOT_TOKEN  = os.getenv("BOT_TOKEN", "SEU_TOKEN_AQUI")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@seu_canal")
ADMIN_IDS  = [int(x) for x in os.getenv("ADMIN_IDS", "0").split(",")]
LINK_CASA  = os.getenv("LINK_CASA", "https://seu-link-afiliado.com")

TZ = ZoneInfo("Europe/Lisbon")  # Horário de Portugal

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def hora_portugal():
    return datetime.now(TZ)

def gerar_sinal():
    multiplicador = round(random.uniform(1.5, 4.5), 2)
    if random.random() < 0.05:
        multiplicador = round(random.uniform(5.0, 15.0), 2)

    # Horário de entrada = agora + 1 a 2 min (em Portugal)
    horario = hora_portugal() + timedelta(minutes=random.randint(1, 2))
    horario_str = horario.strftime("%H:%M")

    niveis = ["🟡 Médio", "🟢 Alto", "🟢 Alto", "🟢 Alto"]
    confianca = random.choice(niveis)

    return {
        "multiplicador": multiplicador,
        "horario": horario_str,
        "confianca": confianca,
    }

def formatar_sinal(sinal: dict) -> str:
    mult = sinal["multiplicador"]
    emoji = "🚀" if mult >= 5 else "✈️"

    return (
        f"👀 Nossa IA identificou um padrão...\n"
        f"\n"
        f"{emoji} *Meta:* `{mult}x`\n"
        f"⏰ *Janela de entrada:* `{sinal['horario']}`\n"
        f"📊 *Confiança:* {sinal['confianca']}\n"
        f"\n"
        f"Essa é a sua chance. Não perca.\n"
        f"\n"
        f"🔞 _Jogue com responsabilidade._"
    )

def formatar_divulgacao() -> str:
    return (
        f"🏦 *CASA RECOMENDADA*\n"
        f"\n"
        f"Jogamos e confiamos nessa plataforma há meses.\n"
        f"\n"
        f"✅ Licenciada e regulamentada\n"
        f"✅ Saque rápido via PIX\n"
        f"✅ Suporte 24h\n"
        f"✅ *Bónus de 100% no 1º depósito*\n"
        f"\n"
        f"👇 Acesse agora e garante o seu bónus:"
    )

# ─── COMANDOS ─────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🎰 Acessar Plataforma", url=LINK_CASA)]]
    await update.message.reply_text(
        "✈️ *BEM-VINDO AO AVIATOR SIGNALS!*\n\n"
        "Recebe os melhores sinais do Aviator em tempo real.\n\n"
        "📌 *Como usar:*\n"
        "1️⃣ Acede à plataforma pelo botão abaixo\n"
        "2️⃣ Aguarda o sinal aparecer aqui\n"
        "3️⃣ Entra na ronda no horário indicado\n"
        "4️⃣ Retira antes do multiplicador ✅\n\n"
        "🟢 *Sinais a cada 3 minutos...*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def sinal_manual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Sem permissão.")
        return
    sinal = gerar_sinal()
    await context.bot.send_message(chat_id=CHANNEL_ID, text=formatar_sinal(sinal), parse_mode="Markdown")
    await update.message.reply_text("✅ Sinal disparado!")

async def divulgar_manual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    keyboard = [[InlineKeyboardButton("🎰 Garantir Bónus de 100%", url=LINK_CASA)]]
    await context.bot.send_message(
        chat_id=CHANNEL_ID,
        text=formatar_divulgacao(),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    await update.message.reply_text("✅ Divulgação enviada!")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    await update.message.reply_text(
        f"🤖 *Status do Bot*\n\n"
        f"✅ Online\n"
        f"📢 Canal: `{CHANNEL_ID}`\n"
        f"🕐 Hora PT: `{hora_portugal().strftime('%d/%m/%Y %H:%M:%S')}`",
        parse_mode="Markdown",
    )

# ─── SCHEDULER ────────────────────────────────────────────────────────────────
bot_instance = None
sinal_count = 0  # Contador para intercalar divulgação

async def job_sinal():
    global sinal_count
    if not bot_instance:
        return
    sinal_count += 1
    sinal = gerar_sinal()
    try:
        await bot_instance.send_message(
            chat_id=CHANNEL_ID,
            text=formatar_sinal(sinal),
            parse_mode="Markdown",
        )
        print(f"[{hora_portugal().strftime('%H:%M:%S')} PT] ✅ Sinal #{sinal_count}: {sinal['multiplicador']}x")
    except Exception as e:
        print(f"[ERRO sinal] {e}")

async def job_divulgacao():
    if not bot_instance:
        return
    keyboard = [[InlineKeyboardButton("🎰 Garantir Bónus de 100%", url=LINK_CASA)]]
    try:
        await bot_instance.send_message(
            chat_id=CHANNEL_ID,
            text=formatar_divulgacao(),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        print(f"[{hora_portugal().strftime('%H:%M:%S')} PT] 📢 Divulgação enviada")
    except Exception as e:
        print(f"[ERRO divulgação] {e}")

def run_scheduler():
    def wrap(coro):
        def fn():
            asyncio.run(coro())
        return fn

    schedule.every(3).minutes.do(wrap(job_sinal))        # Sinal a cada 3 min
    schedule.every(20).minutes.do(wrap(job_divulgacao))  # Divulgação a cada 20 min

    while True:
        schedule.run_pending()
        time.sleep(1)

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    global bot_instance

    print("🚀 Iniciando Aviator Signal Bot...")
    print(f"📢 Canal: {CHANNEL_ID}")
    print(f"🕐 Timezone: Portugal (Europe/Lisbon)")

    app = Application.builder().token(BOT_TOKEN).build()
    bot_instance = app.bot

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("disparar", sinal_manual))
    app.add_handler(CommandHandler("divulgar", divulgar_manual))
    app.add_handler(CommandHandler("status", status))

    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("⏰ Scheduler iniciado — sinais a cada 3min, divulgação a cada 20min")
    print("✅ Bot online!")

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
