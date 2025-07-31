from aiogram import types, Router,F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import random
from app_zaek.api import create_or_update_user, get_question, update_user_statistic

zaek_routers = Router()


@zaek_routers.callback_query(lambda c: c.data == 'user')
async def zaek_user(callback: types.CallbackQuery):
    telegram_id = str(callback.from_user.id)
    name_telegram = callback.from_user.full_name
    create_or_update_user(telegram_id, name_telegram)
    user = create_or_update_user(telegram_id, name_telegram)

    await callback.message.edit_text(
        f"{user['name_telegram']}\n"
        f"Количество попыток: {user['total_attempts']}\n"
        f"Количество верных попыток: {user['correct_attempts']}"
    )


@zaek_routers.callback_query(lambda c: c.data.startswith('answer_'))
async def handle_answer(callback: types.CallbackQuery):
    _, is_correct = callback.data.split('_')
    is_correct = is_correct == 'True'

    # 1. Сначала отправляем результат ответа (новое сообщение)
    result_text = "✅ Правильный ответ!" if is_correct else "❌ Неверный ответ!"

    await update_user_statistic(str(callback.from_user.id), is_correct)



    # Создаем клавиатуру для нового вопроса
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="Следующий вопрос",
        callback_data="question"
    ))

    # Отправляем результат как новое сообщение
    await callback.message.answer(
        result_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

    # 2. Оставляем оригинальное сообщение с вопросом без изменений
    # (просто убираем кнопки ответов)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass



    await callback.answer()


@zaek_routers.callback_query(lambda c: c.data == 'question')
async def zaek_question(callback: types.CallbackQuery):
    # 3. При нажатии "Следующий вопрос" создаем новое сообщение с вопросом
    question_data = get_question()

    if not question_data:
        await callback.answer("Вопросы не найдены", show_alert=True)
        return

    question_text = (
        f"<b>Продукт:</b> {question_data['product'] if question_data['product'] else ''}\n"
        f"<b>Вопрос:</b> {question_data['question']}"
    )

    builder = InlineKeyboardBuilder()
    answers = question_data['answers']
    random.shuffle(answers)

    for answer in answers:
        builder.row(InlineKeyboardButton(
            text=answer['text'],
            callback_data=f"answer_{answer['is_correct']}"
        ))

    # Отправляем новый вопрос как новое сообщение
    await callback.message.answer(
        question_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

    # Удаляем кнопку "Следующий вопрос" из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass

    await callback.answer()