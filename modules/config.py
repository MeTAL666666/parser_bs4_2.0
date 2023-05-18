import os
import sys
import ssl
import random
import re
import json
import time
import requests
import urllib
import urllib.parse
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
from requests.packages.urllib3.util import ssl_
from datetime import timedelta, datetime as dt
from random import randint

import winsound
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, abort
from colorama import Fore, Back, Style, init as colorama_init

from modules  import db_connection

# Необходимое шифрование для подключения к Avito
CIPHERS = """ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-SHA256:AES256-SHA"""
#Подключение к БД
connection, cursor = db_connection.main()
#Словарь для транслитерации населенных пунктов в Avito
translit_dict = {'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'yo',
      'ж':'zh','з':'z','и':'i','й':'i','к':'k','л':'l','м':'m','н':'n',
      'о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'h',
      'ц':'ts','ч':'ch','ш':'sh','щ':'sch','ъ':'','ы':'y','ь':'','э':'e',
      'ю':'u','я':'ya', 'А':'A','Б':'B','В':'V','Г':'G','Д':'D','Е':'E','Ё':'YO',
      'Ж':'ZH','З':'Z','И':'I','Й':'I','К':'K','Л':'L','М':'M','Н':'N',
      'О':'O','П':'P','Р':'R','С':'S','Т':'T','У':'U','Ф':'F','Х':'H',
      'Ц':'TS','Ч':'CH','Ш':'SH','Щ':'SCH','Ъ':'','Ы':'y','Ь':'','Э':'E',
      'Ю':'U','Я':'YA',',':'','?':'?',' ':'_','~':'','!':'','@':'','#':'',
      '$':'','%':'','^':'','&':'','*':'','(':'',')':'','-':'-','=':'','+':'',
      ':':'',';':'','<':'','>':'','\'':'','"':'','\\':'','/':'','№':'',
      '[':'',']':'','{':'','}':'','ґ':'','ї':'', 'є':'','Ґ':'g','Ї':'i',
      'Є':'e', '—':''}

colorama_init()

time_format = "%d/%m/%Y, %H:%M:%S"
delta = timedelta(days=1)

# HTTPS порты, которые исключены из выборки
port_not_use = (':80', ':81', ':443', ':3128', '8000', ':8080', ':8081', ':8888', ':9000')

# Директории файлов с прокси и юзер-агентами
files_dir = os.getcwd() + '/files'
temp_files_dir = os.getcwd() + '/files/temp'
'''Файлы, необходимые для работы ПО'''
config_file = files_dir + '/config.json'                            # конфиг-файл
proxies_file = files_dir + '/proxy_list.txt'                        # список прокси
proxies_database_file = files_dir + '/proxy_database.json'          # внутренняя БД прокси
user_agent_file = files_dir + '/user-agent_list.txt'                # файл с юзер-агентами
priority_file = temp_files_dir + '/priority_list.json'              # файл приоритетов использования прокси в базе
search_file_avito = temp_files_dir + '/search_info_avito.json'      # файл с поисковым запросом Avito
search_file_bazarpnz = temp_files_dir + '/search_info_bazarpnz.json'# файл с поисковым запросом Bazarpnz
stop_file = temp_files_dir + '/stop_function.json'                  # файл со стоп-функцией

proxy_worked = []		    # Прокси, проходящий проверку на работоспособность
user_agent_worked = []	# Выбранный случайным образом юзер-агент

'''Заголовки отправляемые парсером'''
# для Avito
headers = {
  'User-Agent': str(user_agent_worked),
  'origin': 'https://www.avito.ru',
	'accept': '*/*',
	'referer':'https://www.avito.ru',
	'connection':'keep-alive',
	'accept-language':'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
}
# для Bazarpnz
headers_bazarpnz = {
  'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0"}
'''Элементы для составления url'ов'''
correction = 'cd=1&' # с ноября 2022 появилось исправление опечаток на Avito
page_part = '&p='
query_part = '&q='
url_parse_proxy = 'https://webanetlabs.net/publ/30'

'''Класс для соединения с Avito'''
class TlsAdapter(HTTPAdapter):
    def __init__(self, ssl_options=0, **kwargs):
        self.ssl_options = ssl_options
        super(TlsAdapter, self).__init__(**kwargs)

    def init_poolmanager(self, *pool_args, **pool_kwargs):
        ctx = ssl_.create_urllib3_context(ciphers=CIPHERS, cert_reqs=ssl.CERT_REQUIRED, options=self.ssl_options)
        self.poolmanager = PoolManager(*pool_args, ssl_context=ctx, **pool_kwargs)