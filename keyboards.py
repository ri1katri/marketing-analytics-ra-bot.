from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📂 Загрузить данные")],
            [KeyboardButton(text="📊 Анализ"), KeyboardButton(text="📈 Прогноз")],
            [KeyboardButton(text="📉 Графики"), KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True, # Делает кнопки компактными
        input_field_placeholder="Выберите действие ниже..."
    )
    return keyboard
