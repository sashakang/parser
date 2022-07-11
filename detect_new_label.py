from http.client import responses
import numpy as np
from PIL import Image
import requests
from io import BytesIO
import os


def is_new(
    filepath: os.path = None, 
    img_url: str = None,    # TODO: change to pydantic.HttpUrl
    image_show: bool = False,
    verbose: bool = False
) -> bool:
    """
    Args:
        filepath (os.path, optional). Defaults to None.
        img_url (str, optional). Defaults to None.
        image_show (bool, optional). Defaults to False. Opens image in system 
            default image viewer.
        verbose (bool, optional). Defaults to False. Prints log to console.

    Returns:
        bool or None if both 'filepath' and 'url' are 'None'
    
    Detects 'new' label on Artpole product image.
    Requires input image 400x267 RGB.
    'new' label shall be rectangular, mostly red and shall be located at 
    [0:40, 14:40] pixels.
    """
    
    if filepath:
        image = Image.open(filepath).resize((5, 14))
    elif img_url:
        response = requests.get(img_url)
        image = Image.open(BytesIO(response.content)).resize((5, 14))
    else:
        return None
    
    if image_show:
        image.show()
            
    im = np.array(image)
    dot = im[1,0]
            
    is_new = False
    if dot[0] > 180 and dot[1] < 100 and dot[2] < 100:
        is_new = True
        
    if verbose:
        if filepath:
            print(f'{filepath=}, dot={im[1, 0]}, {is_new=}')
        elif img_url:
            print(f'{img_url=}\ndot={im[1, 0]}, {is_new=}')
    
    return is_new


if __name__ == '__main__':
    path = '../data/'
    responses = {
        'SKT4.jpg': False,
        'SKT3.jpg': False,
        'SKT2.jpg': False,
        'SKT1.jpg': False,
        'SKT190_S_new.jpg': True,
        'SKT222_S_new.jpg': True,
        'SKT215_S_new.jpg': True,
        'SKT173_S_new.jpg': True
    }
    for filename, correct_response in responses.items():
        filepath = os.path.join(path, filename)
        response = is_new(filepath=filepath, verbose=True)
        assert response is correct_response, 'Wrong response with {filename}'
            
    prefix = 'https://www.artpole.ru/upload/resize_cache/iblock/'
    urls = [
        prefix + 'acb/400_267_10d47edb054265cd29312e6ab6781ce40/SK139_s_new.png',
        prefix + '04c/400_267_10d47edb054265cd29312e6ab6781ce40/SK140_S_new.png',
        prefix + '903/400_267_10d47edb054265cd29312e6ab6781ce40/SK23_S.png',
        prefix + '942/400_267_10d47edb054265cd29312e6ab6781ce40/S3K4.png'
    ]
    responses = [True, True, False, False]
    for url, correct_response in zip(urls, responses):
        response = is_new(img_url=url, image_show=False, verbose=True)
        assert response is correct_response, 'Wrong response'