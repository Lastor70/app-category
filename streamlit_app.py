import streamlit as st
import pandas as pd
import altair as alt
import data_fetcher
from datetime import datetime

st.set_page_config(page_title="Categorization orders", page_icon="📈")
st.header('Таблиця замовлень:')

api_key = st.secrets["api_key"]

@st.cache_data
def load_data(api_key):
    # Переконайтеся, що fetch_data повертає серіалізовані дані
    return data_fetcher.fetch_data(api_key)

# Функція для завантаження даних та збереження у session_state
def fetch_and_store_data(api_key):
    df_new = load_data(api_key)
    current_date = datetime.now().date()
    date = current_date.strftime('%Y-%m-%d')
    st.session_state['df_new'] = df_new
    st.session_state['date'] = date

# Кнопка для завантаження даних
if st.button('Завантажити дані'):
    fetch_and_store_data(api_key)
    st.success("Дані завантажено успішно!")

# Відображення даних, якщо вони вже завантажені
if 'df_new' in st.session_state:
    date = st.session_state.get('date', 'Невідома дата')
    st.write(f'Дані за {date}')
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