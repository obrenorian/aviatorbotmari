"""
===========================================
  AVIATOR SIGNAL BOT - Telegram
  Autor: Void Partners
===========================================
Dependências: pip install python-telegram-bot schedule requests python-dotenv
"""

import os
import asyncio
import schedule
import time
import random
import threading
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

# ─── CONFIG ───────────────────────────────────────────────────────────────────
BOT_TOKEN   = os.getenv("BOT_TOKEN", "SEU_TOKEN_AQUI")
CHANNEL_ID  = os.getenv("CHANNEL_ID", "@seu_canal")   # Ex: @meucanal ou -100123456789
ADMIN_IDS   = [int(x) for x in os.getenv("ADMIN_IDS", "0").split(",")]  # IDs separados por vírgula

# ─── GERADOR DE SINAIS ────────────────────────────────────────────────────────
def gerar_sinal():
    """Gera um sinal realista para o Aviator."""
    multiplicador = round(random.uniform(1.5, 4.5), 2)
    # Chance de sinal alto (5%) para variedade
    if random.random() < 0.05:
        multiplicador = round(random.uniform(5.0, 15.0), 2)

    horario = datetime.now() + timedelta(minutes=random.randint(1, 3))
    horario_str = horario.strftime("%H:%M")

    niveis_confianca = ["🟡 Médio", "🟢 Alto", "🟢 Alto", "🟢 Alto"]  # 75% alto
    confianca = random.choice(niveis_confianca)

    entradas = random.randint(1, 3)

    return {
        "multiplicador": multiplicador,
        "horario": horario_str,
        "confianca": confianca,
        "entradas": entradas,
    }

def formatar_mensagem_sinal(sinal: dict, numero: int = None) -> str:
    """Formata a mensagem do sinal para envio."""
    emoji_mult = "🚀" if sinal["multiplicador"] >= 5 else "✈️"
    header = f"#{numero} " if numero else ""

    return (
        f"╔══════════════════════╗\n"
        f"║  {emoji_mult}  SINAL AVIATOR  {emoji_mult}  ║\n"
        f"╚══════════════════════╝\n"
        f"\n"
        f"🎯 *Multiplicador:* `{sinal['multiplicador']}x`\n"
        f"⏰ *Horário de Entrada:* `{sinal['horario']}`\n"
        f"📊 *Confiança:* {sinal['confianca']}\n"
        f"🔁 *Entradas:* `{sinal['entradas']}x`\n"
        f"\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ _Gerencie sua banca com responsabilidade._\n"
        f"🔞 _Maior de 18 anos._"
    )

# ─── COMANDOS DO BOT ──────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📡 Receber Sinais", callback_data="info_sinais")],
        [InlineKeyboardButton("🔗 Acessar Plataforma", url="https://seu-link-afiliado.com")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "✈️ *BEM-VINDO AO AVIATOR SIGNALS!*\n\n"
        "Aqui você recebe os melhores sinais do Aviator em tempo real.\n\n"
        "📌 *Como usar:*\n"
        "1️⃣ Acesse a plataforma pelo botão abaixo\n"
        "2️⃣ Aguarde o sinal aparecer aqui\n"
        "3️⃣ Entre na rodada no horário indicado\n"
        "4️⃣ Retire antes do multiplicador indicado ✅\n\n"
        "🟢 *Sinais chegando em breve...*",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )

async def sinal_manual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: dispara um sinal manualmente."""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Você não tem permissão.")
        return

    sinal = gerar_sinal()
    msg = formatar_mensagem_sinal(sinal)

    await context.bot.send_message(
        chat_id=CHANNEL_ID,
        text=msg,
        parse_mode="Markdown",
    )
    await update.message.reply_text("✅ Sinal disparado no canal!")

async def sinal_customizado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /sinal 2.50 - dispara sinal com multiplicador específico."""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Você não tem permissão.")
        return

    try:
        mult = float(context.args[0])
        sinal = gerar_sinal()
        sinal["multiplicador"] = mult
        msg = formatar_mensagem_sinal(sinal)

        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=msg,
            parse_mode="Markdown",
        )
        await update.message.reply_text(f"✅ Sinal `{mult}x` disparado!", parse_mode="Markdown")
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Uso correto: /sinal 2.50")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: mostra o status do bot."""
    if update.effective_user.id not in ADMIN_IDS:
        return

    await update.message.reply_text(
        f"🤖 *Status do Bot*\n\n"
        f"✅ Online\n"
        f"📢 Canal: `{CHANNEL_ID}`\n"
        f"🕐 Hora atual: `{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}`\n"
        f"👤 Admins: `{len(ADMIN_IDS)}`",
        parse_mode="Markdown",
    )

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "info_sinais":
        await query.message.reply_text(
            "📡 *Como receber os sinais:*\n\n"
            "Os sinais são enviados automaticamente no canal.\n"
            "Fique de olho nas notificações! 🔔",
            parse_mode="Markdown",
        )

# ─── SCHEDULER DE SINAIS AUTOMÁTICOS ─────────────────────────────────────────
bot_instance = None

async def enviar_sinal_automatico():
    """Envia um sinal automático para o canal."""
    if not bot_instance:
        return
    sinal = gerar_sinal()
    msg = formatar_mensagem_sinal(sinal)
    try:
        await bot_instance.send_message(
            chat_id=CHANNEL_ID,
            text=msg,
            parse_mode="Markdown",
        )
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Sinal automático enviado: {sinal['multiplicador']}x")
    except Exception as e:
        print(f"[ERRO] Falha ao enviar sinal: {e}")

def run_scheduler():
    """Roda o scheduler em thread separada."""
    async def job():
        await enviar_sinal_automatico()

    def scheduled_job():
        asyncio.run(job())

    # Configura os horários de envio automático (ajuste conforme necessário)
    schedule.every(15).minutes.do(scheduled_job)   # A cada 15 minutos
    # schedule.every().hour.at(":00").do(scheduled_job)  # Alternativa: de hora em hora

    while True:
        schedule.run_pending()
        time.sleep(1)

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    global bot_instance

    print("🚀 Iniciando Aviator Signal Bot...")
    print(f"📢 Canal: {CHANNEL_ID}")
    print(f"👤 Admins: {ADMIN_IDS}")

    app = Application.builder().token(BOT_TOKEN).build()
    bot_instance = app.bot

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("disparar", sinal_manual))
    app.add_handler(CommandHandler("sinal", sinal_customizado))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CallbackQueryHandler(callback_handler))

    # Inicia scheduler em background
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("⏰ Scheduler de sinais automáticos iniciado.")

    print("✅ Bot online! Aguardando comandos...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
