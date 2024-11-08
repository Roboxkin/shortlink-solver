import requests
import time
import logging
from colored import Fore, Back, Style

XEVIL_KEY = ''
XEVIL_IP = '127.0.0.1'
TIMEOUT = 200
ERROR_COLOR = str(f'{Style.BOLD}{Fore.rgb(255, 255, 255)}{Back.rgb(41, 13, 5)}')
WARNING_COLOR = str(f'{Style.BOLD}{Fore.rgb(255, 255, 255)}{Back.rgb(120, 81, 62)}')
SUCCESS_COLOR = str(f'{Style.BOLD}{Fore.rgb(255, 255, 255)}{Back.rgb(5, 41, 21)}')

logging.basicConfig(level=logging.INFO)

# (en) Function to solve captcha based on its type
# (ru) Функция для решения капчи в зависимости от её типа
def solve_captcha(captcha_type, key, url, shortid):
    if captcha_type == 'ReCaptchaV2':
        return solve_recaptcha(key, url, shortid)
    elif captcha_type == 'ReCaptchaV3':
        return solve_recaptcha(key, url, shortid, version='v3')
    elif captcha_type == 'hCaptcha':
        return solve_hcaptcha(key, url, shortid)
    elif captcha_type == 'normal':
        return solve_normal_captcha(url, shortid)
    else:
        logging.error(f"{ERROR_COLOR} Unknown captcha type: {captcha_type} {Style.reset}")
        return None

# (en) Function to solve ReCaptcha
# (ru) Функция для решения ReCaptcha
def solve_recaptcha(sitekey, url, shortid, version='v2'):
    data = {
        'key': XEVIL_KEY,
        'method': 'userrecaptcha',
        'googlekey': sitekey,
        'pageurl': url,
        'version': version
    }

    if version == 'v3':
        data['action'] = 'action'
        data['min_score'] = 0.3

    try:
        response = requests.post(
            f'http://{XEVIL_IP}/in.php',
            data=data
        )
        response.raise_for_status()
        request_data = response.text

        if 'ERROR_NO_SLOT_AVAILABLE' in request_data:
            logging.error(f"{ERROR_COLOR} ERROR NO SLOT AVAILABLE | WAIT 10 sec ... {Style.reset}")
            time.sleep(10)
            return solve_recaptcha(sitekey, url, shortid, version)
        elif 'ERROR_WRONG_USER_KEY' in request_data:
            logging.error(f"{ERROR_COLOR} ERROR WRONG USER KEY {Style.reset}")
            time.sleep(2)
            return None
        elif 'PROXY BANNED' in request_data:
            logging.warning(f"{WARNING_COLOR} PROXY BANNED | WAIT 2 sec ... {Style.reset}")
            time.sleep(2)
            return solve_recaptcha(sitekey, url, shortid, version)
        elif 'ERROR_GOOGLEKEY' in request_data:
            logging.error(f"{ERROR_COLOR} ERROR SITEKEY GOOGLE RECAPTCHA {Style.reset}")
            time.sleep(2)
            return None
        elif 'ERROR_PAGEURL' in request_data:
            logging.error(f"{ERROR_COLOR} ERROR PAGEURL {Style.reset}")
            time.sleep(2)
            return None

        print(request_data)
        idcap = request_data.split('|')[1]
        time_wait = 5

        while True:
            response = requests.get(
                f'http://{XEVIL_IP}/res.php',
                params={
                    'key': XEVIL_KEY,
                    'action': 'get',
                    'id': idcap,
                    'json': 0
                }
            )
            response.raise_for_status()
            request_data = response.text

            if 'CAPCHA_NOT_READY' in request_data:
                logging.info(f"{WARNING_COLOR} ID: {shortid} | RECAPTCHA SOLVED: {time_wait} sec... {Style.reset}")
                time.sleep(5)
                time_wait += 5
                if time_wait > 250:
                    logging.error(f"{ERROR_COLOR} ID: {shortid} | Failed to solve the captcha {Style.reset}")
                    time.sleep(2)
                    return solve_recaptcha(sitekey, url, shortid, version)
            elif 'OK|' in request_data:
                code = request_data.split('OK|')[1]
                logging.info(f"{SUCCESS_COLOR} ID: {shortid} | Success | Recaptcha solved {Style.reset}")
                return code
            else:
                logging.error(f"{ERROR_COLOR} ID: {shortid} | Recaptcha not solved Let's try again {Style.reset}")
                time.sleep(5)
                return solve_recaptcha(sitekey, url, shortid, version)

    except requests.RequestException as e:
        logging.error(f"{ERROR_COLOR} ID: {shortid} | Error solving captcha: {e} {Style.reset}")
        return None

# (en) Function to solve hCaptcha
# (ru) Функция для решения hCaptcha
def solve_hcaptcha(sitekey, url, shortid):
    try:
        response = requests.post(
            f'http://{XEVIL_IP}/in.php',
            data={
                'key': XEVIL_KEY,
                'method': 'hcaptcha',
                'sitekey': sitekey,
                'pageurl': url
            }
        )
        response.raise_for_status()
        request_data = response.text

        if 'ERROR_' in request_data:
            logging.error(f"{ERROR_COLOR} Service is temporarily unavailable !!! {Style.reset}")
            time.sleep(10)
            return solve_hcaptcha(sitekey, url, shortid)

        idcap = request_data.split('|')[1]
        time_wait = 5

        while True:
            response = requests.get(
                f'http://{XEVIL_IP}/res.php',
                params={
                    'key': XEVIL_KEY,
                    'action': 'get',
                    'id': idcap,
                    'json': 0
                }
            )
            response.raise_for_status()
            request_data = response.text

            if 'CAPCHA_NOT_READY' in request_data:
                logging.warning(f"{WARNING_COLOR} ID: {shortid} | hCaptcha solved: {time_wait} sec. {Style.reset}")
                time.sleep(5)
                time_wait += 5
                if time_wait > 250:
                    logging.warning(f"{WARNING_COLOR} ID: {shortid} | Didn't have time to solve hCaptcha!!! {Style.reset}")
                    time.sleep(2)
                    return solve_hcaptcha(sitekey, url, shortid)
            elif 'OK|' in request_data:
                code = request_data.split('OK|')[1]
                logging.warning(f"{SUCCESS_COLOR} ID: {shortid} | hCaptcha solved successfully! {Style.reset}")
                return code
            else:
                logging.warning(f"{WARNING_COLOR} ID: {shortid} | hCaptcha not solved Let's try again {Style.reset}")
                time.sleep(5)
                return solve_hcaptcha(sitekey, url, shortid)

    except requests.RequestException as e:
        logging.error(f"{ERROR_COLOR} Error solving captcha: {e} {Style.reset}")
        return None

# (en) Function to solve normal captcha
# (ru) Функция для решения обычной капчи
def solve_normal_captcha(file_path, shortid):
    try:
        with open(file_path, 'rb') as file:
            response = requests.post(
                f'http://{XEVIL_IP}/in.php',
                files={'file': file},
                data={
                    'key': XEVIL_KEY,
                    'method': 'post'
                }
            )
            response.raise_for_status()
            request_data = response.text

            if 'ERROR_NO_SLOT_AVAILABLE' in request_data:
                logging.error(f"{ERROR_COLOR} Service is temporarily unavailable !!! {Style.reset}")
                time.sleep(10)
                return solve_normal_captcha(file_path, shortid)
            elif 'ERROR_WRONG_USER_KEY' in request_data:
                logging.error(f"{ERROR_COLOR} Not specified or invalid APIKEY !!! {Style.reset}")
                time.sleep(2)
                return None
            elif 'PROXY BANNED' in request_data:
                logging.warning(f"{WARNING_COLOR} ID: {shortid} | PROXY BANNED | WAIT 2 sec ... {Style.reset}")
                time.sleep(2)
                return solve_normal_captcha(file_path, shortid)

            idcap = request_data.split('|')[1]
            time_wait = 5

            while True:
                response = requests.get(
                    f'http://{XEVIL_IP}/res.php',
                    params={
                        'key': XEVIL_KEY,
                        'action': 'get',
                        'id': idcap
                    }
                )
                response.raise_for_status()
                request_data = response.text

                if 'CAPCHA_NOT_READY' in request_data:
                    logging.info(f"{SUCCESS_COLOR} ID: {shortid} | Captcha solved: {time_wait} sec. {Style.reset}")
                    time.sleep(5)
                    time_wait += 5
                    if time_wait > 250:
                        logging.error(f"{ERROR_COLOR} ID: {shortid} | Failed to solve the captcha {Style.reset}")
                        time.sleep(2)
                        return solve_normal_captcha(file_path, shortid)
                elif 'OK|' in request_data:
                    code = request_data.split('OK|')[1]
                    logging.info(f"{SUCCESS_COLOR} ID: {shortid} | Captcha solved successfully! {Style.reset}")
                    return code
                else:
                    logging.warning(f"{WARNING_COLOR} ID: {shortid} | Captcha not solved Let's try again {Style.reset}")
                    time.sleep(5)
                    return solve_normal_captcha(file_path, shortid)

    except requests.RequestException as e:
        logging.error(f"{ERROR_COLOR} Ошибка при решении капчи: {e} {Style.reset}")
        return None