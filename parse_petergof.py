'''
TODO:
parse specs
- does Decimal really needed?
'''
from selenium.webdriver.common.by import By
import pandas as pd
import numpy as np
import time
import sqlalchemy
from services import get_engine, send_mail, get_webdriver
from decimal import *
setcontext(BasicContext)
D = Decimal

brand = 'Петергоф'
            

def get_groups(path: str = 'список для парсинга.xlsb'):
    
    driver.get('https://lepnina.ru/products/')
    
    found = driver.find_elements(By.CLASS_NAME, "card")
    
    groups = {}
    
    for group in found:
        name = group.find_element(By.CLASS_NAME, 'card__name').text
        url = group.get_attribute('href')
        groups[name] = url
        
    return groups
        
        
def get_group(group: str, group_url: str) -> pd.DataFrame:
    
    found_items = pd.DataFrame(columns=[
        'brand',
        'timestamp',
        'new',
        'cat',
        'name',
        'list_price',
        'discount',
        'sale_price',
        'id',
        'specs',
        'url'
    ])

    timestamp = time.strftime('%Y-%d-%m %H:%M:%S', time.gmtime(time.time()))
    
    driver.get(group_url)
    items = driver.find_elements(By.CLASS_NAME, 'card')
    
    for item in items:
        name = params = material = id = list_price = url = None
        discount = sale_price = new_record = None
        specs = ''
        
        name = item.find_element(By.CLASS_NAME, 'card__name').text.strip()
        
        if len(item.find_elements(By.CLASS_NAME, 'card_new_icon')) > 0:
            new = 1
        else:
            new = 0
            
        
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
                if specs == '':
                    specs = text
                else:
                    specs += ';' + text
            
        tags = item.find_elements(By.TAG_NAME, 'a')
        for tag in tags:
            if tag.get_attribute('name') == '': continue
            url = tag.get_attribute('href')
            id = tag.get_attribute('name')
            

        print(f'{name=}, {id=}, {material=}, {specs=}, {list_price=}, {url=}')

        new_record = pd.Series({
            'brand': brand,
            'timestamp': timestamp,
            'new': new,
            'cat': group,
            'name': name,
            'list_price': list_price,
            'discount': discount,
            'sale_price': sale_price,
            'id': id,
            'specs': specs,
            'url': url
        })

        found_items.loc[len(found_items)] = new_record
    
    print(f'\nGot {len(found_items)} items from {group}')
    print(f'{timestamp}')
        
    return found_items

if __name__ == '__main__':
    
    start = time.time()
    print(f'Getting groups from {brand}')
    send_mail(
        recipient='kan@dikart.ru', 
        subject=f'Starting parsing {brand}', 
        message=''
        )
        
    driver = get_webdriver()
    engine = get_engine(fname='../credentials/.server_analytics')
    
    groups = get_groups()
    for k, v in groups.items():
        print(k, v)
        
    result = pd.DataFrame(columns=[
        'brand', 
        'timestamp',
        'new',
        'cat',
        'name',
        'list_price',
        'discount',
        'sale_price',
        'id',
        'specs',
        'url'
    ])
        
    log = {}

    import random
    groups_list = list(groups.items())
    random.shuffle(groups_list)
    groups = {k: v for k, v in groups_list}
    
    for group, url in groups.items():
        # if group != 'Розетки': continue
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
        
    # print result
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
    timestamp = time.strftime('%d.%m.%y %H:%M:%S', time.gmtime(time.time())) 
    print(f'Completed at {timestamp}UTC in {elapsed_str} seconds.')
