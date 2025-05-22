import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

AXI_FONT_PATH = "AxiFont.ttf"    # Путь к вашему кастомному шрифту AXI
CAPTION_FONT_SIZE = 42           # Размер шрифта для подписи
CAPTION_MARGIN = 40              # Отступ сверху для подписи

def get_token():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("ОШИБКА: Переменная окружения BOT_TOKEN не установлена!")
        exit(1)
    return token

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот работает! Пришлите фото с подписью (caption).")

async def add_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.photo:
            await update.message.reply_text("Пожалуйста, пришлите фото с подписью (caption).")
            return

        caption_text = update.message.caption
        if not caption_text:
            await update.message.reply_text("Пожалуйста, добавьте подпись (caption) к фото.")
            return

        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        img_bytes = BytesIO()
        await file.download_to_memory(out=img_bytes)
        img_bytes.seek(0)

        try:
            user_img = Image.open(img_bytes).convert("RGBA")
        except Exception as e:
            await update.message.reply_text(f"Ошибка загрузки изображения: {e}")
            return

        width, height = user_img.size

        # Загружаем фирменный шрифт (AXI)
        try:
            caption_font = ImageFont.truetype(AXI_FONT_PATH, CAPTION_FONT_SIZE)
        except Exception as e:
            await update.message.reply_text(f"Ошибка загрузки шрифта AXI: {e}")
            return

        draw = ImageDraw.Draw(user_img)
        caption_width, caption_height = draw.textsize(caption_text, font=caption_font)

        new_height = height + caption_height + CAPTION_MARGIN * 2
        result_img = Image.new("RGBA", (width, new_height), (0, 0, 0, 0))

        # Рисуем подпись по центру
        draw_result = ImageDraw.Draw(result_img)
        caption_x = (width - caption_width) // 2
        draw_result.text(
            (caption_x, CAPTION_MARGIN),
            caption_text,
            font=caption_font,
            fill=(255, 255, 255, 255)
        )

        # Вклеиваем оригинальную картинку ниже текста
        result_img.paste(user_img, (0, caption_height + CAPTION_MARGIN * 2), user_img)

        output = BytesIO()
        result_img.save(output, format="PNG")
        output.seek(0)

        await update.message.reply_photo(photo=output, caption="Готово!")

    except Exception as ex:
        await update.message.reply_text(f"Произошла ошибка: {ex}")

if __name__ == "__main__":
    TOKEN = get_token()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, add_caption))
    print("Бот запущен.")
    app.run_polling()
