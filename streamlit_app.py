import streamlit as st
import pandas as pd
import asyncio
from datetime import datetime
from data_fetcher import fetch_data

st.set_page_config(page_title="Categorization orders", page_icon="📈")

st.header('Фільтр за датами')
start_date = st.date_input('Початкова дата', value=datetime(2024, 9, 1))
end_date = st.date_input('Кінцева дата', value=datetime(2024, 9, 3))

if end_date < start_date:
    st.error('Кінцева дата не може бути раніше початкової дати.')

api_key = st.secrets["api_key"]

# Кешуємо результат виконання запиту до API
@st.cache_data
def load_data(api_key, start_date, end_date):
    # Виклик асинхронної функції через синхронний контекст
    return asyncio.run(fetch_data(api_key, start_date, end_date))

# Функція для завантаження даних та збереження у session_state
def fetch_and_store_data(api_key, start_date, end_date):
    with st.spinner('Завантаження даних...'):
        df_new = load_data(api_key, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        st.session_state['df_new'] = df_new

# Кнопка для завантаження даних
if st.button('Завантажити дані'):
    fetch_and_store_data(api_key, start_date, end_date)
    st.success("Дані завантажено успішно!")

# Відображення даних, якщо вони вже завантажені
if 'df_new' in st.session_state:
    st.write(f'Дані за {start_date} - {end_date}')
    st.dataframe(st.session_state['df_new'])
else:
    st.write("Натисніть кнопку для завантаження даних.")

# Секція для побудови графіка
st.subheader('Графік:')

# Перевіряємо, чи дані вже завантажені
if 'df_new' in st.session_state:
    df_new = st.session_state['df_new']
    # Додайте тут код для побудови графіка
else:
    st.write("Завантажте дані для побудови графіка.")