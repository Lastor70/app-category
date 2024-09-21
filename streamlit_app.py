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
    with st.spinner('Загрузка данных...'):
        df_new = load_data(api_key, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        st.session_state['df_new'] = df_new
        print(df_new[df_new['Номер замовлення'] == '554245UZ'])

# Кнопка для завантаження даних
if st.button('Загрузить данные'):
    fetch_and_store_data(api_key, start_date, end_date)
    st.success("Данные загружены успешно!")

# Відображення даних, якщо вони вже завантажені
if 'df_new' in st.session_state:
    st.write(f'Данные за {start_date} - {end_date}')
    st.dataframe(st.session_state['df_new'])
else:
    st.write("Нажмите кнопку для загрузки данных.")

if 'df_new' in st.session_state:
    df_new = st.session_state['df_new']
    
    # Перевірка наявності необхідних стовпців
    required_columns = ['Номер замовлення', 'offer_id(заказа)', 'order_category', 'Название товара в срм', 'offer_article', 'order_category', 'Себес $ (из срм)', 'Опт цена $ (себес + 25%)', 'Кількість товару']
    missing_columns = [col for col in required_columns if col not in df_new.columns]
    
    if missing_columns:
        st.error(f"Missing columns: {', '.join(missing_columns)}")
    else:
        # Створюємо список унікальних категорій замовлення
        unique_categories = df_new['order_category'].unique()
        
        # Дозволяємо користувачеві обрати категорію замовлення
        selected_category = st.selectbox("Виберите категорию заказа", unique_categories)
        
        # Фільтруємо дані за обраною категорією
        category_filtered_data = df_new[df_new['order_category'] == selected_category]
        
        if not category_filtered_data.empty:
            # Створюємо список унікальних "Номерів замовлення" для обраної категорії
            unique_orders = category_filtered_data['Номер замовлення'].unique()
            
            # Дозволяємо користувачеві обрати "Номер замовлення"
            selected_order = st.selectbox("Виберите номер заказа", unique_orders)
            
            # Фільтруємо дані для обраного "Номеру замовлення"
            filtered_data = category_filtered_data[category_filtered_data['Номер замовлення'] == selected_order]
            
            if not filtered_data.empty:
                # Перша таблиця з основною інформацією про замовлення
                st.subheader("Информация о заказах")
                first_table = {
                    'Заказ': filtered_data['Номер замовлення'].iloc[0],
                    'Offer-id': filtered_data['offer_id(заказа)'].iloc[0],
                    'Order category': filtered_data['order_category'].iloc[0]
                }
                st.table(pd.DataFrame([first_table]))  # Перша таблиця
                
                # Друга таблиця з деталями по товарам
                st.subheader("Детали по товарам")
                second_table = filtered_data[[
                    'Название товара в срм', 'offer_article', 'product_category', 
                    'Себес $ (из срм)', 'Опт цена $ (себес + 25%)', 'Кількість товару'
                ]]
                second_table = second_table.rename(columns={
                    'offer_article': 'Артикул',
                    'product_category': 'Категория товара',
                    'Название товара в срм': 'Названия товара',
                    'Себес $ (из срм)': 'Себестоимость $',
                    'Опт цена $ (себес + 25%)': 'Оптовая цена $',
                    'Кількість товару': 'Количество'
                })
                
                st.dataframe(second_table)  # Друга таблиця
                
            else:
                st.write("Нет данных для этого заказа")
        else:
            st.write("Нет данных для этой категории")
else:
    st.write("Загрузите данные для постройки таблиц")
