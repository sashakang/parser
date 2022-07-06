'''
TODO:
run on Linux
refactor
remove credentials
'''

# from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import pandas as pd
import re
import time
# from datetime import datetime as dt
import sqlalchemy
from services import get_engine, send_mail, get_webdriver


brand = 'Артполе'


def get_groups(path: str = 'список для парсинга.xlsb'):
    
    attempt_no = 0
    while True:
        print(f'{attempt_no=}')
        attempt_no += 1
        driver = get_webdriver()
        time.sleep(2)
        
        try:
            driver.get('https://www.artpole.ru/catalog/lepnina.html')
            
            time.sleep(1)
            
            found = driver.find_elements(By.CLASS_NAME, "preview-new-td")
            
            groups = {}

            for group in found:
                text = group.text.split('\n')[0]
                # print(text, sep='\n')
        
                link = group.find_element(By.TAG_NAME, "a").get_attribute('href')
                
                groups[text] = link
                
            break
        
        except Exception as e:
            print(e)
        # print(link)
    
    driver.quit()
        
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
    
    attempt_no = 0
    
    while True:     # TODO: limit number of retries
        print(f'{attempt_no=}')
        attempt_no += 1
        print(f'{group=}, {group_url=}')
        
        try:
            driver = get_webdriver()
            time.sleep(2)
            driver.get(group_url)

            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()))
            time.sleep(1)
            
            items = driver.find_elements(By.CLASS_NAME, 'sostav-coll')
            if len(items) == 0:
                items = driver.find_elements(By.CLASS_NAME, 'preview-new-td')
        
            for item in items:
                name = params = material = id = dimensions = url = None
                list_price = sale_price = discount = 0
                try:
                    name = item.find_element(By.CLASS_NAME, 'sostav-item-name').text
                except NoSuchElementException:
                    name = item.find_element(By.CLASS_NAME, 'img-cat-lvl1').get_attribute('title')
                    
                params = item.find_elements(By.CLASS_NAME, 'sostav-item-artikul-wr')
                
                for attr in params:
                    txt = attr.text
                    if "Материал" in txt:
                        material = txt
                    elif "Артикул" in txt:
                        id = txt
                
                try:
                    dimensions = item.find_element(By.CLASS_NAME, 'sostav-item-color-wr').text
                except NoSuchElementException:
                    pass
                    
                try:
                    list_price = item.find_element(By.CLASS_NAME, 'pp2').text
                except NoSuchElementException:
                    for val in item.find_elements(By.CLASS_NAME, 'pp'):
                        txt = val.text
                        if 'Старая цена: ' in txt:
                            list_price = txt
                        elif 'Новая цена: ' in txt:
                            sale_price = txt
                        elif 'Скидка: ' in txt:
                            discount = txt
                    
                url = item.find_element(By.TAG_NAME, 'a').get_attribute('href')
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
                
            driver.quit()    
            
            print(f'\nGot {len(found_items)} items from {group} in {attempt_no} attempts')
            print(f'{timestamp}')
            
            return found_items
    
        except Exception as e: 
            print(f'{e=}')
            driver.quit()


def clean_data(df):
    df.list_price = df.list_price.apply(lambda v: 
        0 if v == 0 else int(''.join(re.findall('\d+', v))) if pd.notna(v) else 0)
    
    df.discount = df.discount.apply(lambda v: 
        0 if v == 0 else int(re.search('\d+', v)[0]) / 100 if pd.notna(v) else 0)

    df.sale_price = df.sale_price.apply(lambda v: 
        0 if v == 0 else int(''.join(re.findall('\d+', v))) if pd.notna(v) else 0)

    df.id = df.id.apply(lambda v: 
        v.replace('Артикул: ', '').strip() if pd.notna(v) else v)
    df.dimensions = df.dimensions.apply(lambda v: 
        v.replace('Размер: ', '').strip() if pd.notna(v) else v)
    df.dimensions = df.dimensions.apply(lambda v: 
        v.replace('мм', '').strip() if pd.notna(v) else v)
    
    return df
    

if __name__ == "__main__":
    start = time.time()

    print(f'Getting groups from {brand}')
    groups = get_groups()
    for group, url in groups.items():
        print(f'{group}: {url}')
        
    import random
    groups_list = list(groups.items())
    random.shuffle(groups_list)
    groups = {k: v for k, v in groups_list}
    
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

    engine = get_engine(fname='.server_analytics')
    
    for group, group_url in groups.items():
        # if not group.startswith('Розетки') : continue
        print('\n', '>'*20, 'Getting', group, '<'*20)
        found = get_group(group, group_url)
        
        found = clean_data(found)

        print(f'\n=>  {engine=}')
        print(found.head())
        found_to_sql = found.to_sql(
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
        print(f'{found_to_sql=}')       
        
        log[group] = len(found)
        result = pd.concat([result, found], ignore_index=True)
        
    msg = f'***PARSED {brand}***\n'
    print('*' * 15, 'PARSED', brand, '*' * 16)
    for group, count in log.items():
        print(f'{group}: {count}')
        msg += f'{group}: {count}\n'
    print('*' * 40)
    msg += '***END***'
    
    elapsed_time = time.time() - start
    elapsed_str = time.strftime('%H:%M:%S', time.gmtime(elapsed_time))
    print(f'Completed in {elapsed_str} seconds.')
 
    send_mail(recipient='kan@dikart.ru', subject=f'Parsed {brand}', message=msg)
        
    # result.to_excel('found_items.xlsx', sheet_name='Артполе',               