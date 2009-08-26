Copy ImageConverter.py and DocumentConverter.py to the following directory: ~/OpenOffice/program/

Make sure Open Office is running with the following parameters:
 -accept=socket,host=localhost,port=8100;urp;

Add the following lines to the settings.py file
STATIC_DIR = 'C:/Projects/rooibos/rooibos/static/'
OPEN_OFFICE_PATH = 'C:/Program Files/OpenOffice.org 3/program/'