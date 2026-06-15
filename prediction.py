import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

def train_and_predict_leads(df, new_budget):
    """Обучает модель линейной регрессии и делает прогноз лидов."""
    # Приводим колонки к нижнему регистру 
    df.columns = df.columns.str.lower()
    
    # Проверяем наличие нужных колонок
    required_cols = ['cost', 'clicks', 'impressions', 'leads']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"В данных не хватает колонки '{col}' для прогноза.")

    # Очищаем данные от возможных нулей и NaN
    clean_df = df[required_cols].dropna()
    clean_df = clean_df[(clean_df != 0).all(axis=1)] # Убираем нулевые строки

    if clean_df.empty:
        raise ValueError("Недостаточно корректных данных для обучения модели.")

    # 1. Подготовка данных для модели
    X = clean_df[['cost', 'clicks', 'impressions']]
    y = clean_df['leads']

    # 2. Обучение модели
    model = LinearRegression()
    model.fit(X, y)

    # 3. Вычисляем историческую стоимость клика и показа для оценки новых значений
    avg_cpc = clean_df['cost'].sum() / clean_df['clicks'].sum()
    avg_cpi = clean_df['cost'].sum() / clean_df['impressions'].sum()

    # Оцениваем ожидаемые клики и показы при новом бюджете
    est_clicks = new_budget / avg_cpc
    est_impressions = new_budget / avg_cpi

    # 4. Формируем новые данные как DataFrame
    new_data = pd.DataFrame({
        'cost': [new_budget],
        'clicks': [est_clicks],
        'impressions': [est_impressions]
    })

    # Делаем прогноз по правилам scikit-learn
    predicted_leads = model.predict(new_data)
    
    # Возвращаем целое число лидов
    return max(0, int(predicted_leads[0]))

   