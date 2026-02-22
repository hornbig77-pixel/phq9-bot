import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "8201940147:AAEMMzys1-HgfatgP6npcUyJbI30H1QBqGs"

ASKING = 0

QUESTIONS = [
    "Отсутствие интереса или удовольствия от того, чем вы обычно занимаетесь",
    "Подавленное настроение, ощущение депрессии или безнадёжности",
    "Проблемы со сном: трудности засыпания, прерывистый сон или, наоборот, слишком долгий сон",
    "Усталость или ощущение нехватки энергии",
    "Плохой аппетит или переедание",
    "Плохое мнение о себе: ощущение, что вы — неудачник, или чувство вины перед собой и близкими",
    "Трудности с концентрацией внимания (например, при чтении или просмотре телевизора)",
    "Замедленность движений или речи (настолько, что окружающие замечали это) или, наоборот, суетливость и беспокойство",
    "Мысли о том, что лучше бы вы умерли, или желание причинить себе вред",
]

OPTIONS = [
    ("Совсем нет", "0"),
    ("Несколько дней", "1"),
    ("Больше половины дней", "2"),
    ("Почти каждый день", "3"),
]


def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(text, callback_data=score)]
        for text, score in OPTIONS
    ])


def get_result(total, q9_score):
    if total <= 4:
        level = "Минимальная депрессия"
        recommendation = "Ваше состояние в норме. Продолжайте заботиться о себе."
    elif total <= 9:
        level = "Лёгкая депрессия"
        recommendation = "Рекомендую обратить внимание на своё состояние. Полезно будет поговорить со специалистом."
    elif total <= 14:
        level = "Умеренная депрессия"
        recommendation = "Рекомендую обратиться к психотерапевту для консультации."
    elif total <= 19:
        level = "Умеренно тяжёлая депрессия"
        recommendation = "Настоятельно рекомендую обратиться к специалисту в ближайшее время."
    else:
        level = "Тяжёлая депрессия"
        recommendation = "Необходима помощь специалиста. Пожалуйста, обратитесь к психотерапевту или психиатру."

    q9_warning = ""
    if q9_score > 0:
        q9_warning = (
            "\n\n⚠️ *Важно:* вы отметили наличие мыслей о смерти или о причинении "
            "себе вреда. Пожалуйста, не оставайтесь с этим одни — обратитесь к специалисту."
        )

    return level, recommendation, q9_warning


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["answers"] = []
    context.user_data["question_index"] = 0

    await update.message.reply_text(
        "Здравствуйте!\n\n"
        "Это тест PHQ-9 — короткий опросник для оценки симптомов депрессии. "
        "Он состоит из 9 вопросов и займёт около 2 минут.\n\n"
        "⚠️ *Важно:* тест не является диагнозом. "
        "Результаты носят ориентировочный характер и не заменяют консультацию специалиста.\n\n"
        "Нажмите кнопку, чтобы начать:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Начать тест", callback_data="start_test")]
        ])
    )
    return ASKING


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "start_test":
        await send_question(query, context)
        return ASKING

    context.user_data["answers"].append(int(query.data))
    context.user_data["question_index"] += 1

    index = context.user_data["question_index"]

    if index < len(QUESTIONS):
        await send_question(query, context)
        return ASKING
    else:
        await show_result(query, context)
        return ConversationHandler.END


async def send_question(query, context):
    index = context.user_data["question_index"]
    question = QUESTIONS[index]

    text = (
        f"*Вопрос {index + 1} из {len(QUESTIONS)}*\n\n"
        f"За последние 2 недели, как часто вас беспокоило:\n\n"
        f"_{question}_"
    )

    await query.edit_message_text(
        text=text,
        parse_mode="Markdown",
        reply_markup=get_keyboard()
    )


async def show_result(query, context):
    answers = context.user_data["answers"]
    total = sum(answers)
    q9_score = answers[8]

    level, recommendation, q9_warning = get_result(total, q9_score)

    filled = round(total / 27 * 10)
    bar = "█" * filled + "░" * (10 - filled)

    text = (
        f"✅ *Тест завершён*\n\n"
        f"Ваш результат: *{total} из 27*\n"
        f"{bar}\n\n"
        f"Уровень: *{level}*\n\n"
        f"{recommendation}"
        f"{q9_warning}\n\n"
        f"_Этот тест — скрининговый инструмент, а не диагноз. "
        f"Точную оценку состояния может дать только специалист._\n\n"
        f"📖 Больше о психологии и психотерапии: [Дневник психотерапевта](https://t.me/psychotherapist_diary)\n\n"
        f"Хотите пройти тест снова? Напишите /start"
    )

    await query.edit_message_text(
        text=text,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Тест отменён. Напишите /start, чтобы начать заново."
    )
    return ConversationHandler.END


async def main():
    import asyncio

    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASKING: [CallbackQueryHandler(handle_callback)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    print("Бот запущен. Нажмите Ctrl+C для остановки.")

    async with app:
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        await asyncio.Event().wait()
        await app.updater.stop()
        await app.stop()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())