import httpx
import logging
from config import settings

logger = logging.getLogger(__name__)

async def send_tender_notification(
    title: str,
    machinery_type: str | None,
    price: float | None,
    url: str,
    scout_score: float,
    platform: str,
    region: str | None
) -> bool:
    """
    Sends a formatted HTML notification card about a new tender to the Telegram Chat/Channel.
    """
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        logger.warning("Telegram Bot Token or Chat ID not configured. Skipping notification.")
        return False

    # Format price nicely
    formatted_price = f"{price:,.0f}".replace(",", " ") if price is not None else "Не указана"

    # HTML Card layout
    message_text = (
        f"<b>🆕 Обнаружен новый лот!</b>\n\n"
        f"🚜 <b>Техника:</b> {machinery_type or 'Не определено'}\n"
        f"🏷️ <b>Название:</b> {title}\n"
        f"💰 <b>Цена:</b> {formatted_price} ₽\n"
        f"📊 <b>Выгода (Scout Score):</b> <code>+{scout_score}%</code>\n"
        f"📍 <b>Регион:</b> {region or 'Не указан'}\n"
        f"🌐 <b>Площадка:</b> {platform}"
    )

    # Telegram Inline Keyboard link
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "🔗 Открыть лот на площадке", "url": url}
            ]
        ]
    }

    api_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": message_text,
        "parse_mode": "HTML",
        "reply_markup": reply_markup
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, json=payload, timeout=5.0)
            if response.status_code == 200:
                logger.info("Notification successfully sent to Telegram.")
                return True
            else:
                logger.error(f"Failed to send Telegram notification: {response.status_code} {response.text}")
                return False
    except Exception as e:
        logger.error(f"Exception occurred while sending Telegram notification: {e}")
        return False
