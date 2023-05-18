from modules.config import *
from modules.addons import DateTimeEncoder
from modules import create_user_agent_file
'''
Парсятся SOCKS 4 прокси
'''
# Написать функцию read_from_file и read_from_json в addons(наверное)
def last_launch_time(forced=False):

	def rw_last_launch_time(file, mode):
		if mode == 'w':
			with open (file,'r') as f:
				#data = [json.load(f)[i] for i in dump.keys()][0]
				dump = json.load(f)

			dump['last_launch_parser_proxy'] = dt.strftime(dt.now(), time_format)
			dump['use_json_base'] = False

			#print([data[i] for i in dump.keys()][0])
			with open (file, mode) as f:
				json.dump(dump,f, indent=4, cls=DateTimeEncoder)
				return dump
		elif mode == 'r':
			with open (file, mode) as f:
				data = json.load(f)
				return data

	if forced == True :
		rw_last_launch_time(config_file, 'w')
	else:	
		data = rw_last_launch_time(config_file, 'r')
		last_launch = dt.strptime(data['last_launch_parser_proxy'], time_format)
		tomorrow = dt.now() - delta
		if tomorrow > last_launch:
			rw_last_launch_time(config_file, 'w')
			return True

def get_html(url):
	with open(user_agent_file, 'r') as ua_f:				# Открывается файл с юзер-агентами
		user_agent = ua_f.readlines()						# Считывается построчно
		user_agent_worked.clear()							# Очищается список юзер-агентов (на каждый запрос свой агент)
		user_agent_worked.append(random.choice(user_agent))	# Случайным образом выбирается юзерагент и добавляется в список

	session = requests.Session()							# Создание сессии(для использования cookies)
	response = session.get(url_parse_proxy, timeout=(30,30), headers=headers)
	return response.text									# Возвращается ответ в текстовом виде
# Функция для получения адресов прокси
def get_proxy(html):
	text = BeautifulSoup(html, 'lxml').get_text().split()	# Получение ответа на запрос в текстовом виде
	upd_count = 0											# Счетчик для вывода даты обновления в файле
	new_proxy = []											# Список полученных новых прокси
	
	if not os.path.exists(proxies_file):					# Если файл, хранящий список прокси отсутствует
		with open(proxies_file, 'w') as p_f:				# создаём его, чтобы избежать исключений
			print('В каталоге "files" создан файл:', proxies_file.split('/')[-1])

	for t in text:
		proxy = re.search('(\d+\.\d+\.\d+\.\d+\:\d+)', t)	# Поиск текста по шаблону
		if proxy != None:
			proxy = proxy.group(1)							# Необходимое условие, чтобы работала группировка
		else:
			continue

		assert isinstance(port_not_use, tuple),'"port_not_use" не является кортежем'

		if not proxy.endswith(port_not_use):							# Если у прокси порт не из списка (не SOCKS4)
			with open(proxies_file, 'r') as p_f:						# считываем файл со списком прокси
				proxies = [line.rstrip() for line in p_f.readlines()]	# убираем знаки переноса строки
				if proxy not in proxies:								# сравниваем список спарсенных прокси с файлом
					new_proxy.append(proxy)								# добавляем новые прокси в список

	if len(new_proxy) > 0:												# если список новых прокси не пустой
		if os.path.exists(priority_file):
				os.remove(priority_file)

		with open(proxies_file, 'a') as p_f:
			for proxy in new_proxy:
				splitter_line = '-' * 34					
				date_update = dt.now().strftime('%d/%m/%Y, %H:%M:%S')
				text_update = ('Date update: ' + date_update + '\n'
						+ str(len(new_proxy)) + ' new proxies have been added\n\n')			#
				while upd_count == 0:
					upd_count += 1
					p_f.write(splitter_line + '\n' + text_update)
				p_f.write(proxy + '\n')					# записываем его в файл
		print('Было добавлено', len(new_proxy), 'новых прокси!')
		time.sleep(2)

def main():
	if not os.path.exists(user_agent_file):
		create_user_agent_file.create_file()
	print(Style.BRIGHT + Fore.CYAN + 'Парсер прокси был запущен!', end='')
	print(Style.RESET_ALL)
	proxy_list = get_proxy(get_html(url_parse_proxy))