'''
Detects 'new' label on Artpole product image.
Requires input image 400x267 RGB
'new' label shall be rectangular, red and shall be located at [0:40, 14:40] pixels
'''
import numpy as np
from PIL import Image
import os


path = '../data/'
for filename in os.listdir(path):
    file = os.path.join(path, filename)
    if os.path.isfile(file):
        image = Image.open(file).resize((5, 14))
        image.show()
        
        im = np.array(image)
        dot = im[1,0]
        
        new = False
        if dot[0] > 180 and dot[1] < 100 and dot[2] < 100:
            new = True
        print(f'{filename=}, {im[1, 0]}, {new=}')
