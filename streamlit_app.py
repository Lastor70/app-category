import streamlit as st
import pandas as pd
import asyncio
from datetime import datetime
from data_fetcher import fetch_data

st.set_page_config(page_title="Categorization orders", page_icon="📈")

st.header('Фильтр по датам')
start_date = st.date_input('Начальная дата', value=datetime(2024, 9, 1))
end_date = st.date_input('Конечная дата', value=datetime(2024, 9, 3))

if end_date < start_date:
    st.error('Конечная дата не может быть раньше начальной даты.')

api_key = st.secrets["api_key"]

# Кешуємо результат виконання запиту до API
@st.cache_data
def load_data(api_key, start_date, end_date):
    # Виклик асинхронної функції через синхронний контекст
    return asyncio.run(fetch_data(api_key, start_date, end_date))

# Функція для завантаження даних та збереження у session_state
def fetch_and_store_data(api_key, start_date, end_date):
    with st.spinner('Загрузка данныъ...'):
        df_new = load_data(api_key, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        st.session_state['df_new'] = df_new

# Кнопка для завантаження даних
if st.button('Загрузить данные'):
    fetch_and_store_data(api_key, start_date, end_date)
    st.success("Данные загружены успешно!")

# Відображення даних, якщо вони вже завантажені
if 'df_new' in st.session_state:
    st.write(f'Данные за {start_date} - {end_date}')
    st.dataframe(st.session_state['df_new'])
else:
    st.write("Натисніть кнопку для завантаження даних.")

# Секція для побудови графіка
# st.subheader('Графік:')

if 'df_new' in st.session_state:
    df_new = st.session_state['df_new']
    
    # Створюємо список унікальних "Номерів замовлення"
    unique_orders = df_new['Номер замовлення'].unique()
    
    # Дозволяємо користувачеві обрати "Номер замовлення"
    selected_order = st.selectbox("Выберите номер заказа", unique_orders)
    
    # Фільтруємо дані для обраного "Номеру замовлення"
    filtered_data = df_new[df_new['Номер замовлення'] == selected_order]
    
    if not filtered_data.empty:
        # Перша таблиця з основною інформацією про замовлення
        st.subheader("Информация по заказам")
        first_table = {
            'Заказ': filtered_data['Номер замовлення'].iloc[0],
            'Offer-id': filtered_data['offer_id(заказа)'].iloc[0],
            'Order category': filtered_data['order_category'].iloc[0]
        }
        st.table(pd.DataFrame([first_table]))  # Перша таблиця
        
        # Друга таблиця з деталями по товарам
        st.subheader("Детали по товарам")
        second_table = filtered_data[[
            'Название товара в срм', 'offer_article', 'order_category', 
            'Себес $ (из срм)', 'Опт цена $ (себес + 25%)', 'Кількість товару'
        ]]
        second_table = second_table.rename(columns={
            'offer_article': 'Артикул',
            'order_category': 'Категория товара',
            'Название товара в срм': 'Название товара',
            'Себес $ (из срм)': 'Себес $ (из срм)',
            'Опт цена $ (себес + 25%)': 'Опт цена $ (себес + 25%)',
            'Кількість товару': 'Кол-во'
        })
        
        st.dataframe(second_table)  # Друга таблиця
        
    else:
        st.write("Немає даних для цього замовлення.")
else:
    st.write("Завантажте дані для побудови графіка.")