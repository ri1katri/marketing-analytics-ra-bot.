import pandas as pd
import numpy as np

def calculate_metrics(df):
    df.columns = df.columns.str.lower()

    # Базовые метрики эффективности
    if 'clicks' in df.columns and 'impressions' in df.columns:
        df['ctr'] = (df['clicks'] / df['impressions']).fillna(0) * 100

    if 'cost' in df.columns and 'clicks' in df.columns:
        df['cpc'] = (df['cost'] / df['clicks']).fillna(0)

    if 'cost' in df.columns and 'leads' in df.columns:
        df['cpl'] = (df['cost'] / df['leads']).fillna(0)

    if 'cost' in df.columns and 'conversions' in df.columns:
        df['cpa'] = (df['cost'] / df['conversions']).fillna(0)
    else:
        df['cpa'] = 0 # Заглушка, если колонки конверсий нет

    # Финансовые метрики 
    if 'revenue' in df.columns and 'cost' in df.columns:
        df['roi'] = ((df['revenue'] - df['cost']) / df['cost']).fillna(0) * 100
        df['roas'] = (df['revenue'] / df['cost']).fillna(0)
    else:
        df['roi'] = 0
        df['roas'] = 0

    # Убираем возможные бесконечности
    df.replace([np.inf, -np.inf], 0, inplace=True)
    
    return df