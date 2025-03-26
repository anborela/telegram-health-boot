from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import datetime
import os

TOKEN = os.environ["TELEGRAM_TOKEN"]
registro = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hola, soy tu asistente de salud. ¿Qué has comido hoy?")

async def mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    user = update.effective_user.first_name
    hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    registro.append({"usuario": user, "mensaje": texto, "hora": hora})
    await update.message.reply_text("¿Cómo te sentiste después de comer eso?")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensaje))
app.run_polling()
