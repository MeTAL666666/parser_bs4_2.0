# Импорт всех переменных из config.py
from modules.config import *
# Импорт модулей
from modules import parser_proxy, base, create_user_agent_file, parser_avito, parser_bazarpnz, db_connection
# Импорт функций из модуля addons.py
from modules.addons import work_with_json, write_to_json, work_with_exceptions, check_proxy, get_start_page

app=Flask(__name__) # Переменная для запуска Flask

# Декоратор для перехода на главную страницу
@app.route('/')
def index():
	return render_template('index.html')
# Декоратор для перехода на страницу поиска Avito
@app.route('/avito')
def avito():
	# При каждом посещении страницы очищаем таблицу Avito
	delete_avito_sql = """
		DELETE FROM avito
	"""
	db_connection.delete_table(delete_avito_sql, connection, cursor)
	# Создаем json для записи запроса, введенного пользователем
	if not os.path.exists(temp_files_dir):
		os.mkdir(temp_files_dir)
	if not os.path.exists(search_file_avito):
		default_dump = {"search_query": "",
						"region": ""}
		write_to_json(search_file_avito, default_dump)
	# Создаем json для остановки парсера
	try:
		json.load(open(stop_file_bazarpnz))
	except:
		if not os.path.exists(stop_file):
			default_dump = {'stop_function': False}
			write_to_json(stop_file, default_dump)
	# Отправляем на отрисовку html-страницу
	return render_template('avito.html')
# Декоратор для перехода на страницу результатов поиска Avito
@app.route('/success_avito', methods=['POST'])
def success_avito():
	try:
		# Получаем данные из поискового запроса, введенного пользователем
		if request.method=='POST':
			search_response= request.form['what_search']
			region_response = request.form['region']
			in_headlines = request.form.get('in_headlines')
			# Если не введен регион, или выбран «Все регионы»
			if region_response.lower() in ['все регионы','?','', r'\s+']:
				#Меняем его
				region_response = 'all'
			# Если введен регион «Каменка»
			elif'каменка' in region_response.lower():				
				region_response = [i.strip() for i in region_response.split(',')]
				region_response = (f'{region_response[1]} {region_response[0]}').lower()
				for key in translit_dict:
					# Подставляем впереди область (особенность Авито для конкретных регионов)
					region_response = region_response.replace(key, translit_dict[key]).lower()
			# В остальных случаях убираем область, оставляем населенный пункт	
			else:
				region_response = [i.strip() for i in region_response.split(',')]
				region_response = region_response[0].lower()
				for key in translit_dict:
					region_response = region_response.replace(key, translit_dict[key]).lower()

			if not os.path.exists(temp_files_dir):
				os.mkdir(temp_files_dir)
			# Записываем полученный запрос в json
			if os.path.exists(search_file_avito):
				default_dump = {'search_query': search_response,
								'region': region_response}
				write_to_json(search_file_avito, default_dump)
			# При начале поиска отключаем остановку парсинга
			if os.path.exists(stop_file):
				default_dump = {'stop_function': False}
				write_to_json(stop_file, default_dump)
			# Отправляем на отрисовку html страницу с ключевыми словами, чтобы работать с ними в html
			return render_template('success_avito.html', keyword = request.form['what_search'],
									 region = request.form['region'] if request.form['region'] not in ['?','', r'\s+'] else 'Все регионы',
									 display = parser_avito.main(in_headlines))
	# Если выброшено исключение, то результаты не найдены
	except (TypeError, AttributeError):
		return render_template('no_result_avito.html', keyword = request.form['what_search'])
# Декоратор для остановки парсера Avito
@app.route('/stop_avito')
def stop_avito():
	if not os.path.exists(temp_files_dir):
				os.mkdir(temp_files_dir)
	# Меняем значение в файле для остановки парсера
	if os.path.exists(stop_file):
		default_dump = {'stop_function': True}
		write_to_json(stop_file, default_dump)
	return render_template('stop_avito.html')
# Декоратор для перехода на страницу отсутствия результатов поиска Avito
@app.route('/no_result_avito')
def no_result_avito():
	return render_template('no_result_avito.html')

'''Ниже для Bazarpnz повторяются те же действия, что и для Avito'''

# Декоратор для перехода на страницу поиска Bazarpnz
@app.route('/bazarpnz')
def bazarpnz():
	delete_bazarpnz_sql = """
		DELETE FROM bazarpnz
	"""
	db_connection.delete_table(delete_bazarpnz_sql, connection, cursor)
	if not os.path.exists(temp_files_dir):
		os.mkdir(temp_files_dir)
	if not os.path.exists(search_file_bazarpnz):
		default_dump = {"search_query": ""}
		write_to_json(search_file_bazarpnz, default_dump)
	try:
		json.load(open(stop_file_bazarpnz))
	except:
		if not os.path.exists(stop_file):
			default_dump = {'stop_function': False}
			write_to_json(stop_file, default_dump)
	return render_template('bazarpnz.html')
# Декоратор для перехода на страницу результатов поиска Bazarpnz
@app.route('/success_bazarpnz', methods=['POST'])
def success_bazarpnz():
	try:
		if request.method=='POST':
			search_response= request.form['what_search']
			search_response = urllib.parse.quote(search_response, encoding='cp1251')
			in_headlines = request.form.get('in_headlines')
			if not os.path.exists(temp_files_dir):
				os.mkdir(temp_files_dir)
			if os.path.exists(search_file_bazarpnz):
				default_dump = {'search_query': search_response}
				write_to_json(search_file_bazarpnz, default_dump)
			if os.path.exists(stop_file):
				default_dump = {'stop_function': False}
				write_to_json(stop_file, default_dump)
			
			return render_template('success_bazarpnz.html', keyword = request.form['what_search'],
									 display = parser_bazarpnz.main(in_headlines))
	except TypeError:
		return render_template('no_result_bazarpnz.html', keyword = request.form['what_search'])
# Декоратор для остановки парсера Bazarpnz
@app.route('/stop_bazarpnz')
def stop_bazarpnz():
	if not os.path.exists(temp_files_dir):
				os.mkdir(temp_files_dir)
	if os.path.exists(stop_file):
		default_dump = {'stop_function': True}
		write_to_json(stop_file, default_dump)
	return render_template('stop_bazarpnz.html')
# Декоратор для перехода на страницу отсутствия результатов поиска Bazarpnz
@app.route('/no_result_bazarpnz')
def no_result_bazapnz():
	return render_template('no_result_bazarpnz.html')

# Декораторы для редиректа на главную страницу при ошибках
@app.errorhandler(404)
def page_not_found(e):
    return redirect('/')

@app.errorhandler(405)
def method_not_allowed(e):
    return redirect('/')

#Точка входа
if __name__ == '__main__':
	print(f'Парсер объявлений с ОПРО «Avito» и «Bazarpnz»'
			f'\nv.1.0 RC1'
			f'\nNikolaev.V.A.')
	#Обязательная проверка конфиг-файла при запуске ПО
	work_with_json('create_config_file')
	# Если была произведена запись времени запуска парсера прокси
	if parser_proxy.last_launch_time() == True:
		# Запускаем парсер прокси (он отрабатывает либо 1 раз в сутки, либо при создании записи last_lauch_time.json)		
		parser_proxy.main()
	work_with_json()
	app.debug=False
	# Запуск программы
	app.run()