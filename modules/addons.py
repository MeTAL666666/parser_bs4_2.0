from modules.config import *
'''
Описание функций:

work_with_json() - функция для работы с файлами json. Принимает аргумент, в зависимости из которого вызывается внутренняя функция
	create_config_file() - создание конфиг-файла с параметрами по умолчанию
	check_config_file() - проверка конфиг-файла на целостность (запускается при каждом запуске ПО)
	create_proxy_database_structure() - создание внутренней БД для распределения использовавашихся ранее прокси-серверах

work_with_exceptions() - функция для обработки исключений
	search_proxy_in_json_lists - поиск текущего прокси в списках уже использовавшихся (для исключения одинаковых прокси в БД)

check_proxy() - функция для проверки прокси на работоспособноть

write_to_json() - функция для записи в json
write_to_db() - функция для записи в БД
'''

#Звуковой сигнал успешного выполнения программы
def end_sound():
      winsound.PlaySound('SystemAsterisk', winsound.SND_ALIAS)

def work_with_json(param = None):
	# Функция создаёт конфиг-файл по запросу программы
	def create_config_file():
		config_structure = {'last_launch_parser_proxy': dt.strftime(dt.now() - delta, time_format),
							'use_proxy': False,
							'start_page': 1,
							'use_json_base': False,
							'looped_program': False		#возможность зациклить программу пока не спарсятся все объявления
							}

		if not os.path.exists(config_file):
			if not os.path.exists(files_dir):
				os.mkdir(files_dir)
			write_to_json(config_file, config_structure)
			print('В каталоге "files" создан файл:', config_file.split('/')[-1])
		# Проверка конфиг-файла на целостность
		def check_config_file():
			try:
				data = json.load(open(config_file))
				last_launch = data['last_launch_parser_proxy'].split('.')[0]
				last_launch = dt.strptime(last_launch, time_format)
				use_proxy = data['use_proxy']
				start_page = data['start_page']
				use_json_base = data['use_json_base']
				looped_program = data['looped_program']
				
				assert isinstance (start_page, int),'"start_page" не является числом'
				assert isinstance (use_proxy, bool),'"use_proxy" не является булевым значением'
				assert isinstance (use_json_base, bool),'"use_json_base" не является булевым значением'
				assert isinstance (looped_program, bool),'"looped_program" не является булевым значением'

				if start_page != 1:
					data['start_page'] = 1
					write_to_json(config_file, data)	
			except (json.decoder.JSONDecodeError, KeyError, ValueError, AssertionError):
				print('Файл', config_file.split('/')[-1], 'поврежден! Структура сброшена.')
				time.sleep(1)
				write_to_json(config_file, config_structure)
		
		check_config_file()
	# Создание дефолтной структуры БД по запросу программы
	def create_proxy_database_structure():
		proxy_database_structure = {'ok': [],
					'blocked': [],
					'connection_error': [],
					'failed': []
					}

		if not os.path.exists(proxies_database_file):
			write_to_json(proxies_database_file, proxy_database_structure)
			
			data = json.load(open(config_file))
			data['use_json_base'] = False
			write_to_json(config_file, data)

			print('В каталоге "files" создан файл:', proxies_database_file.split('/')[-1])

		while True:
			try:
				data_json = json.load(open(proxies_database_file))

				proxy_ok = [d for d in data_json['ok']]
				proxy_blocked = [d for d in data_json['blocked']]
				proxy_con_err = [d for d in data_json['connection_error']]
				proxy_failed = [d for d in data_json['failed']]

			except (json.decoder.JSONDecodeError, KeyError):
				print('Файл', proxies_database_file.split('/')[-1], 'поврежден! Структура сброшена.')
				if os.path.exists(priority_file):
					os.remove(priority_file)
				time.sleep(1)
				write_to_json(proxies_database_file,proxy_database_structure)
				continue
			break
		return (proxy_ok, proxy_blocked, proxy_con_err, proxy_failed)
	
	if param == 'create_config_file':
		return create_config_file()
	else:
		return create_proxy_database_structure()

# В зависимоти от исключений, распределение прокси по спискам
def work_with_exceptions(proxy_worked, proxy_sorted, sublist_name=None, use_base=False):
	def search_proxy_in_json_lists(list_name, param):
		# Функция для проверки текущего прокси в других списках
		def in_other_sublists():
			set_of_sublists = set(proxy_sorted.keys())
			set_of_sublists.discard(list_name)	

			proxies_in_other_sublists = []
			for sublist in set_of_sublists:
				for proxy in proxy_sorted[sublist]:
					if proxy_worked == proxy['ip:port']:
						proxies_in_other_sublists.append([sublist, proxy_worked, proxy['attempts'], proxy['success']])
			return proxies_in_other_sublists
		# Функция для проверки текущего прокси в текущем списке (для обновления данных)
		def in_current_sublist():
			if proxy_worked not in [proxy.get('ip:port', None) for proxy in proxy_sorted[list_name]]:
				return False
			else:
				proxies_in_current_sublist = []
				for proxy in proxy_sorted[list_name]:
					if proxy_worked == proxy['ip:port']:
						proxies_in_current_sublist.append([list_name, proxy_worked, proxy['attempts'], proxy['success']])
			return proxies_in_current_sublist
		
		if param == 'other_sublists':
			return in_other_sublists()
		if param == 'current_sublist':
			return in_current_sublist()
	# Общая функция для обработки списков
	def sublist_processing():
		flag = False
		if search_proxy_in_json_lists(sublist_name, 'current_sublist') == False:
			for sublist, proxy, attempts, success in search_proxy_in_json_lists(sublist_name, 'other_sublists'):
				delete_from_list(sublist, proxy)
				append_to_list(sublist_name, proxy_worked,attempts=attempts, success=success)	
				flag = True
		else:
			for sublist, proxy, attempts, success in search_proxy_in_json_lists(sublist_name, 'current_sublist'):
				append_to_list(sublist_name, proxy_worked, update = 'Yes', attempts=attempts, success=success)
				flag = True
		if flag != True:
			append_to_list(sublist_name, proxy_worked)

	def ok():
		sublist_processing()	
		# Запись в JSON структуры со списками
		write_to_json(proxies_database_file, proxy_sorted)

	def blocked():
		sublist_processing()
		# Запись в JSON структуры со списками
		write_to_json(proxies_database_file, proxy_sorted)

		print ('Сайт блокирует этот прокси, подбираю следующий...\n', end='')
		#os.execl(sys.executable, sys.executable, *sys.argv)			# Перезапуск программы

	def connection_error():
		sublist_processing()
		# Запись в JSON структуры со списками
		write_to_json(proxies_database_file, proxy_sorted)

		print('\nСоединение было сброшено...\n', end='')						# ТЕСТОВОЕ СООБЩЕНИЕ
		#os.execl(sys.executable, sys.executable, *sys.argv)	# Перезапуск программы
		
	def failed():
		#print ([p_f.get('ip:port', None) for p_f in proxy_sublist])
		#print(proxy_sublist)
		sublist_processing()

		write_to_json(proxies_database_file, proxy_sorted)

		print(Back.RED + 'Ошибка подключения к ' + proxy_worked, end = '')
		print(Style.RESET_ALL)
	# Функция для обработки пустого файла 'proxies_list.txt'
	def empty_proxy_file():
		with open(proxies_file, 'r') as p_f:
			empty_proxy_file = []
			for p in p_f:
				sub_str = re.sub(r'\s', ":", p)							# Меняем все пробелы на двоеточия
				proxy = re.match('(\d+\.\d+\.\d+\.\d+\:\d+)', sub_str)	# Ищем в начале строки шаблон
				
				if proxy != None:
					proxy = proxy.group(1)	
					empty_proxy_file.append(proxy)

		if len(empty_proxy_file) == 0:
			print('Файл', proxies_file.split('/')[-1], 'не содержит прокси!')
			os.remove(proxies_file)
			with open (proxies_file, 'w') as p_f:
				pass
			return 0
		else:
			print('\nСписок прокси-серверов закончился.')
			return 1	
	# Добавление в список
	def append_to_list(proxy_sublist, proxy_worked, update=None, attempts=0, success=0):
		if update == None:
			if proxy_sublist == 'ok':
				success += 1
			proxy_sorted[proxy_sublist].append({'ip:port': proxy_worked,
									'last_use': dt.strftime(dt.now(), time_format),
									'attempts': attempts + 1,
									'success': success
									})
		else:
			if proxy_sublist == 'ok':
				success += 1

			for index, dict_ in enumerate(proxy_sorted[proxy_sublist]):
				if 'ip:port' in dict_ and dict_['ip:port'] == proxy_worked:
					#attempt = int(dict_['attempt'])
					#success = int(dict_['success'])
					proxy_sorted[proxy_sublist][index] = {'ip:port': proxy_worked,
										'last_use': dt.strftime(dt.now(), time_format),
										'last_use1': dt.strftime(dt.now() - delta, time_format),
										'attempts': attempts + 1,
										'success': success
										}
	# Добавление из списка список
	def delete_from_list(proxy_sublist, proxy_worked):
		#print (proxy_sorted[proxy_sublist], proxy_worked)
		for index, dict_ in enumerate(proxy_sorted[proxy_sublist]):
			if 'ip:port' in dict_ and dict_['ip:port'] == proxy_worked:
				del proxy_sorted[proxy_sublist][index]

	if sublist_name == 'ok':
		ok()
	if sublist_name == 'blocked':
		blocked()
	if sublist_name == 'connection_error':
		connection_error()	
	if sublist_name == 'failed':
		failed()
	if sublist_name == 'empty_proxy_file':
		return empty_proxy_file()

# Функция проверки прокси на работоспособность
def check_proxy(proxy_sorted, use_base=None, base_list=None):
	# когда программа не использует свою БД
	def not_use_json_base():
		if not os.path.exists(proxies_file):
			with open (proxies_file, 'w') as p_f:
				pass
			print('В каталоге "files" создан файл:', proxies_file.split('/')[-1])
		
		proxies_list = []
		with open(proxies_file, 'r') as p_f:							# Открываем .txt-файл с прокси
			for p in p_f:
				sub_str = re.sub(r'\s', ":", p)							# Меняем все пробелы на двоеточия
				proxy = re.match('(\d+\.\d+\.\d+\.\d+\:\d+)', sub_str)	# Ищем в начале строки шаблон
			
				if proxy != None:				# Необходимое условие, чтобы работала группировка
					proxy = proxy.group(1)		# Группируем найденные значения построчно
					proxies_list.append(proxy)
				else:
					continue

		for proxy in proxies_list:

			# Если прокси есть в списках неработающих - пропускаем его	
			proxy_failed = [sublist_name for sublist_name in proxy_sorted['failed']]
			proxy_blocked = [sublist_name for sublist_name in proxy_sorted['blocked']]
			proxy_con_err = [sublist_name for sublist_name in proxy_sorted['connection_error']]

			if proxy in [p_f.get('ip:port', None) for p_f in proxy_failed]:		
				continue
			elif proxy in [p_b.get('ip:port', None) for p_b in proxy_blocked]:		
				continue
			elif proxy in [p_e.get('ip:port', None) for p_e in proxy_con_err]:		
				continue
			print(f'\nПроверяю прокси: {proxy}\t#{str(proxies_list.index(proxy) + 1)}/{len(proxies_list)}')

			# Проверка прокси на работоспособность с помощью запроса к 2ip.ru
			try:
				response = requests.get('https://2ip.ru',timeout=(10,10),
					 headers=headers, proxies={'https':'socks4://' + proxy})
			# Если ошибка - добавляем прокси в список proxy_failed и переходим к следующему прокси
			except OSError:
				work_with_exceptions(proxy, proxy_sorted, 'failed')
				continue

			if response.status_code == requests.codes['ok']:					# Если статус запроса 200
				select_ip = re.search('(\d+\.\d+\.\d+\.\d+)', response.text)	# в ответе ищем шаблон (IP-адрес)
				if select_ip != None:											# группируем результат поиска
					select_ip = select_ip.group(1)
				print(Back.GREEN + 'OK! Установлен IP-адрес: ' + str(select_ip), end='')
				print(Style.RESET_ALL)
				time.sleep(1)
				proxy_worked.append(proxy)
				print (str(user_agent_worked[0]), end='')		# Вывод выбранного юзер-агента на экран
				time.sleep(1)									# добавляем в список рабочий прокси
				break											# Выходим из цикла
		return proxy
	# когда программа использует свою БД
	def use_json_base():
		for index, proxy_info in base_list.items():
			proxy = proxy_info[0]
			priority = proxy_info[1]

			print(f'\nПроверяю прокси: {proxy}\t#{str(index)}/{max([int(i) for i in base_list.keys()])} ' + 
				Back.BLUE + Fore.WHITE + '[DATABASE]' + Style.RESET_ALL + ' ' +
				Back.BLUE + Fore.WHITE + '[' + priority + ']' + Style.RESET_ALL)

			data = json.load(open(priority_file))
			data['last_index'] = index
			write_to_json(priority_file, data)
			# Проверка прокси на работоспособность с помощью запроса к 2ip.ru
			try:
				response = requests.get('https://2ip.ru',timeout=(10,10),
					 headers=headers, proxies={'https':'socks4://' + proxy})
			# Если ошибка - добавляем прокси в список proxy_failed и переходим к следующему прокси]
			except OSError:
				work_with_exceptions(proxy, proxy_sorted, 'failed')
				continue

			if response.status_code == requests.codes['ok']:					# Если статус запроса 200
				select_ip = re.search('(\d+\.\d+\.\d+\.\d+)', response.text)	# в ответе ищем шаблон (IP-адрес)
				if select_ip != None:											# группируем результат поиска
					select_ip = select_ip.group(1)
				print(Back.GREEN + 'OK! Установлен IP-адрес: ' + str(select_ip), end='')
				print(Style.RESET_ALL)
				time.sleep(1)
				proxy_worked.append(proxy)
				print (str(user_agent_worked[0]), end='')		# Вывод выбранного юзер-агента на экран
				time.sleep(1)									# добавляем в список рабочий прокси
				break											# Выходим из цикла]
		return proxy

	try:													
		if use_base == None:
			return not_use_json_base()						
		else:
			return use_json_base()
	except UnboundLocalError:									# если файл НЕ содержит прокси
		pass												 	# пропустить исключение 
# Функция для получения последней удачно спарсенной страницы (для определения завершения работы ПО)
def get_start_page(dump, start_page=None,table_name=None):

	if dump == 'default_dump':
		start_page = json.load(open(config_file))['start_page']
		return start_page
			
	elif dump == 'dump':
		dump = json.load(open(config_file))
		dump['start_page'] = start_page
		write_to_json(config_file, dump)
	
	elif dump == 'end_dump':
		dump = json.load(open(config_file))
		dump['start_page'] = 1
		write_to_json(config_file, dump)
		print(Style.BRIGHT + Fore.GREEN +
		 '\nВсе объявления сохранены в базу данных', end='')
		print(Style.RESET_ALL)
		#Получаем названия столбцов
		cursor.execute(f"SELECT * FROM {table_name}")
		row_headers=[x[0] for x in cursor.description]
		rv = cursor.fetchall()
		all_data = []
		for result in rv:
			k=[]
			for i in result:
				if isinstance(i,str):
					k.append(i.replace('\\xa0', ' '))
				else:
					k.append(i)
			all_data.append(dict(zip(row_headers,k)))
		end_sound()
		return(all_data)

# Общая функция для записи информации в JSON
def write_to_json(json_file, dump):
	with open (json_file, 'w')	as j_f:
		json.dump(dump,j_f,indent=4, cls=DateTimeEncoder)
# Общая функция для записи информации в БД
def write_to_db(data, table_name):
	if table_name == 'avito':
		cursor.execute(
		"""INSERT INTO avito (Id_объявления, Размещено, Название, Текст, Цена,
							 Рыночная_цена, Примечание, Телефон, Адрес,
							 Категория, Фото, Ссылка, Продавец)
		 	VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (Id_объявления)
		 	DO UPDATE SET (Размещено, Название, Текст, Цена, Рыночная_цена, Примечание,
		 	 				Телефон, Адрес, Категория, Фото, Ссылка, Продавец) = 
		 	 				(EXCLUDED.Размещено, EXCLUDED.Название, EXCLUDED.Текст, EXCLUDED.Цена,
		 	 				 EXCLUDED.Рыночная_цена, EXCLUDED.Примечание, EXCLUDED.Телефон,
		 	 				 EXCLUDED.Адрес, EXCLUDED.Категория, EXCLUDED.Фото, EXCLUDED.Ссылка,
		 	 				 EXCLUDED.Продавец)""", tuple(data.values()))
		connection.commit()
		print("Record inserted successfully") 

	elif table_name == 'bazarpnz':
		cursor.execute(
		"""INSERT INTO bazarpnz (Id_объявления, Размещено, Название, Текст, Цена,
							 Телефон, Адрес, Категория, Фото, Ссылка, Продавец)
		 	VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (Id_объявления)
		 	DO UPDATE SET (Размещено, Название, Текст, Цена, Телефон,
		 					Адрес, Категория, Фото, Ссылка, Продавец) = 
		 	 				(EXCLUDED.Размещено, EXCLUDED.Название, EXCLUDED.Текст, EXCLUDED.Цена,
		 	 				 EXCLUDED.Телефон, EXCLUDED.Адрес, EXCLUDED.Категория, EXCLUDED.Фото,
		 	 				 EXCLUDED.Ссылка, EXCLUDED.Продавец)""", tuple(data.values()))
		connection.commit()
		print("Record inserted successfully") 

# Класс для возможности записывать в JSON объект datetime		
class DateTimeEncoder(json.JSONEncoder):
	# Переопределение дефолтного метода
	def default(self, obj):
		if isinstance(obj, (dt)):
			return obj.isoformat()