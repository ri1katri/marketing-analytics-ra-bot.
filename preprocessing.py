import pandas as pd

def clean_and_analyze_data(file_path):
    """Загружает CSV, очищает данные и возвращает базовую статистику."""
    # Читаем файл
    df = pd.read_csv(file_path) 
    
    # Удаляем дубликаты и заполняем пустые значения нулями
    df.drop_duplicates(inplace=True) 
    df.fillna(0, inplace=True) 
    
    # Считаем базовую статистику для ответа пользователю
    rows_count = len(df)
    
    # Ищем колонку с названием каналов
    channels_count = "Неизвестно"
    for col in df.columns:
        if col.lower() in ['channel', 'канал', 'source', 'источник']:
            channels_count = df[col].nunique()
            break
            
    return df, rows_count, channels_count