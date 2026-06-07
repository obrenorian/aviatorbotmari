"""
===========================================
  AVIATOR SIGNAL BOT - Telegram v3
  Autor: Void Partners
===========================================
pip install python-telegram-bot schedule python-dotenv
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
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()

# ─── CONFIG ───────────────────────────────────────────────────────────────────
BOT_TOKEN  = os.getenv("BOT_TOKEN", "SEU_TOKEN_AQUI")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@seu_canal")
ADMIN_IDS  = [int(x) for x in os.getenv("ADMIN_IDS", "0").split(",")]
LINK_CASA  = os.getenv("LINK_CASA", "https://seu-link-afiliado.com")
TZ         = ZoneInfo("Europe/Lisbon")

# ─── ESTADO DOS SINAIS ────────────────────────────────────────────────────────
# sinais_pendentes[sinal_id] = { multiplicador, horario, message_id_resultado }
sinais_pendentes = {}
sinal_counter = 0

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def hora_pt():
    return datetime.now(TZ)

def novo_id():
    global sinal_counter
    sinal_counter += 1
    return sinal_counter

def gerar_sinal():
    mult = round(random.uniform(1.5, 4.5), 2)
    if random.random() < 0.05:
        mult = round(random.uniform(5.0, 15.0), 2)
    horario = hora_pt() + timedelta(minutes=random.randint(1, 2))
    niveis = ["🟡 Médio", "🟢 Alto", "🟢 Alto", "🟢 Alto"]
    return {
        "id": novo_id(),
        "multiplicador": mult,
        "horario": horario.strftime("%H:%M"),
        "confianca": random.choice(niveis),
    }

def msg_sinal(sinal):
    emoji = "🚀" if sinal["multiplicador"] >= 5 else "✈️"
    return (
        f"👀 Nossa IA identificou um padrão...\n"
        f"\n"
        f"{emoji} *Meta:* `{sinal['multiplicador']}x`\n"
        f"⏰ *Janela de entrada:* `{sinal['horario']}`\n"
        f"📊 *Confiança:* {sinal['confianca']}\n"
        f"🔖 *ID:* `#{sinal['id']}`\n"
        f"\n"
        f"Essa é a sua chance. Não perca.\n"
        f"\n"
        f"🔞 _Jogue com responsabilidade._"
    )

def msg_resultado(sinal, green: bool):
    if green:
        return (
            f"✅ *GREEN* `#{sinal['id']}`\n"
            f"\n"
            f"🎯 Meta de `{sinal['multiplicador']}x` *atingida!*\n"
            f"⏰ Entrada: `{sinal['horario']}`\n"
            f"\n"
            f"💰 Quem entrou, lucrou. Próximo sinal em breve! 🔥"
        )
    else:
        return (
            f"❌ *RED* `#{sinal['id']}`\n"
            f"\n"
            f"Meta de `{sinal['multiplicador']}x` não atingida.\n"
            f"\n"
            f"😤 Faz parte. Próximo sinal vai compensar! 💪"
        )

def botoes_sinal():
    """Botões que aparecem em todos os sinais e resultados."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🆘 Quero ajuda pra jogar", url=f"https://t.me/{os.getenv('SUPORTE_USER', 'seu_suporte')}"),
            InlineKeyboardButton("🎰 Jogar agora", url=LINK_CASA),
        ]
    ])

def msg_divulgacao():
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
        f"👇 Acessa agora e garante o teu bónus:"
    )

# ─── ENVIO DE RESULTADO ───────────────────────────────────────────────────────
async def enviar_resultado(sinal_id: int, green: bool):
    """Envia ou edita a mensagem de resultado de um sinal."""
    if sinal_id not in sinais_pendentes:
        return

    sinal = sinais_pendentes[sinal_id]
    texto = msg_resultado(sinal, green)

    try:
        # Se já existe mensagem de resultado, edita ela
        if sinal.get("result_msg_id"):
            await bot_instance.edit_message_text(
                chat_id=CHANNEL_ID,
                message_id=sinal["result_msg_id"],
                text=texto,
                parse_mode="Markdown",
                reply_markup=botoes_sinal(),
            )
        else:
            # Envia nova mensagem de resultado
            sent = await bot_instance.send_message(
                chat_id=CHANNEL_ID,
                text=texto,
                parse_mode="Markdown",
                reply_markup=botoes_sinal(),
            )
            sinais_pendentes[sinal_id]["result_msg_id"] = sent.message_id

        status = "GREEN ✅" if green else "RED ❌"
        print(f"[{hora_pt().strftime('%H:%M:%S')} PT] {status} — Sinal #{sinal_id} ({sinal['multiplicador']}x)")

        # Remove do pendente após registrar resultado
        if green is not None:
            del sinais_pendentes[sinal_id]

    except Exception as e:
        print(f"[ERRO resultado] {e}")

# ─── JOBS AUTOMÁTICOS ─────────────────────────────────────────────────────────
bot_instance = None

async def job_sinal():
    sinal = gerar_sinal()
    try:
        await bot_instance.send_message(
            chat_id=CHANNEL_ID,
            text=msg_sinal(sinal),
            parse_mode="Markdown",
            reply_markup=botoes_sinal(),
        )
        # Salva sinal como pendente
        sinais_pendentes[sinal["id"]] = {**sinal, "result_msg_id": None}
        print(f"[{hora_pt().strftime('%H:%M:%S')} PT] ✈️ Sinal #{sinal['id']}: {sinal['multiplicador']}x")

        # Agenda resultado automático em 3 minutos
        sinal_id = sinal["id"]
        async def resultado_auto():
            await asyncio.sleep(180)  # 3 minutos
            # Só envia se ainda não foi corrigido manualmente
            if sinal_id in sinais_pendentes and sinais_pendentes[sinal_id].get("result_msg_id") is None:
                green = random.random() < 0.80  # 80% green
                await enviar_resultado(sinal_id, green)

        asyncio.create_task(resultado_auto())

    except Exception as e:
        print(f"[ERRO sinal] {e}")

async def job_divulgacao():
    keyboard = [[InlineKeyboardButton("🎰 Garantir Bónus de 100%", url=LINK_CASA)]]
    try:
        await bot_instance.send_message(
            chat_id=CHANNEL_ID,
            text=msg_divulgacao(),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        print(f"[{hora_pt().strftime('%H:%M:%S')} PT] 📢 Divulgação enviada")
    except Exception as e:
        print(f"[ERRO divulgação] {e}")

# ─── COMANDOS ADMIN ───────────────────────────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def cmd_disparar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Sem permissão.")
        return
    await job_sinal()
    await update.message.reply_text("✅ Sinal disparado!")

async def cmd_green(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /green 5 — marca sinal #5 como green"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    try:
        sinal_id = int(context.args[0])
        if sinal_id not in sinais_pendentes:
            await update.message.reply_text(f"❌ Sinal #{sinal_id} não encontrado ou já encerrado.")
            return
        await enviar_resultado(sinal_id, green=True)
        await update.message.reply_text(f"✅ GREEN aplicado no sinal #{sinal_id}!")
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Uso: /green 5")

async def cmd_red(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /red 5 — marca sinal #5 como red"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    try:
        sinal_id = int(context.args[0])
        if sinal_id not in sinais_pendentes:
            await update.message.reply_text(f"❌ Sinal #{sinal_id} não encontrado ou já encerrado.")
            return
        await enviar_resultado(sinal_id, green=False)
        await update.message.reply_text(f"✅ RED aplicado no sinal #{sinal_id}!")
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Uso: /red 5")

async def cmd_pendentes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: lista sinais aguardando resultado"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    if not sinais_pendentes:
        await update.message.reply_text("📭 Nenhum sinal pendente.")
        return
    linhas = [f"*Sinais pendentes:*\n"]
    for sid, s in sinais_pendentes.items():
        linhas.append(f"• `#{sid}` — {s['multiplicador']}x — entrada {s['horario']}")
    await update.message.reply_text("\n".join(linhas), parse_mode="Markdown")

async def cmd_divulgar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    await job_divulgacao()
    await update.message.reply_text("✅ Divulgação enviada!")

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    await update.message.reply_text(
        f"🤖 *Status*\n\n"
        f"✅ Online\n"
        f"📢 Canal: `{CHANNEL_ID}`\n"
        f"🕐 Hora PT: `{hora_pt().strftime('%d/%m/%Y %H:%M:%S')}`\n"
        f"⏳ Pendentes: `{len(sinais_pendentes)}`",
        parse_mode="Markdown",
    )

# ─── SCHEDULER ────────────────────────────────────────────────────────────────
def run_scheduler():
    loop = asyncio.new_event_loop()

    def wrap(coro_fn):
        def fn():
            loop.run_until_complete(coro_fn())
        return fn

    schedule.every(3).minutes.do(wrap(job_sinal))
    schedule.every(20).minutes.do(wrap(job_divulgacao))

    loop.run_forever() if False else None
    while True:
        schedule.run_pending()
        time.sleep(1)

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    global bot_instance

    print("🚀 Aviator Signal Bot v3 iniciando...")
    print(f"📢 Canal: {CHANNEL_ID} | 🕐 Timezone: Portugal")

    app = Application.builder().token(BOT_TOKEN).build()
    bot_instance = app.bot

    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("disparar",  cmd_disparar))
    app.add_handler(CommandHandler("green",     cmd_green))
    app.add_handler(CommandHandler("red",       cmd_red))
    app.add_handler(CommandHandler("pendentes", cmd_pendentes))
    app.add_handler(CommandHandler("divulgar",  cmd_divulgar))
    app.add_handler(CommandHandler("status",    cmd_status))

    t = threading.Thread(target=run_scheduler, daemon=True)
    t.start()
    print("⏰ Scheduler: sinal a cada 3min | divulgação a cada 20min")
    print("✅ Bot online!\n")
    print("Comandos admin:")
    print("  /disparar        → dispara sinal manual")
    print("  /green <id>      → marca sinal como GREEN")
    print("  /red <id>        → marca sinal como RED")
    print("  /pendentes       → lista sinais sem resultado")
    print("  /divulgar        → envia divulgação manual")
    print("  /status          → status do bot")

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
