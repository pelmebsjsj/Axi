import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = os.environ["BOT_TOKEN"]  # Токен брать из переменных окружения!
AXI_FONT_PATH = "AxiFont.ttf"    # Путь к вашему кастомному шрифту AXI
CAPTION_FONT_SIZE = 42           # Размер шрифта для подписи
CAPTION_MARGIN = 40              # Отступ сверху для подписи

async def add_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.photo:
        await update.message.reply_text("Пожалуйста, пришлите фото с подписью (текстом).")
        return

    caption_text = update.message.caption
    if not caption_text:
        await update.message.reply_text("Пожалуйста, добавьте подпись (текст) к фото.")
        return

    # Получаем фото максимального размера
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    img_bytes = BytesIO()
    await file.download_to_memory(out=img_bytes)
    img_bytes.seek(0)

    user_img = Image.open(img_bytes).convert("RGBA")
    width, height = user_img.size

    # Загружаем фирменный шрифт (AXI)
    try:
        caption_font = ImageFont.truetype(AXI_FONT_PATH, CAPTION_FONT_SIZE)
    except Exception as e:
        await update.message.reply_text(f"Ошибка загрузки шрифта AXI: {e}")
        return

    # Высчитываем размер подписи
    draw = ImageDraw.Draw(user_img)
    caption_width, caption_height = draw.textsize(caption_text, font=caption_font)

    # Создаем новое изображение с местом сверху под подпись
    new_height = height + caption_height + CAPTION_MARGIN * 2
    result_img = Image.new("RGBA", (width, new_height), (0, 0, 0, 0))

    # Рисуем подпись (центр, белый)
    draw_result = ImageDraw.Draw(result_img)
    caption_x = (width - caption_width) // 2
    draw_result.text((caption_x, CAPTION_MARGIN), caption_text, font=caption_font, fill=(255, 255, 255, 255))

    # Вклеиваем оригинальную картинку ниже текста
    result_img.paste(user_img, (0, caption_height + CAPTION_MARGIN * 2), user_img)

    # Сохраняем и отправляем
    output = BytesIO()
    result_img.save(output, format="PNG")
    output.seek(0)

    await update.message.reply_photo(photo=output, caption="Готово!")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, add_caption))
    print("Бот запущен.")
    app.run_polling()
