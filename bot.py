import os
import logging
from dotenv import load_dotenv
from anthropic import Anthropic
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

conversations: dict[int, list[dict]] = {}
MAX_EXCHANGES = 10

SYSTEM_PROMPT = """You are the ANBORELA conversational support assistant — a non-clinical AI built to offer empathetic, anonymous, and non-judgmental dialogue to people navigating addiction recovery, behavioural health challenges, or emotional distress.

IDENTITY:
- Operated by Anborela OÜ (registered in Estonia, EU e-Residency)
- Research prototype — not a licensed medical or psychological service
- Independent from Big Tech: not hosted on AWS, Azure, or Google Cloud
- Compliant with GDPR and designed in alignment with the EU AI Act

LANGUAGE RULE — CRITICAL:
- ALWAYS respond in the same language the user writes in
- If the user writes in French, respond in French
- If the user writes in German, respond in German
- If the user writes in Polish, respond in Polish
- If the user switches language mid-conversation, switch with them immediately
- Never default to English unless the user writes in English

CORE PRINCIPLES:
1. LISTEN FIRST — reflect feelings before offering any information
2. VALIDATE — normalise struggle without minimising it
3. NO JUDGMENT — never moralise about substance use, relapses, or behaviour
4. STAGE AWARENESS — adapt tone to recovery stage: pre-contemplation, contemplation, action, maintenance, relapse
5. ANONYMITY — never ask for name, ID, location, or medical history
6. BOUNDARIES — for clinical questions, always redirect to professionals

SAFETY LAYER — NON-NEGOTIABLE:
- If user expresses suicidal ideation, self-harm intent, or acute crisis:
  * STOP all other content immediately
  * Provide emergency numbers FIRST in the user's language:
    - Spain: 024 (crisis line) · 112 (emergency)
    - EU-wide: 116 123 (Samaritans multilingual)
    - UK: 116 123 · 999 (emergency)
  * Then offer calm, present support
- Never leave a crisis message without a referral to live human help

TONE & STYLE:
- Warm, calm, unhurried — like a trusted companion who understands recovery from the inside
- Short paragraphs, accessible language, no clinical jargon
- Never preachy, never clinical unless user introduces clinical terms
- Use the user's own words to reflect understanding back

ABSOLUTE LIMITS:
- Never diagnose, prescribe, or recommend specific medications or doses
- Never provide drug interaction information
- Never discourage seeking professional treatment
- Never claim to replace therapy, psychiatry, or medical care
- Never reference or repeat personal information across sessions"""

WELCOME_MSG = """🔵 *ANBORELA*

Write to me in any language — I will respond in yours.
Escríbeme en cualquier idioma — te respondo en el tuyo.

🇪🇺 Available in all EU languages · Disponible en todos los idiomas UE

──────────────────────

📋 *Important · Aviso importante*
- Non-clinical conversational AI · IA conversacional no clínica
- No personal data stored · Sin datos personales almacenados
- /salir to end session · /salir para terminar la sesión
- Crisis: *024* (ES) · *116 123* (EU) · *999* (UK)

_Anborela OÜ · Estonia · GDPR compliant · Pre-deployment ethical review_

──────────────────────

How are you feeling today?
¿Cómo estás hoy?"""

GOODBYE_MSG = """Session ended. All conversation data has been permanently deleted.
Sesión finalizada. Los datos han sido eliminados de forma permanente.

Take care. You can return whenever you need. 🔵
Cuídate. Puedes volver cuando quieras.

_ANBORELA · Anborela OÜ · ai@anborela.ee_"""

PRIVACY_MSG = """*Privacy & Data · Privacidad y Datos — ANBORELA*

- *Collected:* only session text, in temporary memory
- *NOT collected:* name, ID, location, medical history
- *Storage:* messages exist only in RAM during active session
- *On /salir:* everything deleted immediately
- *Third parties:* no data sharing
- *Legal basis:* GDPR · Anborela OÜ · Estonia (EU)

_More info: ai@anborela.ee_"""

HELP_MSG = """*Commands · Comandos*

/start — Start · Iniciar
/reset — New session · Nueva sesión
/salir — End & delete · Terminar y borrar
/privacidad — Privacy policy · Política de datos
/ayuda — This help · Esta ayuda

_ANBORELA · Non-clinical conversational AI support_"""

QUALITY_SEAL = """

━━━━━━━━━━━━━━━━━━━━━
🔵 *ANBORELA · Verified Information*
✓ Non-clinical AI · Conversational support only
✓ No personal data · European infrastructure
✓ Does not replace professional care
_Crisis: 024 (ES) · 116 123 (EU) · 999 (UK)_
━━━━━━━━━━━━━━━━━━━━━"""

ERROR_MSG = """Technical error. Please try again in a few seconds.
Error técnico. Por favor inténtalo de nuevo.

Urgent support · Apoyo urgente: *024* (ES) · *116 123* (EU)"""


def get_history(user_id: int) -> list[dict]:
    if user_id not in conversations:
        conversations[user_id] = []
    return conversations[user_id]


def trim_history(history: list[dict]) -> None:
    while len(history) > MAX_EXCHANGES * 2:
        history.pop(0)


async def safe_reply(update: Update, text: str) -> None:
    try:
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception:
        plain = text.replace("*", "").replace("_", "").replace("`", "")
        await update.message.reply_text(plain)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conversations[update.effective_user.id] = []
    logger.info("New session: user %s", update.effective_user.id)
    await safe_reply(update, WELCOME_MSG)


async def cmd_salir(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conversations.pop(update.effective_user.id, None)
    await update.message.reply_text(
        GOODBYE_MSG.replace("*", "").replace("_", "")
    )


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conversations[update.effective_user.id] = []
    await update.message.reply_text("✓ Session restarted · Sesión reiniciada")


async def cmd_ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await safe_reply(update, HELP_MSG)


async def cmd_privacidad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await safe_reply(update, PRIVACY_MSG)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_text = update.message.text

    history = get_history(user_id)
    history.append({"role": "user", "content": user_text})
    trim_history(history)

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing",
    )

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=history,
        )

        reply_text = "".join(
            block.text for block in response.content if block.type == "text"
        )

        history.append({"role": "assistant", "content": reply_text})

        await safe_reply(update, reply_text + QUALITY_SEAL)

    except Exception as e:
        logger.error("Claude API error — user %s: %s", user_id, str(e))
        await safe_reply(update, ERROR_MSG)


def main() -> None:
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_TOKEN not set")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("salir", cmd_salir))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(CommandHandler("ayuda", cmd_ayuda))
    app.add_handler(CommandHandler("privacidad", cmd_privacidad))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🔵 ANBORELA bot running — claude-sonnet-4-20250514")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
