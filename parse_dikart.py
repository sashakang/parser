from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import pandas as pd
import re
import time
import sqlalchemy
from services import get_engine, send_mail, get_webdriver


brand = 'Дикарт'


def get_groups():
    driver.get('https://dikart.ru/catalog/')
    sections = driver.find_element(By.CLASS_NAME, 'content ')
    found = sections.find_elements(By.TAG_NAME, "li")
    
    groups = {}

    for group in found:
        try:
            link = group.find_element(By.TAG_NAME, 'a').get_attribute('href')
            name = group.find_element(By.TAG_NAME, 'span').text
            if len(name) > 0 and len(link) > 0:
                groups[name] = link
                print(f'{name}: {link}')
        except NoSuchElementException as e:
            pass
        
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
        'url',
        'unit_id'
    ])
    
    driver.get(group_url)

    timestamp = time.strftime('%Y-%d-%m %H:%M:%S', time.gmtime(time.time()))
    
    items = driver.find_elements(By.CLASS_NAME, 'product-item')

    for item in items:
        name = params = material = id = specs = url = None
        list_price = sale_price = discount = 0
        new = 0
        
        name = item.find_element(By.CLASS_NAME, 'title').text
        specs = item.find_element(By.CLASS_NAME, 'output_size').text
        list_price = item.find_element(By.CLASS_NAME, 'price').text
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
            'url': url,
            'unit_id': None
        })

        found_items.loc[len(found_items)] = new_record
            
    print(f'\nGot {len(found_items)} items from {group}')
    print(f'{timestamp}')
    
    return found_items


def clean_data(df):
    
    def get_unit(string) -> int:    
        '''
        returns int code of unit_id according to `units` table
        '''
        if string.lower().startswith('от '):
            return None
        if ' руб./п.м.' in string:
            return 0
        if ' руб./шт.' in string:
            return 1
        if ' руб./пар.' in string:
            return 2
        if ' руб./компл.' in string:
            return 4
        return None
        
    df.unit_id = df.list_price.apply(get_unit)
    
    def get_list_price(s) -> float:
        if s.lower().startswith('от'):
            return None
        
        price = re.match(r'\b(\d+)\sруб\.', s)
        if price:
            return int(price.groups()[0])
        
        return None 


    df.list_price = df.list_price.apply(get_list_price)
    
    
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
        
        if len(found) > 0:
            found = clean_data(found)

            print(f'\n=>  {engine=}')
            print(found.iloc[:5, :6])
            found_to_sql = found.to_sql(
                name='parsed_dev',
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
    log = {k: log[k] for k in sorted(log)}
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