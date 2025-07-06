import os
import yt_dlp
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)


def download_video(url: str) -> str:
    output_template = "downloads/%(title)s.%(ext)s"
    cookies_file = os.getenv("YT_DLP_COOKIES", "cookies.txt")
    last_exception = None

    for attempt in range(3):
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'recodevideo': 'mp4',
            'outtmpl': output_template,
            'cookies': cookies_file,
            'verbose': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)
        except Exception as e:
            last_exception = str(e)
    raise Exception(f"All retries exhausted. Last error: {last_exception}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Send me a video URL, and I'll download it for you!")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_text = update.message.text
    bot_username = context.bot.username

    if update.message.chat.type in ["group", "supergroup"]:
        if not message_text.startswith(f"@{bot_username} "):
            return
        parts = message_text.split(" ", 1)
        if len(parts) < 2:
            await update.message.reply_text("Please provide a video link after mentioning me.")
            return
        url = parts[1]
    else:
        url = message_text

    try:
        filename = download_video(url)
        try:
            with open(filename, 'rb') as video_file:
                await update.message.reply_video(video=video_file)
        finally:
            os.remove(filename)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set in the environment.")
    
    os.makedirs("downloads", exist_ok=True)
    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & (filters.ChatType.PRIVATE | filters.Entity("mention")), handle_message))
    
    application.run_polling()


if __name__ == "__main__":
    main()
