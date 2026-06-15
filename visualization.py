import matplotlib.pyplot as plt
import seaborn as sns
import os
import pandas as pd

def create_roi_chart(df):
    plt.figure(figsize=(10, 6))
    
    # Ищем колонку с каналом 
    channel_col = next((col for col in df.columns if col in ['channel', 'канал', 'source']), None)
    
    if not channel_col or 'roi' not in df.columns:
        return None

    # Строим график
    sns.barplot(x=channel_col, y='roi', data=df, color='royalblue')
    plt.title('ROI по рекламным каналам', fontsize=14)
    plt.ylabel('ROI (%)', fontsize=12)
    plt.xlabel('Канал', fontsize=12)
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Сохраняем в папку reports
    filepath = os.path.join('reports', 'channel_roi.png')
    plt.savefig(filepath)
    plt.close()
    
    return filepath

def create_correlation_heatmap(df):
    plt.figure(figsize=(8, 6))
    
    numeric_df = df.select_dtypes(include=['float64', 'int64'])
    
    if numeric_df.empty:
        return None

    # Строим матрицу
    corr = numeric_df.corr()
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5)
    plt.title('Матрица корреляций', fontsize=14)
    plt.tight_layout()

    filepath = os.path.join('reports', 'correlation.png')
    plt.savefig(filepath)
    plt.close()
    
    return filepath