from modules.config import *
from modules.addons import check_proxy, write_to_json
# Функция для задания списоков приоритета
def prioritization(proxy_sorted, last_index, looped_program=None, priority_list_from_file=None):
	priority_list = []
	not_use_list = []
	# в список попадают прокси, которые больше не будут использоваться в БД программы
	def not_use():
		for key, value in proxy_sorted.items():
			for proxy in value:
				if proxy['attempts'] >= 30 and proxy['success'] / proxy['attempts'] <= 0.1:
					not_use_list.append(proxy['ip:port'])
	# ['ok']
	def first():
		for proxy in proxy_sorted['ok']:
			if proxy['ip:port'] not in not_use_list:
				if proxy['ip:port'] not in [i[0] for i in priority_list]:
					priority_list.append((proxy['ip:port'], 'Priority: 1'))
	# attempts >10 & success > 70%
	def second():
		for key, value in proxy_sorted.items():
			if key != 'blocked':
				for proxy in value:
					if proxy['ip:port'] not in not_use_list:
						if proxy['ip:port'] not in [i[0] for i in priority_list]:
							if proxy['attempts'] >= 10 and proxy['success'] / proxy['attempts'] >= 0.7:
								priority_list.append((proxy['ip:port'], 'Priority: 2'))
	#[connection_error]	
	def third():
		for proxy in proxy_sorted['connection_error']:
			if proxy['ip:port'] not in not_use_list:
				if proxy['ip:port'] not in [i[0] for i in priority_list]:
					priority_list.append((proxy['ip:port'], 'Priority: 3'))
	#use ['blocked'] > tomorrow
	def fourth():						#blocked > tomorrow
		for key, value in proxy_sorted.items():
			if key == 'blocked':
				for proxy in value:
					if proxy['ip:port'] not in not_use_list:
						if proxy['ip:port'] not in [i[0] for i in priority_list]:
							last_use = dt.strptime(proxy['last_use'], time_format)
							tomorrow = dt.now() - delta
							if tomorrow > last_use:
								 priority_list.append((proxy['ip:port'], 'Priority: 4'))

	def fifth():							#failed
		for proxy in proxy_sorted['failed']:
			if proxy['ip:port'] not in not_use_list:
				if proxy['ip:port'] not in [i[0] for i in priority_list]:
					priority_list.append((proxy['ip:port'],'Priority: 5'))
		
	not_use()
	first(), second(), third(), fourth(), fifth()

	if last_index == 1:
		if looped_program == False:
			color_text = Fore.RED
		elif looped_program == True:
			color_text = Fore.GREEN

		if looped_program != None:
			print(Style.BRIGHT + color_text + '\nLooped program = ' + str(looped_program) + Style.RESET_ALL)
		#priority_dict =	dict((index + 1, proxy) for index, proxy in enumerate(list(dict.fromkeys(priority_list)))) # удаляем повторы
		priority_dict =	dict((index + 1, proxy) for index, proxy in enumerate(priority_list))	
		# Меняем ключи и значения местами
		priority_dict = {index: proxy for index, proxy in priority_dict.items() if index >= int(last_index)}
		#print(len(priority_dict))
	else:
		priority_dict = {index: proxy for index, proxy in priority_list_from_file[0].items() if int(index) >= int(last_index) and int(last_index) != int(index)}
	return priority_dict, not_use_list
# Функция устанавливает параметр в конфиге для использования БД
def install_checkbox():
	data = json.load(open(config_file))
	data['use_json_base'] = True
	write_to_json(config_file, data)

def main_base(proxy_sorted, use_json_base, looped_program):
	
	if not os.path.exists(temp_files_dir):
		os.mkdir(temp_files_dir)
	if not os.path.exists(priority_file):
		default_dump = {'last_index': 1,
						'priority_list': prioritization(proxy_sorted, 1, looped_program)}
		write_to_json(priority_file, default_dump)
		#subprocess.call(['attrib', '+h', priority_file])		# делаем файл скрытым от пользователя	
	
	data = json.load(open(priority_file))
	last_index = data['last_index']
	priority_list_from_file = data['priority_list']

	return check_proxy(proxy_sorted,use_base=use_json_base, base_list=prioritization(proxy_sorted, last_index, looped_program, priority_list_from_file)[0])

'''def restart_module():		# функция для перезапуска программы (вместо os.execl(sys.executable, sys.executable, *sys.argv))
	restart = 0
	while restart == 0:
		restart += 1
		main()'''	