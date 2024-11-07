import requests
from captcha_service import solve_captcha
from lxml import etree
import json
import time
from urllib.parse import urlencode
from colored import Fore, Back, Style
import logging

ERROR_COLOR = str(f'{Style.BOLD}{Fore.rgb(255, 255, 255)}{Back.rgb(41, 13, 5)}')
WARNING_COLOR = str(f'{Style.BOLD}{Fore.rgb(255, 255, 255)}{Back.rgb(120, 81, 62)}')
SUCCESS_COLOR = str(f'{Style.BOLD}{Fore.rgb(255, 255, 255)}{Back.rgb(5, 41, 21)}')

logging.basicConfig(level=logging.INFO)


# (en) Function to convert a dictionary to a query string
# (ru) Функция для преобразования словаря в строку запроса
def dict_to_query_string(data):
    return urlencode(data, doseq=True)


# (en) Main function to process short URLs
# (ru) Основная функция для обработки коротких URL
def short_start(shorturl, short_domain, shortid):
    parser = etree.HTMLParser()
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': shorturl,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    response = session.get(shorturl, headers=headers, allow_redirects=True)

    if response.status_code == 200:
        html_content = response.text
        tree = etree.fromstring(response.content, parser)

        try:
            # (en) Extract the value of the '_method' input field
            # (ru) Извлечение значения поля ввода '_method'
            method = tree.xpath('//input[@name="_method"]')
            if method:
                method_value = method[0].get('value')
            else:
                logging.error(
                    f"{ERROR_COLOR} Error! 'method' no search, GROUP: group_one, SHORTURL: {shorturl} {Style.reset}")
                return "https://error.error/error"

            # (en) Extract the value of the '_csrfToken' input field
            # (ru) Извлечение значения поля ввода '_csrfToken'
            csrf_token = tree.xpath('//input[@name="_csrfToken"]')
            if csrf_token:
                csrf_token_value = csrf_token[0].get('value')
            else:
                logging.error(
                    f"{ERROR_COLOR} Error! 'csrfToken' no search, GROUP: group_one, SHORTURL: {shorturl} {Style.resetT}")
                return "https://error.error/error"

            # (en) Extract the value of the 'action' input field
            # (ru) Извлечение значения поля ввода 'action'
            action = tree.xpath('//input[@name="action"]')
            if action:
                action_value = action[0].get('value')
            else:
                logging.error(
                    f"{ERROR_COLOR} Error! 'action' no search, GROUP: group_one, SHORTURL: {shorturl} {Style.reset}")
                return "https://error.error/error"

            # (en) Extract the value of the 'f_n' input field
            # (ru) Извлечение значения поля ввода 'f_n'
            f_n = tree.xpath('//input[@name="f_n"]')
            f_n_value = ''
            if f_n:
                f_n_value = f_n[0].get('value')

            # (en) Extract the value of the '_Token[fields]' input field
            # (ru) Извлечение значения поля ввода '_Token[fields]'
            token_fields = tree.xpath('//input[@name="_Token[fields]"]')
            if token_fields:
                token_fields_value = token_fields[0].get('value')
            else:
                logging.error(
                    f"{ERROR_COLOR} Error! 'token_fields' no search, GROUP: group_one, SHORTURL: {shorturl} {Style.reset}")
                return "https://error.error/error"

            # (en) Extract the value of the '_Token[unlocked]' input field
            # (ru) Извлечение значения поля ввода '_Token[unlocked]'
            token_unlocked = tree.xpath('//input[@name="_Token[unlocked]"]')
            if token_unlocked:
                token_unlocked_value = token_unlocked[0].get('value')
            else:
                logging.error(
                    f"{ERROR_COLOR} Error! 'token_unlocked' no search, GROUP: group_one, SHORTURL: {shorturl} {Style.reset}")
                return "https://error.error/error"
        except IndexError:
            logging.error(
                f"{ERROR_COLOR} Error! One of the required fields is missing, GROUP: group_one, SHORTURL: {shorturl} {Style.reset}")
            return "https://error.error/error"

        # (en) Extract JSON data from the HTML content
        # (ru) Извлечение JSON данных из HTML контента
        json_str = html_content.split('var app_vars = ')[1].split(';')[0]
        app_vars = json.loads(json_str)

        # (en) Check if captcha is enabled and solve it if necessary
        # (ru) Проверка, включена ли капча, и ее решение, если необходимо
        enable_captcha = app_vars.get('enable_captcha')
        if enable_captcha == "yes":
            captcha_type = app_vars.get('captcha_type')
            if captcha_type:
                if captcha_type == "recaptcha":
                    key = app_vars.get('reCAPTCHA_site_key')
                    cap_type = 'ReCaptchaV2'
                    captcha_response = solve_captcha(cap_type, key, shorturl, shortid)
                    if captcha_response is None:
                        logging.error(f"{ERROR_COLOR} ReCaptchaV2 was not resolved or an error occurred {Style.reset}")
                        return "https://error.error/error"

                elif captcha_type in ["invisible-recaptcha", "invisible"]:
                    key = app_vars.get('invisible_reCAPTCHA_site_key')
                    cap_type = 'ReCaptchaV3'
                    captcha_response = solve_captcha(cap_type, key, shorturl, shortid)
                    if captcha_response is None:
                        logging.error(f"{ERROR_COLOR} ReCaptchaV3 was not resolved or an error occurred {Style.reset}")
                        return "https://error.error/error"

                elif captcha_type == "hcaptcha_checkbox":
                    key = app_vars.get('hcaptcha_checkbox_site_key')
                    cap_type = 'hCaptcha'
                    captcha_response = solve_captcha(cap_type, key, shorturl, shortid)
                    if captcha_response is None:
                        logging.error(f"{ERROR_COLOR} hCaptcha was not resolved or an error occurred {Style.reset}")
                        return "https://error.error/error"

            else:
                logging.error(f"{ERROR_COLOR} Captcha type is not specified for SHORTURL: {shorturl} {Style.reset}")
                return "https://error.error/error"
        else:
            logging.warning(f"{WARNING_COLOR} Captcha is not enabled for SHORTURL: {shorturl} {Style.reset}")

        # (en) Extract the counter value from the JSON data
        # (ru) Извлечение значения счетчика из JSON данных
        counter_value = app_vars.get('counter_value')
        if counter_value is None:
            logging.error(f"{ERROR_COLOR} Counter value is not specified for SHORTURL: {shorturl} {Style.reset}")
            return "https://error.error/error"

        # (en) Prepare the data for the POST request
        # (ru) Подготовка данных для POST запроса
        data = {
            '_method': method_value,
            '_csrfToken': csrf_token_value,
            'action': action_value,
            '_Token[fields]': token_fields_value,
            '_Token[unlocked]': token_unlocked_value
        }

        # (en) Add captcha response to the data if captcha is enabled
        # (ru) Добавление ответа капчи к данным, если капча включена
        if enable_captcha == "yes":
            if captcha_type in ["recaptcha", "invisible-recaptcha", "invisible"]:
                data['g-recaptcha-response'] = captcha_response

            if captcha_type == "hcaptcha_checkbox":
                data['g-recaptcha-response'] = captcha_response
                data['h-captcha-response'] = captcha_response

        if f_n_value:
            data['f_n'] = f_n_value

        query_string = dict_to_query_string(data)

    else:
        logging.error(f"{ERROR_COLOR} Error while requesting: {response.status_code} {Style.reset}")
        return "https://error.error/error"

    # (en) Send the POST request with the prepared data
    # (ru) Отправка POST запроса с подготовленными данными
    response_post = session.post(shorturl, data=query_string, headers=headers)

    if response_post.status_code == 200:
        tree = etree.fromstring(response_post.content, parser)

        try:
            # (en) Extract the value of the '_method' input field from the response
            # (ru) Извлечение значения поля ввода '_method' из ответа
            method = tree.xpath('//input[@name="_method"]')
            if method:
                method_value = method[0].get('value')
            else:
                logging.error(
                    f"{ERROR_COLOR} Error! 'method' no search, GROUP: group_one, SHORTURL: {shorturl} {Style.reset}")
                return "https://error.error/error"

            # (en) Extract the value of the '_csrfToken' input field from the response
            # (ru) Извлечение значения поля ввода '_csrfToken' из ответа
            csrf_token = tree.xpath('//input[@name="_csrfToken"]')
            if csrf_token:
                csrf_token_value = csrf_token[0].get('value')
            else:
                logging.error(
                    f"{ERROR_COLOR} Error! 'csrfToken' no search, GROUP: group_one, SHORTURL: {shorturl} {Style.reset}")
                return "https://error.error/error"

            # (en) Extract the value of the 'ad_form_data' input field from the response
            # (ru) Извлечение значения поля ввода 'ad_form_data' из ответа
            ad_form_data = tree.xpath('//input[@name="ad_form_data"]')
            if ad_form_data:
                ad_form_data_value = ad_form_data[0].get('value')
            else:
                logging.error(
                    f"{ERROR_COLOR} Error! 'ad_form_data' no search, GROUP: group_one, SHORTURL: {shorturl} {Style.reset}")
                return "https://error.error/error"

            # (en) Extract the value of the '_Token[fields]' input field from the response
            # (ru) Извлечение значения поля ввода '_Token[fields]' из ответа
            token_fields = tree.xpath('//input[@name="_Token[fields]"]')
            if token_fields:
                token_fields_value = token_fields[0].get('value')
            else:
                logging.error(
                    f"{ERROR_COLOR} Error! 'token_fields' no search, GROUP: group_one, SHORTURL: {shorturl} {Style.reset}")
                return "https://error.error/error"

            # (en) Extract the value of the '_Token[unlocked]' input field from the response
            # (ru) Извлечение значения поля ввода '_Token[unlocked]' из ответа
            token_unlocked = tree.xpath('//input[@name="_Token[unlocked]"]')
            if token_unlocked:
                token_unlocked_value = token_unlocked[0].get('value')
            else:
                logging.error(
                    f"{ERROR_COLOR} Error! 'token_unlocked' no search, GROUP: group_one, SHORTURL: {shorturl} {Style.reset}")
                return "https://error.error/error"

            # (en) Extract the value of the 'action' attribute from the form
            # (ru) Извлечение значения атрибута 'action' из формы
            action = tree.xpath('(//form[@method="post"])[1]/@action')
            if action:
                if isinstance(action[0], etree._ElementUnicodeResult):
                    action_value = action[0]
                else:
                    action_value = action[0].get('value')
            else:
                logging.error(
                    f"{ERROR_COLOR} Error! 'form action' no search, GROUP: group_one, SHORTURL: {shorturl} {Style.reset}")
                return "https://error.error/error"

            time.sleep(counter_value)

            # (en) Prepare the data for the final POST request
            # (ru) Подготовка данных для финального POST запроса
            data2 = {
                '_method': method_value,
                '_csrfToken': csrf_token_value,
                'ad_form_data': ad_form_data_value,
                '_Token[fields]': token_fields_value,
                '_Token[unlocked]': token_unlocked_value,
            }
            query_string = dict_to_query_string(data2)

            headers2 = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Referer': shorturl,
                'X-Requested-With': 'XMLHttpRequest'
            }

            url_final_post = f"https://{short_domain}/{action_value}"
            response_final_post = session.post(url_final_post, data=query_string, headers=headers2)
            response_json = response_final_post.json()

            status = response_json.get('status')
            if status == 'success':
                response_link = response_json.get('url')
                return response_link
            else:
                logging.error(
                    f"{ERROR_COLOR} Error! 'url_final_post' no status 'success', GROUP: group_one, SHORTURL: {shorturl} {Style.reset}")
                return "https://error.error/error"
        except IndexError:
            logging.error(
                f"{ERROR_COLOR} Error! One of the required fields is missing, GROUP: group_one, SHORTURL: {shorturl} {Style.reset}")
            return "https://error.error/error"
    else:
        logging.error(f"{ERROR_COLOR} Error sending first post request: {response.status_code} {Style.reset}")
        return "https://error.error/error"
