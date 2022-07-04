# from operator import index
# from os import times
# from this import d
# from unicodedata import name
# from webbrowser import get
from selenium import webdriver
# from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import pandas as pd
import numpy as np
# import re
# import openpyxl
import time

import sqlalchemy
from parse_artpole import get_groups_list
# import pyodbc
from services import get_engine, send_mail
from datetime import datetime as dt
from datetime import timedelta

from decimal import *
setcontext(BasicContext)
D = Decimal

expiration_period = timedelta(minutes=1)
brand = 'Петергоф'
            

def get_groups(path: str = 'список для парсинга.xlsb'):
    
    sections = get_groups_list(filter=brand)

    # System.setProperty("webdriver.chrome.driver", "C:\\path\\to\\chromedriver.exe");
    options = webdriver.ChromeOptions() 
    options.add_argument("--headless")
    # options.add_argument("start-maximized")    # open Browser in maximized mode
    # options.add_argument("disable-infobars")   # disabling infobars
    # options.add_argument("--disable-extensions")   # disabling extensions
    # options.add_argument("--disable-gpu")  # applicable to windows os only
    # options.add_argument("--disable-dev-shm-usage")    # overcome limited resource problems
    options.add_argument("--no-sandbox")   # Bypass OS security model
    options.add_argument("--disable-setuid-sandbox")
    driver = webdriver.Chrome(options=options)
    
    driver.get('https://lepnina.ru/products/')
    
    found = driver.find_elements(By.CLASS_NAME, "card")
    
    groups = {}
    
    for group in found:
        name = group.find_element(By.CLASS_NAME, 'card__name').text
        url = group.get_attribute('href')
        if name in sections:
            groups[name] = url
        
    return groups
        
        
def get_group(group: str, group_url: str) -> pd.DataFrame:
    
    found_items = pd.DataFrame(columns=[
        'brand',
        'timestamp',
        'cat',
        'name',
        'list_price',
        'discount',
        'sale_price',
        'id',
        'dimensions',
        'url'
    ])
    
    options = webdriver.ChromeOptions() 
    options.add_argument("--headless")
    # options.add_argument("start-maximized")    # open Browser in maximized mode
    options.add_argument("disable-infobars")   # disabling infobars
    options.add_argument("--disable-extensions")   # disabling extensions
    options.add_argument("--disable-gpu")  # applicable to windows os only
    options.add_argument("--disable-dev-shm-usage")    # overcome limited resource problems
    options.add_argument("--no-sandbox")   # Bypass OS security model 
    options.add_argument("--disable-setuid-sandbox")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(1)
    driver.get(group_url)
    timestamp = dt.now().strftime('%Y-%m-%d %H:%M:%S')

    items = driver.find_elements(By.CLASS_NAME, 'card')
    
    for item in items:
        name = params = material = id = list_price = url = None
        discount = sale_price = new_record = None
        dimensions = ''
        
        name = item.find_element(By.CLASS_NAME, 'card__name').text.strip()
        
        params = item.find_element(By.CLASS_NAME, 'params-item')
        rows = params.find_elements(By.TAG_NAME, 'tr')
        
        for row in rows:
            text = row.text
            if text.startswith('Цена'):
                try:
                    list_price = D(text.replace('Цена ', '').replace(' р.', ''))\
                        .quantize(D('0.01'), rounding=ROUND_HALF_UP)
                except (ValueError, InvalidOperation):
                    list_price = np.nan
            else:
                if dimensions == '':
                    dimensions = text
                else:
                    dimensions += ';' + text
            
        tags = item.find_elements(By.TAG_NAME, 'a')
        for tag in tags:
            if tag.get_attribute('name') == '': continue
            url = tag.get_attribute('href')
            id = tag.get_attribute('name')
            

        print(f'{name=}, {id=}, {material=}, {dimensions=}, {list_price=}, {url=}')

        new_record = pd.Series({
            'brand': brand,
            'timestamp': timestamp,
            'cat': group,
            'name': name,
            'list_price': list_price,
            'discount': discount,
            'sale_price': sale_price,
            'id': id,
            'dimensions': dimensions,
            'url': url
        })

        found_items.loc[len(found_items)] = new_record
        
    return found_items

if __name__ == '__main__':
    # import os
    # print(f'{os.getcwd()=}')
    # print(f'{os.listdir()=}')
    # time.sleep(60)
    
    start = time.time()
    print(f'Getting groups from {brand}')
    
    if True:
        
        groups = get_groups()
        for k, v in groups.items():
            print(k, v)
            
        result = pd.DataFrame(columns=[
            'brand', 
            'timestamp',
            'cat',
            'name',
            'list_price',
            'discount',
            'sale_price',
            'id',
            'dimensions',
            'url'
        ])
            
        log = {}
        
        engine = get_engine(fname='.server_analytics', db='PROD_ANALYTICS')
        
        import random
        groups_list = list(groups.items())
        random.shuffle(groups_list)
        groups = {k: v for k, v in groups_list}
        
        for group, url in groups.items():
            # if group != 'Купола': continue
            print('\n', '>'*15, 'Getting', group, '<'*15)
            found = get_group(group, url)
            
            log[group] = len(found)
            
            print(f'\n=>  {engine=}')
        
            found.to_sql(
                name='parsed',
                con=engine,
                if_exists='append',
                index=False,
                dtype={
                    'timestamp': sqlalchemy.DateTime,
                    'list_price': sqlalchemy.Numeric,
                    'discount': sqlalchemy.Float,
                    'sale_price': sqlalchemy.Numeric
                }
            )
            
            result = pd.concat([result, found], ignore_index=True)

        msg = f'***PARSED {brand}***\n'
        print('*' * 15, 'PARSED', brand, '*' * 16)
        for group, count in log.items():
            print(f'{group}: {count}')
            msg += f'{group}: {count}\n'
        print('*' * 40)
        msg += '***END***'
        
        send_mail(recipient='kan@dikart.ru', subject=f'Parsed {brand}', message=msg)
        
        elapsed_time = time.time() - start
        elapsed_str = time.strftime('%H:%M:%S', time.gmtime(elapsed_time))
        print(f'Completed in {elapsed_str} seconds.')
        
        # writer = pd.ExcelWriter('found_items.xlsx', engine = 'openpyxl')
        # result.to_excel(writer, sheet_name=brand, index=False)
        # writer.