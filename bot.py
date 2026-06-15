import asyncio
import os

from aiogram import Bot
from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from dotenv import load_dotenv

from keyboards import get_main_keyboard

from aiogram import F

from preprocessing import clean_and_analyze_data

from metrics import calculate_metrics
from database import init_db, save_analysis_results, get_latest_analysis

import glob
from aiogram.types import FSInputFile
from visualization import create_roi_chart, create_correlation_heatmap

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from prediction import train_and_predict_leads


# Загружаем переменные из .env
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

# Создаем объекты бота и диспетчера
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Класс для сохранения состояния диалога
class PredictState(StatesGroup):
    waiting_for_budget = State()

# Обработка команды /start
@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        "Привет!\n\n"
        "Я помогу оценить эффективность рекламных каналов.\n\n"
        "Загрузите CSV-файл для анализа.",
        reply_markup=get_main_keyboard()
    )

# Обработка загрузки CSV-файла
@dp.message(F.document)
async def handle_document(message: Message):
    document = message.document
    
    # Проверяем, что загружен именно CSV
    if not document.file_name.endswith('.csv'):
        await message.answer("Пожалуйста, загрузите файл в формате .csv")
        return
        
    # Формируем уникальное имя файла с ID пользователя
    user_id = message.from_user.id
    safe_file_name = f"{user_id}_{document.file_name}"
    file_path = os.path.join("uploads", safe_file_name)
    
    # Получаем информацию о файле и скачиваем его
    file_info = await bot.get_file(document.file_id)
    await bot.download_file(file_info.file_path, file_path)
    
    # --- АНАЛИТИКА ---
    try:
        # 1. Запускаем очистку и анализ данных
        df, rows_count, channels_count = clean_and_analyze_data(file_path)
        
        # Отправляем пользователю базовую статистику
        await message.answer(
            f"Файл получен.\n"
            f"Строк: {rows_count}\n"
            f"Каналов: {channels_count}\n\n"
            f"Начинаю обработку..."
        )
        
        # 2. Рассчитываем маркетинговые метрики
        df = calculate_metrics(df)
        
        # 3. Сохраняем результаты в SQLite
        save_analysis_results(message.from_user.id, df)
        
        await message.answer(
            "✅ <b> Данные успешно обработаны и сохранены в базу!</b>\n"
            "Выберите дальнейшее действие в меню."
        )
        
    except Exception as e:
        await message.answer(f"Произошла ошибка при чтении файла: {e}")

# Обработка кнопки "📂 Загрузить данные"
@dp.message(F.text == "📂 Загрузить данные")
async def upload_help_handler(message: Message):
    await message.answer(
        "📎 <b> Как загрузить файл: </b>\n\n"
        "1. Нажмите на значок скрепки 📎 (рядом с полем ввода сообщения).\n"
        "2. Выберите пункт <b>'Файл'</b> или <b>'Документ'</b>.\n"
        "3. Отправьте ваш CSV-файл в этот чат.\n\n"
        "Я автоматически считаю его и занесу данные в базу!"
    )

# Обработка кнопки "ℹ️ Помощь"
@dp.message(F.text == "ℹ️ Помощь")
async def help_handler(message: Message):
    await message.answer(
        "💡 <b>Справка по меню:</b>\n\n"
        "📂 <b>Загрузить данные</b> — инструкция по отправке файлов.\n"
        "📊 <b>Анализ</b> — выводит рейтинг каналов (ROI, стоимость лида) и дает советы по оптимизации бюджета.\n"
        "📉 <b>Графики</b> — генерирует столбчатую диаграмму окупаемости и матрицу корреляций.\n"
        "📈 <b>Прогноз</b> — — рассчитывает ожидаемое количество лидов при новом бюджете (при условии сохранения текущего распределения средств по каналам).\n\n"
        "❗ <b>Обратите внимание:</b> Для работы аналитики, графиков и прогноза нужно предварительно загрузить CSV-файл."
    )


# Обработка кнопки "📊 Анализ"
@dp.message(F.text == "📊 Анализ")
async def analysis_handler(message: Message):
    # Достаем данные из базы
    results = get_latest_analysis(message.from_user.id)
    
    if not results:
        await message.answer("Нет данных для анализа. Пожалуйста, сначала загрузите CSV-файл.")
        return

    # Сортируем каналы по ROI по убыванию
    sorted_results = sorted(results, key=lambda x: x[1], reverse=True)

    response_text = "📊 <b>Анализ эффективности каналов:</b>\n\n"
    
    # Формируем вывод для каждого канала
    for index, row in enumerate(sorted_results, start=1):
        channel, roi, cpl, cpa = row
        
        # Логика автоматических рекомендаций
        recommendation = "Держать на текущем уровне"
        if roi > 100:
            recommendation = "Увеличить бюджет 🟢"
        elif roi < 0:
            recommendation = "Сократить расходы 🔴"

        response_text += (
            f"<b>{channel}</b>\n"
            f"🏆 Рейтинг: {index} место\n"
            f"📈 ROI: {roi:.1f}%\n"
            f"💰 Стоимость лида (CPL): {cpl:.2f} ₽\n"
            f"💡 Рекомендация: <b> {recommendation} </b>\n"
            "──────────────\n"
        )
        
    await message.answer(response_text)

# Обработка кнопки "📉 Графики"
@dp.message(F.text == "📉 Графики")
async def graphs_handler(message: Message):
    # Ищем файлы текущего пользователя
    user_id = message.from_user.id
    list_of_files = glob.glob(f'uploads/{user_id}_*.csv')
    
    if not list_of_files:
        await message.answer("Нет данных для графиков. Пожалуйста, сначала загрузите CSV-файл.")
        return
        
    latest_file = max(list_of_files, key=os.path.getctime)
    
    await message.answer("🎨 Рисую графики, подождите пару секунд...")

    try:
        # Получаем данные
        df, _, _ = clean_and_analyze_data(latest_file)
        df = calculate_metrics(df)

        # Генерируем картинки
        roi_path = create_roi_chart(df)
        heatmap_path = create_correlation_heatmap(df)

        # Отправляем графики пользователю
        if roi_path:
            await message.answer_photo(
                FSInputFile(roi_path), 
                caption="📊 <b>Столбчатая диаграмма ROI</b>\nСравнение окупаемости по каналам."
            )
        if heatmap_path:
            await message.answer_photo(
                FSInputFile(heatmap_path), 
                caption="🔥 <b>Матрица корреляций</b>\nПоказывает скрытые зависимости между метриками."
            )

    except Exception as e:
        await message.answer(f"Произошла ошибка при создании графиков: {e}")

# Обработка кнопки "📈 Прогноз"
@dp.message(F.text == "📈 Прогноз")
async def forecast_start_handler(message: Message, state: FSMContext):
    # Проверяем, есть ли файлы для анализа
    list_of_files = glob.glob('uploads/*.csv')
    if not list_of_files:
        await message.answer("Сначала загрузите CSV-файл с данными.")
        return

    # Переводим бота в режим ожидания бюджета
    await state.set_state(PredictState.waiting_for_budget)
    await message.answer("Введите предполагаемый рекламный бюджет <b> (только число)</b>.:")


# Обработка введенного бюджета
@dp.message(PredictState.waiting_for_budget)
async def forecast_process_handler(message: Message, state: FSMContext):
    # Если пользователь передумал и нажал любую другую кнопку меню
    if message.text in ["📂 Загрузить данные", "📊 Анализ", "📉 Графики", "ℹ️ Помощь"]:
        await state.clear()
        await message.answer("Режим прогноза отменен. Нажмите на нужную кнопку еще раз.")
        return

    # Проверяем, ввел ли пользователь число
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите только число (например, 50000).")
        return
        

    budget = float(message.text)
    
   # Находим последний файл конкретного пользователя
    user_id = message.from_user.id
    list_of_files = glob.glob(f'uploads/{user_id}_*.csv')
    
    if not list_of_files:
        await message.answer("Файл не найден. Сначала загрузите CSV-файл с данными.")
        await state.clear()
        return
        
    latest_file = max(list_of_files, key=os.path.getctime)

    try:
        await message.answer("🤖 Модель обучается, считаю прогноз...")
        
        # Получаем данные и делаем прогноз
        df, _, _ = clean_and_analyze_data(latest_file)
        expected_leads = train_and_predict_leads(df, budget)
        
        await message.answer(
            f"🎯 <b>Прогноз эффективности:</b>\n\n"
            f"При бюджете: {budget:,.0f} ₽\n"
            f"Ожидаемое количество лидов: <b>≈ {expected_leads}</b>\n\n"
            f"<i>(Рассчитано с помощью модели машинного обучения Linear Regression при условии сохранения текущего распределения средств по каналам)</i>"
        )
    except Exception as e:
        await message.answer(f"Ошибка при расчете прогноза: {e}")
    finally:
        # Обязательно сбрасываем состояние, чтобы бот вернулся в обычный режим
        await state.clear()


# main() запускает бота и обеспечивает его работу
async def main():
    # Автоматически создаем папки для файлов и графиков, если их случайно нет
    for folder in ['uploads', 'reports']:
        os.makedirs(folder, exist_ok=True)

    # Создаем базу данных 
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())