'''
TODO:
parse specs
process pilasters, pillars, frames, portals, ceiling frames, panels, 
    наборные композиции, готовые решения subpages
add Dikart parsing for public representation
mail cron output
start the whole process with a single call
replace try-except with len(find_elements)
detect 'new' label in Artpole product images
chk error msgs in the output
regex the specs or the entire item data string
use ML to process data string?
automatically find matches using images and specsiptions
'''

from typing import List
from numpy import result_type
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import pandas as pd
import re
import time
import sqlalchemy
from services import get_engine, send_mail, get_webdriver


brand = 'Артполе'


def get_groups():
    driver.get('https://www.artpole.ru/catalog/lepnina.html')
    found = driver.find_elements(By.CLASS_NAME, "preview-new-td")
    
    groups = {}

    for group in found:
        text = group.text.split('\n')[0]
        link = group.find_element(By.TAG_NAME, "a").get_attribute('href')
        groups[text] = link
        
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
    
    driver.get(group_url)

    timestamp = time.strftime('%Y-%d-%m %H:%M:%S', time.gmtime(time.time()))
    
    items = driver.find_elements(By.CLASS_NAME, 'sostav-coll')
    if len(items) == 0:
        items = driver.find_elements(By.CLASS_NAME, 'preview-new-td')

    for item in items:
        name = params = material = id = specs = url = None
        list_price = sale_price = discount = 0
        new = 0
        
        try:
            name = item.find_element(By.CLASS_NAME, 'sostav-item-name').text
        except NoSuchElementException:
            name = item.find_element(By.CLASS_NAME, 'img-cat-lvl1').get_attribute('title')
            
        new_list = item.find_elements(By.CLASS_NAME, 'l-00')
        
        if len(new_list) > 0:
            src = new_list[0].get_attribute('src')
            if '_new.' in src:
                new = 1
            
        params = item.find_elements(By.CLASS_NAME, 'sostav-item-artikul-wr')
        
        for attr in params:
            txt = attr.text
            if "Материал" in txt:
                material = txt
            elif "Артикул" in txt:
                id = txt
        
        try:
            specs = item.find_element(By.CLASS_NAME, 'sostav-item-color-wr').text
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


def clean_data(df):
    
    df.list_price = df.list_price.apply(lambda v: 
        0 if v == 0 else int(''.join(re.findall('\d+', v))) if pd.notna(v) else 0)
    
    df.discount = df.discount.apply(lambda v: 
        0 if v == 0 else int(re.search('\d+', v)[0]) / 100 if pd.notna(v) else 0)

    df.sale_price = df.sale_price.apply(lambda v: 
        0 if v == 0 else int(''.join(re.findall('\d+', v))) if pd.notna(v) else 0)

    df.id = df.id.apply(lambda v: 
        v.replace('Артикул: ', '').strip() if pd.notna(v) else v)
    df.specs = df.specs.apply(lambda v: 
        v.replace('Размер: ', '').strip() if pd.notna(v) else v)
    df.specs = df.specs.apply(lambda v: 
        v.replace('мм', '').strip() if pd.notna(v) else v)
    
    def get_dimensions(series: pd.Series):
        '''
        Takes a `specs` string to parse.
        
        Returns a cortege:
        1. width in mm
        2. height in mm
        3. depth in mm
        4. diameter in mm
        5. weigth in g
        '''
        string = series[0]
        
        if not string or string == '': return [None, None, None, None, None ]
        
        pattern1 = re.compile('^(\d+)x(\d+)x(\d+)$')  # 100x80x40
        pattern2 = re.compile('^(\d+)x(\d+)$')    # 120x120
        pattern3 = re.compile('^D(\d+)$')         # D100
        pattern4 = re.compile('^D(\d+)x(\d+)$')   # D1000x100
        pattern5 = re.compile('^D(\d+)x(\d+)x(\d+)$')   # D1000x500x100
        pattern6 = re.compile('^H(\d+)x(\d+)$')   # H500x100
        pattern7 = re.compile('^H(\d+)x(\d+)x(\d+)$')   # H500x100x20
        
        result = re.match(pattern1, string)
        if result:
            groups = result.groups()
            return [int(groups[0]), int(groups[1]), int(groups[2]), None, None]
        
        result = re.match(pattern2, string)
        if result:
            groups = result.groups()
            return [int(groups[0]), int(groups[1]), None, None, None]
        
        result = re.match(pattern3, string)
        if result:
            groups = result.groups()
            return [None, None, None, int(groups[0]), None]
        
        result = re.match(pattern4, string)
        if result:
            groups = result.groups()
            return [None, None, int(groups[1]), int(groups[0]), None]
        
        result = re.match(pattern5, string)
        if result:
            groups = result.groups()
            width = max(int(groups[1]), int(groups[0]))
            height = min(int(groups[1]), int(groups[0]))
            depth = int(groups[2])
            return [width, height, depth, None, None]

        result = re.match(pattern6, string)
        if result:
            groups = result.groups()
            return [None, int(groups[0]), int(groups[1]), None, None]
        
        result = re.match(pattern7, string)
        if result:
            groups = result.groups()
            return [int(groups[1]), int(groups[0]), int(groups[2]), None, None]
        
        print(f'Not recognized {string=}')
        return [None, None, None, None, None]
        
    df[['width_mm', 'height_mm', 'depth_mm', 'diameter_mm', 'weight_g']] = \
        df[['specs']].apply(get_dimensions, axis=1, result_type='expand')
    
    return df
    

if __name__ == "__main__":
    print('Starting v.0.2')
    start = time.time()

    print(f'Getting groups from {brand}')
    send_mail(
        recipient='kan@dikart.ru', 
        subject=f'Starting parsing {brand}', 
        message=''
        )
    
    engine = get_engine(fname='../credentials/.server_analytics')
    driver = get_webdriver()
    
    groups = get_groups()
    for group, url in groups.items():
        print(f'{group}: {url}')
        
    import random
    groups_list = list(groups.items())
    random.shuffle(groups_list)
    groups = {k: v for k, v in groups_list}
    
    log = {}

    for group, group_url in groups.items():
        # if group != 'Карнизы гладкие' : continue
        print('\n', '>'*20, 'Getting', group, '<'*20)
        found = get_group(group, group_url)
        
        found = clean_data(found)

        print(f'\n=>  {engine=}')
        print(found.iloc[:5, :6])
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
        
    # print result
    msg = f'***PARSED {brand}***\n'
    print('*' * 15, 'PARSED', brand, '*' * 16)
    for group, count in log.items():
        print(f'{group}: {count}')
        msg += f'{group}: {count}\n'
    print('*' * 40)
    msg += '***END***'
    
    elapsed_time = time.time() - start
    elapsed_str = time.strftime('%H:%M:%S', time.gmtime(elapsed_time))
    timestamp = time.strftime('%d.%m.%y %H:%M:%S', time.gmtime(time.time())) 
    print(f'Completed at {timestamp}UTC in {elapsed_str} seconds.')
 
    send_mail(
        recipient='kan@dikart.ru', 
        subject=f'Parsed {brand}', 
        message=msg
        )