import requests
import pandas as pd
from datetime import datetime
from time import time
import asyncio
import aiohttp

res = pd.read_csv('data/res.csv')

async def fetch_data(api_key):
    url = 'https://uzshopping.retailcrm.ru/api/v5/orders'
    current_date = datetime.now().date()
    date = current_date.strftime('%Y-%m-%d')
    params = {
        'apiKey': api_key,
        'filter[createdAtFrom]': '2024-08-01',
        'filter[createdAtTo]': '2024-08-01',
    }

    async with aiohttp.ClientSession() as session:
        async def fetch_page(page):
            params_with_page = {**params, 'page': page}
            async with session.get(url, params=params_with_page) as response:
                return await response.json()

        initial_response = await fetch_page(1)
        total_pages = initial_response['pagination']['totalPageCount']

        tasks = [fetch_page(page) for page in range(1, total_pages + 1)]
        pages_data = await asyncio.gather(*tasks)

    # Створення DataFrame
    df = pd.DataFrame(range(total_pages), columns=['p']).assign(st=0., en=0., t=None, r=None)

    def parse_page_data(page_data):
        if page_data['success']:
            return page_data['data']['orders']
        return []

    orders_data = [parse_page_data(page_data) for page_data in pages_data]
    df1 = pd.json_normalize({'data': [order for sublist in orders_data for order in sublist]}, record_path=['data', 'orders'], max_level=0)

    mask = ['number', 'status', 'customFields', 'items']
    df2 = df1[mask]

    def get_item_data(items, key):
        data = []
        for item in items:
            if isinstance(item, dict) and 'offer' in item and key in item['offer']:
                data.append(item['offer'][key])
            else:
                data.append(None)
        return data

    df_items_expanded = df2.explode('items')

    df_items_expanded['price'] = df_items_expanded['items'].apply(lambda x: x['prices'][0]['price'] if isinstance(x, dict) and 'prices' in x and x['prices'] else None)
    df_items_expanded['quantity'] = df_items_expanded['items'].apply(lambda x: x['prices'][0]['quantity'] if isinstance(x, dict) and 'prices' in x and x['prices'] else None)
    df_items_expanded['externalId'] = df_items_expanded['items'].apply(lambda x: get_item_data([x], 'externalId')[0] if isinstance(x, dict) else None)
    df_items_expanded['name'] = df_items_expanded['items'].apply(lambda x: x['offer']['name'] if isinstance(x, dict) and 'offer' in x and 'name' in x['offer'] else None)
    df_items_expanded['item_buyer_id'] = df_items_expanded.apply(lambda x: x['customFields']['buyer_id'] if 'buyer_id' in x['customFields'] else None, axis=1)
    df_items_expanded['item_offer_id'] = df_items_expanded.apply(lambda x: x['customFields']['offer_id'] if 'offer_id' in x['customFields'] else None, axis=1)

    df_items_expanded = df_items_expanded.rename(columns={'number': 'Номер замовлення',
                      'status': 'Статус',
                      'externalId': 'Product_id',
                      'name': 'Назва товару',
                      'quantity': 'Кількість товару',
                      'price': 'Ціна товару',
                      'item_offer_id': 'offer_id(заказа)',
                      'item_buyer_id': 'buyer_id'})

    df_items_expanded.drop(['customFields', 'items'], axis=1, inplace=True)
    
    df = df_items_expanded

    df.dropna(subset=['Product_id'], inplace=True)
    df.dropna(subset=['buyer_id'], inplace=True)
    df['offer_id(товара)'] = df['Product_id'].apply(lambda x: '-'.join(x.split('-')[:3]))
    df['Загальна сума'] = df['Ціна товару'] * df['Кількість товару']

    desired_column_order = ['Номер замовлення', 'Статус', 'offer_id(товара)', 'Product_id', 'Назва товару', 'Кількість товару', 'Ціна товару', 'Загальна сума', 'offer_id(заказа)', 'buyer_id']
    df = df.reindex(columns=desired_column_order)

    df = df[~df['Назва товару'].str.contains('оставка')]

    def define_category(group):
        # Перевіряємо всі товари в замовленні на наявність 'ss' або 'tv' в 'offer_id(товара)'
        for index, row in group.iterrows():
            offer_id = row['offer_id(товара)']
            item_name = row['Назва товару']
            
            # Якщо є доставка в назві товару
            if 'оставка' in item_name:
                group.loc[index, 'order_category'] = 'delivery'
            # Перевіряємо, чи починається 'offer_id(товара)' з 'ss'
            elif offer_id.startswith('ss'):
                group.loc[index, 'order_category'] = 'ss'
            # Перевіряємо, чи починається 'offer_id(товара)' з 'tv'
            elif offer_id.startswith('tv'):
                group.loc[index, 'order_category'] = 'tv'
            # Якщо не 'ss' і не 'tv', призначаємо категорію 'timur'
            else:
                group.loc[index, 'order_category'] = 'timur'

        return group

    orders = df.groupby('Номер замовлення').apply(define_category)
    df_before = orders.merge(res, left_on='offer_id(заказа)', right_on='offer_article', how='left')
    df_before = df_before.rename(columns={'offer_purchasePrice': 'Себес $ (из срм)'})
    df_before['Опт цена $ (себес + 25%)'] = (df_before['Себес $ (из срм)'] * 1.25).round(2)
    
    return df_before
