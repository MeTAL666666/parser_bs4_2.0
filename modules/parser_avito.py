from modules.config import *
from modules import parser_proxy, base, create_user_agent_file
from modules.addons import work_with_json, write_to_json, work_with_exceptions, check_proxy, get_start_page
# Импорт модуля для получения данных со страниц объявлений Avito
from modules.get_data import get_data_avito

'''
Описание функций:
get_html() - получение html документа по запросу на переданный в функцию url
get_total_pages() - определение количества страниц, исходя из данных в html документе
get_page_data() - отправка html в модуль get_data для получениz данных из объявлений
main() - получает на вход от Flask режим поиска (общий или по заголовкам)

'''

def get_html(url, start_page, proxy_sorted, use_proxy, use_json_base, looped_program):
	try:		
		session = requests.session()		# Создание сессии подключения
		adapter = TlsAdapter(ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1)
		session.mount("https://", adapter)
		if use_proxy == True:
			response = session.request('GET',url,timeout=(90,90), 
				headers=headers, proxies={'https': 'socks4://' + proxy_worked[0]})
		else:
			response = session.request('GET',url,timeout=(90,90), headers=headers)
		return response.text				# Возвращается ответ в текстовом виде
	# При данном исключении считается, что все прокси перебраны или proxy_list.txt пуст		
	except IndexError:
		if use_proxy == True:
			# Обработка пустого файла proxy_file.txt
			empty = work_with_exceptions(None, None, 'empty_proxy_file')
			# Если proxy_list.txt пуст...
			if empty == 0:
				parser_proxy.last_launch_time(True) # обновляется время запуска парсера прокси
				parser_proxy.main()					# принудительно запускается парсер прокси
				main()								# запускается основная функция программы
			else:
				if use_json_base == False: 			# если весь proxy_list.txt проверен
					count = 0						
					while count <7:
						count += 1
						time.sleep(0.3)
						points = '.' * count
						print(Style.BRIGHT + Back.BLUE + 'Начинаю работу с базой' 
							+ points, end='\r') 							
					print(Style.RESET_ALL)
					base.install_checkbox()			# вызов модуля работы с базой
					os.execl(sys.executable, sys.executable, *sys.argv)
				else:
					if looped_program == False:
						print('конец программы')
						os.remove(priority_file)
						sys.exit()						# программа завершается
					else:
						os.remove(priority_file)
						os.execl(sys.executable, sys.executable, *sys.argv)
	# Если соединение с Avito не удалось...
	except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
		if use_proxy == True:	
			# ...проверяем текущий прокси на нахождение в списке connection_error
			work_with_exceptions(proxy_worked[0], proxy_sorted, 'connection_error', use_base = use_json_base)
			pass
		else:
			print('Соединение потеряно')
			pass
			
def get_total_pages(html, start_page, proxy_sorted, use_proxy, use_json_base):
	try:
		soup = BeautifulSoup(html, 'lxml')
		if soup.find('div', class_='no-results-root-bWQVm') == None and soup.find('div', class_='items-extra-hfCGf') == None or soup.find('div', class_='items-extraTitle-JFe8_').text == 'Дальше встречаются объявления из других городов':
			pages = soup.find('div', class_='pagination-pages').find_all('a', class_='pagination-page')[-1].get('href')
			total_pages = pages.split('=')[2].split('&')[0]
			ads_count = soup.find('span', class_='page-title-count-wQ7pG').text
			print(f'Найдено объявлений: {ads_count}')
		elif soup.find('div', class_='no-results-root-bWQVm') != None:
			total_pages = 0
			print('Объявлений по запросу не найдено')
		elif soup.find('div', class_='items-extra-hfCGf') != None and soup.find('div', class_='items-extraTitle-JFe8_').text != 'Дальше встречаются объявления из других городов':
				total_pages = 1
				ads_count = soup.find('span', class_='page-title-count-wQ7pG').text
				print(f'Найдено объявлений: {ads_count}')
		return int(total_pages)
	# При данном исключении считаем, что Avito блокирует IP	
	except AttributeError:	
		if use_proxy == True:
			# ...проверяем текущий прокси на нахождение в списке proxy_blocked
			work_with_exceptions(proxy_worked[0], proxy_sorted,'blocked', use_base=use_json_base)
		else:
			print('Неверное указан регион поиска или Ваш IP-адрес заблокирован Avito...')
			raise AttributeError
		return 0

def get_page_data(html, proxy_sorted, use_proxy, use_json_base):
	soup = BeautifulSoup(html, 'lxml')
	try:
		items = soup.find('div', class_='items-items-kAJAg').find_all('div', class_='iva-item-root-_lk9K')
		get_data_avito(items,use_proxy)							
	# При данном исключении считаем, что Avito блокирует IP			
	except AttributeError:
		if use_proxy == True:
			# ...проверяем текущий прокси на нахождение в списке proxy_blocked
			work_with_exceptions(proxy_worked[0], proxy_sorted,'blocked', use_base=use_json_base)
		else:
			print('Ваш IP-адрес заблокирован Avito...')

def main(in_headlines):
	'''
	Описание основных переменных:
	in_headlines - передан из main.py (режим поиска)
	data_search - данные из json (поисковой запрос + регион)
	search_query - поисковой запрос
	region - регион поиска
	url - адрес для формирования запроса и получения количества страниц
	base_url - используется как база для подстановки при переходе по страницам

	data - все параметры из конфиг-файла
	use_proxy - параметр их конфиг-файла (включено или выключено использование прокси-серверов)
	use_json_base - параметр их конфиг-файла (используется ли собранная и отсортированная база прокси серверов)
	looped_program - параметр их конфиг-файла (False: при использовании прокси  парсит, пока в списке не закончились рабочие прокси
											   True: при использовании прокси  парсит, пока не будут спарсены все объявления)
	'''

	if in_headlines != 'enable':
		i_hl = ''
	else:
		i_hl = 'bt=1&'
	'''Определение параметров для составления url'''	
	data_search = json.load(open(search_file_avito))
	search_query = query_part +  data_search['search_query']
	region = data_search['region'] + '?'
	url = 'https://www.avito.ru/' + region + i_hl + correction + search_query[1:]
	base_url = 'https://www.avito.ru/' + region

	data = json.load(open(config_file))
	use_proxy = data['use_proxy']
	use_json_base = data['use_json_base']
	looped_program = data['looped_program']
	if not os.path.exists(user_agent_file):
		create_user_agent_file.create_file()
	with open(user_agent_file, 'r') as ua_f:				# Открывается файл с юзер-агентами
		user_agent = ua_f.readlines()						# Считывается построчно
		user_agent_worked.clear()							# Очищается список юзер-агентов (на каждый запрос свой агент)
		user_agent_worked.append(random.choice(user_agent))	# Рандомно выбирается юзер-агент и добавляется в список
	# Получение списков из структуры proxy_json.json
	# Распределение списков для последующей записи в proxy_json.json
	proxy_sorted = {'ok': work_with_json()[0],
				'blocked': work_with_json()[1],
				'connection_error': work_with_json()[2],
				'failed': work_with_json()[3]
				}
	start_page = get_start_page('default_dump')
	if use_proxy == True:
		if use_json_base == False:
			# Проверка работоспособности прокси		
			proxy = check_proxy(proxy_sorted)
		else:
			proxy = base.main_base(proxy_sorted, use_json_base, looped_program)
	else:
		print('\n' + Back.RED + 'Программа запущена без использования прокси!!!', end = '')
		print(Style.RESET_ALL)

		#Автоматический пропуск предупреждения
		while False: #При смене на True программа будет ждать подтверждения
			msg = input('Продолжить? Y/N\n')
			msg = ''
			if msg.lower() in ['y', 'н', 'у', 'e', '']:
				break
			elif msg.lower() in ['n','т']:
				sys.exit()
	print(url)
	# Получение списка страниц с Авито
	total_pages = get_total_pages(get_html(url, start_page, proxy_sorted,use_proxy, use_json_base, looped_program), start_page, proxy_sorted, use_proxy, use_json_base)
	# Если страниц больше одной
	if total_pages > 1:
		for i in range(start_page, total_pages):
			try:
				# При каждом переходе на новую страницу проверяется значение функции остановки парсинга
				data = json.load(open(stop_file))
				if data['stop_function'] == True:
					connection.close()
					cursor.close()
					raise Exception("Something went wrong")
				else:
					pass
			except:
				os.execl(sys.executable, sys.executable, *sys.argv)				
			url_gen = base_url + correction[:-1] + page_part + str(i) + search_query 	# url после ввода запроса
			print(f'\n{url_gen}\n#{start_page}/{total_pages}')							# вывод url'ов страниц
			html = get_html(url_gen, start_page, proxy_sorted, use_proxy, use_json_base, looped_program)
			time.sleep(10)																# задержка
			get_page_data(html, proxy_sorted, use_proxy, use_json_base)					# получение информации из объявлений
			if use_proxy == True:														
				work_with_exceptions(proxy, proxy_sorted,'ok')							# запись прокси в список рабочих
			start_page += 1
			get_start_page('dump', start_page)

		if use_proxy == True:
			# Проверяем прокси из файла proxy_list.txt на нахождение в списке proxy_ok
			work_with_exceptions(proxy, proxy_sorted,'ok')
			if os.path.exists(priority_file):
				os.remove(priority_file)
		return get_start_page('end_dump',table_name='avito')
	# Если страница одна, действия повторяются из предыдущего условия
	elif total_pages == 1:
		url_gen = base_url + correction[:-1] + page_part + str(total_pages) + search_query
		print(f'\n{url_gen}\n#{total_pages}/{total_pages}')		# вывод url'ов страниц
		html = get_html(url_gen, total_pages, proxy_sorted, use_proxy, use_json_base, looped_program)
		time.sleep(10)
		get_page_data(html, proxy_sorted, use_proxy, use_json_base)
		if use_proxy == True:
			work_with_exceptions(proxy, proxy_sorted,'ok')
		start_page == 1
		get_start_page('dump', start_page)
		if use_proxy == True:
			# Проверяем прокси из файла proxy_list.txt на нахождение в списке proxy_ok
			work_with_exceptions(proxy, proxy_sorted,'ok')
			if os.path.exists(priority_file):
				os.remove(priority_file)
		return get_start_page('end_dump',table_name='avito')
	# Если не найдено объявлений, то ничего не делать, тем самым поймается и обработается исключение об отсутствии результатов
	elif total_pages == 0:
		pass