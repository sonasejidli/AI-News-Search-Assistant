import html
import logging
import shutil, pathlib

# Hər başlanğıcda __pycache__ sil — köhnə .pyc faylları bug yaradır
_cache = pathlib.Path(__file__).parent / "__pycache__"
if _cache.exists():
    shutil.rmtree(_cache, ignore_errors=True)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    CallbackQueryHandler, filters, ContextTypes
)

from config import TELEGRAM_BOT_TOKEN
from query_parser import parse_query
import Search
from Search import search_news
from keywords import extract_keywords, format_keywords_text

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


_last_results: dict[int, list[dict]] = {}
_last_query: dict[int, dict] = {}


def escape(text: str) -> str:
    return html.escape(str(text) if text else "")


def format_article(article: dict, idx: int) -> str:
    title = escape(article.get("title", "Başlıqsız"))
    source = escape(article.get("source", "—"))
    published = escape(article.get("published_at", "—"))
    url = escape(article.get("url", ""))
    snippet = escape(article.get("snippet", ""))
    score = article.get("score", 0)
    category = escape(article.get("category", ""))

    msg = f"<b>{idx}. {title}</b>\n"
    msg += f"📅 {published}    🌐 {source}"
    if category:
        msg += f"    🏷 {category}"
    msg += f"\n⭐ Uyğunluq: {score}\n\n"
    msg += f"<i>{snippet}...</i>\n\n"
    if url and url.startswith("http"):
        msg += f'🔗 <a href="{url}">Məqaləni aç</a>'
    return msg


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Salam! Mən xəbər axtarış assistentinəm.\n\n"
        "Mənə təbii dildə sual ver:\n"
        "  • <i>AccessBank haqqında xəbər tap</i>\n"
        "  • <i>20 may SOCAR-la bağlı nə var?</i>\n"
        "  • <i>18-21 may arası gömrük xəbərləri</i>\n"
        "  • <i>Bank xəbərlərində ən çox keçən sözlər</i>"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    uid = update.effective_user.id

    thinking = await update.message.reply_text("🔍 Axtarıram...")

    try:
        parsed = parse_query(user_text)
        logger.info(f"Parsed: {parsed}")
        _last_query[uid] = parsed

        intent = parsed.get("intent", "search")

        # ====== KEYWORD INTENT ======
        if intent == "keywords":
            topic = parsed.get("topic") or ""
            articles = search_news(
                query=topic or "xəbər",
                date_from=parsed.get("date_from"),
                date_to=parsed.get("date_to"),
                category=parsed.get("category"),
                source=parsed.get("source"),
                n=100,
            )
            if not articles:
                await thinking.edit_text("❌ Bu filtrlərlə heç bir məqalə tapılmadı.")
                return

            articles_for_kw = [
                {"title": a["title"], "content": a["snippet"]}
                for a in articles
            ]
            kw_result = extract_keywords(articles_for_kw, top_n=15)
            text = format_keywords_text(kw_result)
            await thinking.delete()
            await update.message.reply_text(text, parse_mode="Markdown")
            return

        # ====== SEARCH INTENT ======
        results = search_news(
            query=parsed.get("topic") or user_text,
            date_from=parsed.get("date_from"),
            date_to=parsed.get("date_to"),
            category=parsed.get("category"),
            source=parsed.get("source"),
            n=5,
        )

        if not results:
            await thinking.edit_text(
                "❌ Heç bir nəticə tapılmadı.\n"
                "Sorğunu fərqli yazmağa çalış."
            )
            return

        _last_results[uid] = results

        filters_info = []
        if parsed.get("date_from") or parsed.get("date_to"):
            df = parsed.get("date_from", "?")
            dt = parsed.get("date_to", "?")
            filters_info.append(f"📅 {df} → {dt}")
        if parsed.get("category"):
            filters_info.append(f"🏷 {parsed['category']}")
        if parsed.get("source"):
            filters_info.append(f"🌐 {parsed['source']}")

        header = f"✅ <b>{len(results)} nəticə tapıldı</b>"
        if filters_info:
            header += "\n" + " | ".join(filters_info)
        await thinking.delete()
        await update.message.reply_text(header, parse_mode="HTML")

        for i, art in enumerate(results, 1):
            try:
                await update.message.reply_text(
                    format_article(art, i),
                    parse_mode="HTML",
                    disable_web_page_preview=False,
                )
            except Exception as e:
                logger.error(f"Mesaj göndərmə xətası: {e}")

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Keyword-ləri göstər", callback_data="show_keywords")]
        ])
        await update.message.reply_text(
            "Bu nəticələrlə bağlı ən çox keçən sözləri görmək istəyirsən?",
            reply_markup=keyboard,
        )

    except Exception as e:
        logger.exception("handle_message xətası")
        try:
            await thinking.edit_text(f"⚠️ Xəta baş verdi: {escape(str(e))}")
        except Exception:
            await update.message.reply_text(f"⚠️ Xəta: {escape(str(e))}")


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id

    if query.data == "show_keywords":
        results = _last_results.get(uid)
        if not results:
            await query.message.reply_text("Əvvəlcə bir axtarış et.")
            return
        articles_for_kw = [
            {"title": r["title"], "content": r["snippet"]}
            for r in results
        ]
        kw_result = extract_keywords(articles_for_kw, top_n=15)
        text = format_keywords_text(kw_result)
        await query.message.reply_text(text, parse_mode="Markdown")


def main():
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "❌ TELEGRAM_BOT_TOKEN tapılmadı. .env-ə əlavə et:\n"
            "TELEGRAM_BOT_TOKEN=botfather-dan-aldigin-token"
        )

    logger.info("Search module: %s (%s)", Search.__file__, Search.SEARCH_VERSION)

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot işə düşdü. Ctrl+C ilə dayandır.")
    app.run_polling()


if __name__ == "__main__":
    main()
