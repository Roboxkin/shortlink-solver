import urllib.request
import urllib.parse

# IP-адрес сайта
ip_address = '208.68.163.87'

# Доменное имя сайта
domain_name = 'oii.la'

# URL для запроса
url = f'http://{ip_address}/links/go'

# Заголовки запроса
headers = {
    'Host': domain_name,
    'Content-Type': 'application/x-www-form-urlencoded',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
    'Referer': url
    # 'X-Requested-With': 'XMLHttpRequest'  # Имитация запроса от jQuery
}

# Данные для отправки в формате формы
data = {
    'token': 'd90613b380c2697807dfec66e695527f47e734de2024GR8YpL4enmV0711aHR0cHM6Ly9saXRlY29pbmZhdWNldC5jb20vP3Rva2VuPTM4Mi5kNTgyZTIyNmUzYmRiZGRjNDU5NjE4MDQx',
    '_method': 'POST',
    'ad_form_data': 'ZTlhMGJjOThmYmFlNGEyYWUwYjZmZTdmMDQwNTIyN2ExMzY5ZWM0NjQ3ZDNiNmJmNDQzOTgzYmE3Y2E4OGY1MMYLrjUQdjpmVbuHxxRWxA/gicSh1Sy5lR+qt5RACreT11iap+R6xJZGU0PbeyBa8EOsS1jywhab/0H2p/1hve4I1JI+wslz5logT6JcZjQbDAljgo4lcvfxHDfcswYf9PejyhQRi4Su4lsIN1EmB8yhpkIJEvtFvXyuyNPicyVe0sJu3PH7JUxMKdL/NY3bjUtpZ/MQrBouIZiCuDusp6PjiIms08ckZFf6YSxytsYdp1jv6B1NlmdMfETQGOryMdnd97OlyTUIvjpJmRxFhKdBD4tvtTilwZzswpvo0aCnOu5+xng6mxFkMHWWsNSwW/MIUF3jy3wmyWcaryZugDj5ahvqG1JyIVoZScib+sTx',
    # 'alias': 'GR8YpL4enmV',
    # 'url': 'oii.la/GR8YpL4enmV',
}

# Кодирование данных в формат application/x-www-form-urlencoded
data_encoded = urllib.parse.urlencode(data).encode('utf-8')

# Создание запроса
req = urllib.request.Request(url, data=data_encoded, headers=headers, method='POST')

# Выполнение запроса
try:
    response = urllib.request.urlopen(req)
    # Чтение ответа
    response_data = response.read()
    # Декодирование ответа в строку
    response_text = response_data.decode('utf-8')
    print(response_text)
except urllib.error.URLError as e:
    print(f"Error: {e.reason}")
