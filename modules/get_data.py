from modules.config import *
from modules.addons import write_to_db

# Функция для получения данных из объявлений c Avito
def get_data_avito(items, use_proxy):
	for item in items:
		try:
			data = json.load(open(stop_file))
			if data['stop_function'] == True:
				connection.close()
				cursor.close()
				raise Exception("Stop parsing!")
			else:
				pass
		except:
			os.execl(sys.executable, sys.executable, *sys.argv)

		try:
			title = item.find('div',class_='iva-item-body-KLUuy').find('h3').text.strip()
			print ('\n' + title)
		except:
			title = ''
		try:
			price = re.sub(r"\D", '',item.find('div',class_='iva-item-body-KLUuy').find('span', class_='price-price-JP7qe').text)
			if price == None:
				print(' ₽')
				price = 1
			else:
				print(price + ' ₽')
		except:
			price = 1			
		try:
			period = item.find('div',class_='date-text-KmWDf').text
			print(period)
		except:
			period = ''
		try:
			note = item.find('span',class_='SnippetBadge-title-afjYB').text
			print(note)
		except:
			note = ''
		try:
			text = item.find('div',class_='iva-item-text-Ge6dR iva-item-description-FDgK4 text-text-LurtD text-size-s-BxGpL').text.replace('\n',' ')
			print(text)
		except:
			text = ''
		try:
			delivery = item.find('div', class_= 'delivery-root-LFKPq')
			if delivery != None:
				delivery = 'Есть доставка'
				print('Есть доставка')
			else:
				delivery = ''
				print('Нет доставки')
		except:
			delivery = ''
			print('Нет доставки' )
		try:
			url ='https://www.avito.ru' + item.find('div',class_='iva-item-body-KLUuy').find('a').get('href')
			print(url)
		except:
			url = ''
		#Запрос для открытия каждого объявления
		time.sleep(randint(10,16))
		session = requests.session()		# Создание сессии подключения
		adapter = TlsAdapter(ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1)
		session.mount("https://", adapter)
		if use_proxy == True:
			response = session.request('GET',url,timeout=(90,90), 
				headers=headers, proxies={'https': 'socks4://' + proxy_worked[0]})
		else:
			response = session.request('GET',url,timeout=(90,90), headers=headers)			
		response_soup = BeautifulSoup(response.text, 'lxml')
		try:
			try:
				address1 = str(response_soup.find('div',class_='style-item-address-KooqC').find('span',class_='style-item-address__string-wt61A').text)
				if address1 == None:
					address1 = ''
			except:
				address1 = ''				
			try:
				address2 = str(response_soup.find('span',class_='style-item-address-georeferences-item-TZsrp').find_all('span')[-1].text)
				if address2 == None:
					address2 = ''
			except:
				address2 = ''
			if address1 != '' and address2 != '':
				address1+='  |  '
			address = address1 + address2
			print(address)
		except:
			address = ''
		try:
			phone = re.search('(\d{5}\%\d{5}\-\d{2}\-\d{2})', response.text)
			phone = phone.group(0).replace('-','')
			phone = '+7'+ phone[2:5] + phone[9:]
			print (phone)
		except:
			phone = ''
		try:
			photo = response_soup.find('div',id='app').find('div',{"class":"image-frame-wrapper-_NvbY"}).find('img').attrs['src']
			print(photo)
		except:
			photo = ''
		try:
			price_note1 = response_soup.find('span',class_='styles-title-cjhHf desktop-15tqd8s')				
			if price_note1 != None:
				price_note1 = price_note1.text.split('— ')[1].capitalize()
				print (price_note1)				
			price_note2 = response_soup.find('div',class_='goods-imv-block-RyBso').find('span', class_='styles-hint-_wpET desktop-12w52jh')				
			if price_note2 != None:
				price_note2 = price_note2.text
				print(price_note2)
			price_note = '. '.join([i for i in [price_note1, price_note2] if i != None])
		except:
			price_note = ''
		try:
			market_price = ' '.join([re.sub(r'\D','',response_soup.find('div', class_='desktop-ari7g4').find('div', class_= 'styles-chart-KWG7y').find_all('span', class_="styles-border-r6BSm")[0].text), '—',
            						re.sub(r'\D','',response_soup.find('div', class_='desktop-ari7g4').find('div',class_= 'styles-chart-KWG7y').find_all('span', class_="styles-border-r6BSm")[1].text)]) + ' ₽'
			if 'Цена ниже рыночной' not in price_note:
				print('Рыночная цена:', market_price, '₽')
			else:
				print('Средняя рыночная цена:', market_price.split(' — ')[1], '₽')
		except:
			market_price = ''
		try:
			seller_block = response_soup.find('div', class_='style-seller-info-col-PETb_')
			if seller_block != None:
				try:
					name = '«' + seller_block.find('span').text + '»'
				except:
					name = None
				try:
					group = seller_block.find('div', {'data-marker': 'seller-info/label'}).get_text()
				except:
					group = None
				try:
					# Как давно продавец на Авито
					prescription = seller_block.find_all('div', class_='style-seller-info-value-vOioL')[1].find('div').text
				except:
					prescription = None
				try:
					rating = 'Рейтинг ' + seller_block.find('span', class_='style-seller-info-rating-score-C0y96').text.replace(',','.')
				except:
					rating = None
				try:
					feedback = item.find('span', {'data-marker': 'seller-rating/summary'}).get_text()
				except:
					feedback = None
				
				seller_info = ', '.join([i for i in [name, group, prescription, rating, feedback] if i != None])
				print(seller_info)
			elif seller_block == None:
				seller_info = ', '.join([response_soup.find('span', class_='text-text-LurtD text-size-ms-_Zk4a').text,
										response_soup.find('div', {'data-marker': 'seller-info/label'}).get_text()])
				print(seller_info)
		except:
			seller_info = ''
		try:
			category = response_soup.find('div',class_='breadcrumbs-root-_GADZ').text.replace('·',' · ')
			print(category)
		except:
			category = ''			
		try:
			uid_find = re.search(r'\d+$',response_soup.find('span', {'data-marker': 'item-view/item-id'}).get_text())
			uid = int(uid_find.group())
			print('uid:', uid)			
		except:
			uid = ''			
		data = {'Id_объявления': uid,
				'Размещено': period,
				'Название': title,
				'Текст': text,
				'Цена': price,
				'Рыночная_цена': ', '.join([market_price, price_note]).strip(', '),
				'Примечание': ', '.join([delivery, note]).strip(', '),
				'Телефон': phone,
				'Адрес': address,
				'Категория': category,
				'Фото': photo,
				'Ссылка': url,
				'Продавец': seller_info
				}
		write_to_db(data, 'avito')

# Функция для получения данных из объявлений с Bazarpnz
def get_data_bazarpnz(items, use_proxy):
	for item in items:
		try:
			data = json.load(open(stop_file))
			if data['stop_function'] == True:
				connection.close()
				cursor.close()
				raise Exception("Stop parsing!")
			else:
				pass
		except:
			os.execl(sys.executable, sys.executable, *sys.argv)

		try:
			title = re.sub("'",'',item.find('td',class_='text').find('a').text)
			print('\n' + title)
		except:
			title = ''
		try:
			price = re.sub(r"\D", '',item.find('td',class_='price').find('span', class_='price').text)
			print(price, '₽')
			if price == '':
				price = 1
		except:
			price = 1
		try:
			if item.find('td',class_='text').find('div',class_='vdatext').find('a').get('href').startswith('/ann'):
				url ='http://bazarpnz.ru' + item.find('td',class_='text').find('div',class_='vdatext').find('a').get('href')
			else:
				url = item.find('td',class_='text').find('div',class_='vdatext').find('a').get('href')
			print(url)
		except:
			url = ''
		#Запрос для открытия каждого объявления
		time.sleep(randint(3,5))
		session = requests.session()		# Создание сессии подключения
		adapter = TlsAdapter(ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1)
		session.mount("http://", adapter)
		if use_proxy == True:
			response = session.request('GET',url,timeout=(90,90), 
				headers=headers, proxies={'https': 'socks4://' + proxy_worked[0]})
		else:
			response = session.request('GET',url,timeout=(90,90), headers=headers_bazarpnz)			
		response_soup = BeautifulSoup(response.text, 'lxml')
		try:
			try:
				period = re.search(r'(\d{2}\.\d{2}\.\d{4})',[i.get_text().split(': ')[1] for i in response_soup.find_all('span', class_='views') if i.get_text().startswith('Дата публикации объявления')][0]).group(0)
				print(period)
			except IndexError:
				period = re.search(r'(\d{2}\.\d{2}\.\d{4})',[i.get_text().split(': ')[1] for i in response_soup.find_all('span', class_='views') if i.get_text().startswith('Дата размещения объявления')][0]).group(0)
				print(period)
		except:
			period = ''
		try:
			text = re.sub("\\xa0"," ",re.sub("'",'',' '.join([i for i in list(response_soup.find_all('p', class_='adv_text')[0]) if isinstance(i,str)]).rstrip()))
			print(text)
		except:
			text = ''
		seller_block = {
						'name': '',
						'tel': '',
						'mailto': '',
						'address': ''
						}
		try:
			address = [i.replace('Район города:', 'address:') for i in re.sub(r'\s{2,}','\n',response_soup.text.strip()).strip().split('\n') if i.startswith('Район города:')]
			name = [i.replace('Имя:', 'name:') for i in response_soup.find_all('p', class_='contact_info')[-1].text.strip().split('\n') if i.startswith('Имя:')]
			script = response_soup.find_all('script')
			data = []
			for i in script:
				i = re.sub(r"[;'](\w+\=)*","",i.get_text()).strip().split('"')
				if len(i)>1:
					data += i
			seller = name + data + address
			for i in seller:
				if i.startswith(('tel:','mailto:', 'name:','address:')):
					seller_block[i.split(':')[0]] = i.split(':')[1].strip().replace('&#','-')
				seller_block['tel'] = re.sub(r'^8','+7',seller_block['tel'])
			for key, value in seller_block.items():
				if value not in ('',' '):
					print(value)
		except:
			tel = ''
			mailto = ''
			name= ''
			address = ''
		try:
			photo = 'http://bazarpnz.ru' + response_soup.find('a',class_='big_photo').get('href')
			if photo.endswith('img/1x1.gif'):
				photo = ''
			print(photo)
		except:
			photo = ''
		try:
			category_list = [i.get_text() for i in response_soup.find('div',id='nav').find_all('a')]
			for index, value in enumerate(category_list):
				if index == 0 and value != 'Главная':
					del category_list[0:3]
				elif index == 0 and value == 'Главная':
					del category_list[0]
			category = ' · '.join(category_list)
			print(category)
		except:
			category = ''			
		try:
			uid = int([i.get_text().split('№')[1] for i in response_soup.find_all('span', class_='views') if i.get_text().startswith('Объявление №')][0])
			print('uid:', uid)			
		except:
			uid = ''
		data = {'Id_объявления': uid,
				'Размещено': period,
				'Название': title,
				'Текст': text,
				'Цена': price,
				'Телефон': seller_block['tel'],
				'Адрес': seller_block['address'],
				'Категория': category,
				'Фото': photo,
				'Ссылка': url,
				'Продавец': ', '.join([seller_block['name'], seller_block['mailto']]).strip(', ')
				}			
		write_to_db(data,'bazarpnz')