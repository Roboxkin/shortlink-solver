from fastapi import FastAPI, Form, HTTPException
from contextlib import asynccontextmanager
from Proxy_List_Scrapper import Scrapper, ScrapperException
from concurrent.futures import ThreadPoolExecutor
from colored import Fore, Back, Style
import importlib
import random
import string
import asyncio
import aiofiles
import logging
import re
import os

HOSTS_FILE = 'C:\Windows\System32\drivers\etc\hosts'
HOSTS_ENTRIES_FILE = 'hosts_entries.txt'
ERROR_COLOR = str(f'{Style.BOLD}{Fore.rgb(255, 255, 255)}{Back.rgb(41, 13, 5)}')
WARNING_COLOR = str(f'{Style.BOLD}{Fore.rgb(255, 255, 255)}{Back.rgb(120, 81, 62)}')
SUCCESS_COLOR = str(f'{Style.BOLD}{Fore.rgb(255, 255, 255)}{Back.rgb(5, 41, 21)}')

logging.basicConfig(level=logging.INFO)

# (en) Regular expression pattern to match URLs
# (ru) Регулярное выражение для сопоставления URL
# noinspection RegExpRedundantEscape
URL_PATTERN = re.compile(r"(https?):/\/([^\/]+)/(.*)")

# (en) Dynamic list to store added hosts entries
# (ru) Динамический список для хранения добавленных записей hosts
added_entries = []


# (en) Function to read additional hosts entries from a file
# (ru) Функция для чтения дополнительных записей hosts из файла
def read_hosts_entries():
    try:
        if not os.path.isfile(HOSTS_ENTRIES_FILE):
            logging.warning(
                f"{WARNING_COLOR} WARNING: File {HOSTS_ENTRIES_FILE} does not exist. {Style.reset}")
            return []
        with open(HOSTS_ENTRIES_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    except IOError as e:
        logging.error(
            f"{ERROR_COLOR} ERROR: Error opening {HOSTS_ENTRIES_FILE}: {e} {Style.reset}")
        return []


# (en) Function to read existing hosts entries from the hosts file
# (ru) Функция для чтения существующих записей hosts из файла hosts
def read_existing_hosts_entries():
    try:
        with open(HOSTS_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    except IOError as e:
        logging.error(f"{ERROR_COLOR} ERROR: Error reading {HOSTS_FILE}: {e} {Style.reset}")
        return []


# (en) Function to add additional hosts entries to the hosts file
# (ru) Функция для добавления дополнительных записей hosts в файл hosts
def add_hosts_entries():
    global added_entries
    entries = read_hosts_entries()
    existing_entries = read_existing_hosts_entries()

    try:
        with open(HOSTS_FILE, "a", encoding="utf-8") as f:
            for entry in entries:
                if entry not in existing_entries:
                    f.write(entry + "\n")
                    added_entries.append(entry)
        logging.warning(f"{WARNING_COLOR} WARNING: >>> Hosts entries added. <<< {Style.reset}")
    except IOError as e:
        logging.error(f"{ERROR_COLOR} ERROR: Error adding hosts entries: {e} {Style.reset}")


# (en) Function to remove added hosts entries from the hosts file
# (ru) Функция для удаления добавленных записей hosts из файла hosts
def remove_hosts_entries():
    global added_entries
    entries_to_remove = read_hosts_entries()

    try:
        with open(HOSTS_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

        with open(HOSTS_FILE, "w", encoding="utf-8") as f:
            for line in lines:
                if line.strip() not in entries_to_remove:
                    f.write(line)

        added_entries = []
        logging.warning(f"{WARNING_COLOR} WARNING: >>> Hosts entries removed. <<< {Style.reset}")
    except IOError as e:
        logging.error(f"{ERROR_COLOR} ERROR: Error removing hosts entries: {e} {Style.reset}")


# (en) Lifespan context manager to add and remove hosts entries during application startup and shutdown
# (ru) Контекстный менеджер жизненного цикла для добавления и удаления записей hosts во время запуска и завершения работы приложения
@asynccontextmanager
async def lifespan(app: FastAPI):
    add_hosts_entries()
    yield
    remove_hosts_entries()


# (en) FastAPI application instance with lifespan context manager
# (ru) Экземпляр приложения FastAPI с контекстным менеджером жизненного цикла
app = FastAPI(lifespan=lifespan)

# (en) Lists of domains to replace
# (ru) Списки доменов для замены
first_list_domain = ["iir.la", "clk.wiki"]
second_list_domain = ["oii.la", "clk.kim"]

# (en) Create a dictionary for replacements
# (ru) Создаем словарь для замен
replacement_dict = dict(zip(first_list_domain, second_list_domain))


# (en) Function to replace the domain
# (ru) Функция для замены домена
async def replace_domain(url, replacement):
    # (en) Use regular expression to find the domain
    # (ru) Используем регулярное выражение для поиска домена
    pattern = re.compile(r'(https?://)([^/]+)(.*)')
    match = pattern.match(url)

    if match:
        # (en) Extract scheme, domain, and path from the URL
        # (ru) Извлекаем схему, домен и путь из URL
        scheme, domain, path = match.groups()

        # (en) Check if the domain is in the replacement dictionary
        # (ru) Проверяем, есть ли домен в словаре замен
        if domain in replacement:
            # (en) Get the new domain from the replacement dictionary
            # (ru) Получаем новый домен из словаря замен
            new_domain = replacement[domain]

            # (en) Construct the new URL with the replaced domain
            # (ru) Собираем новый URL с замененным доменом
            new_url = f"{scheme}{new_domain}{path}"
            logging.info(f"{SUCCESS_COLOR} SUCCESS REPLACE: {url} || {new_url} {Style.reset}")
            return new_url
        else:
            # (en) If the domain is not in the dictionary, return the original URL
            # (ru) Если домена нет в словаре, возвращаем исходный URL
            return url
    else:
        # (en) If the URL does not match the pattern, return the original URL
        # (ru) Если URL не соответствует шаблону, возвращаем исходный URL
        return url


# (en) Function to generate a random ID of a specified length
# (ru) Функция для генерации случайного ID заданной длины
async def generate_random_id(length):
    letters = string.ascii_lowercase
    rand_string = ''.join(random.choice(letters) for _ in range(length))
    return rand_string


# (en) Asynchronous function to write domain information to the no_group.txt file if the domain does not belong to a group
# (ru) Асинхронная функция для записи информации о домене в файл no_group.txt, если домен не принадлежит к группе
async def domain_record(record, protocol, short_domain, short_code):
    if record == "no_group":
        try:
            if os.path.isfile("no_group.txt"):
                async with aiofiles.open('no_group.txt', 'r+', encoding="utf-8") as file:
                    content = await file.read()
                    if short_domain not in content:
                        await file.write(f"{protocol}://{short_domain}/{short_code}\n")
                        logging.warning(
                            f"{WARNING_COLOR} Successfully Record no group >>> Added entry to file {protocol}://{short_domain}/{short_code} <<< {Style.reset}")
                        record_response = "no_group"
                    else:
                        record_response = "no_group"
            else:
                async with aiofiles.open('no_group.txt', 'w', encoding="utf-8") as file:
                    await file.write(f"{protocol}://{short_domain}/{short_code}\n")
                    logging.info(
                        f"{SUCCESS_COLOR} Successfully Record no group >>> Added entry to file {protocol}://{short_domain}/{short_code} <<< {Style.reset}")
                    record_response = "no_group"
        except Exception as e:
            logging.error(f"{ERROR_COLOR}Error writing to file: {e} {Style.reset}")
            raise HTTPException(status_code=500,
                                detail=f"{ERROR_COLOR} Error writing to file: {e} {Style.reset}")
    return record_response


# (en) Asynchronous function to parse the URL into protocol, domain, and code using a regular expression
# (ru) Асинхронная функция для разбора URL на протокол, домен и код с использованием регулярного выражения
async def domain_from_url(url):
    match = URL_PATTERN.match(url)
    if match:
        protocol = match.group(1)
        short_domain = match.group(2)
        short_code = match.group(3)
        return protocol, short_domain, short_code
    else:
        raise HTTPException(status_code=400,
                            detail=f"{ERROR_COLOR} Invalid URL format {Style.reset}")


# (en) Asynchronous function to check which group the domain belongs to
# (ru) Асинхронная функция для проверки, к какой группе принадлежит домен
async def check_donor_group(shorturl):
    shorturl = await replace_domain(shorturl, replacement_dict)
    protocol, short_domain, short_code = await domain_from_url(shorturl)

    group_one = ["ccurl.net"]
    group_two = []
    group_three = []
    group_four = []
    group_five = []
    group_six = []
    group_seven = []
    group_eight = []

    cloudflare = ["cety.app", "cuty.io"]
    blacklist = []
    error = ["error.error"]

    if short_domain in cloudflare:
        response_group = "cloudflare"
    elif short_domain in blacklist:
        response_group = "blacklist"
    elif short_domain in error:
        response_group = "error"
    elif short_domain in group_one:
        response_group = "group_one"
    elif short_domain in group_two:
        response_group = "group_two"
    elif short_domain in group_three:
        response_group = "group_three"
    elif short_domain in group_four:
        response_group = "group_four"
    elif short_domain in group_five:
        response_group = "group_five"
    elif short_domain in group_six:
        response_group = "group_six"
    elif short_domain in group_seven:
        response_group = "group_seven"
    elif short_domain in group_eight:
        response_group = "group_eight"
    else:
        response_group = await domain_record("no_group", protocol, short_domain, short_code)

    return response_group, short_domain


# (en) Asynchronous function to check the domain group and write the result to a file with the name corresponding to shortid
# (ru) Асинхронная функция для проверки группы домена и записи результата в файл с именем, соответствующим shortid
async def result_file(shortid, shorturl, faucet):
    faucet_domain = faucet

    while True:
        group, short_domain = await check_donor_group(shorturl)
        if group in ["cloudflare", "blacklist", "no_group", "error"]:
            logging.warning(
                f"{WARNING_COLOR} >>> Short Link {shorturl} is in the {group} <<< {Style.reset}")
            async with aiofiles.open(f"{shortid}.txt", "w", encoding="utf-8") as file:
                await file.write(f"Sorry, short link in the group {group}")
            return f"Sorry, short link in the group {group}"
        else:
            try:
                module_group = f"{group}"
                try:
                    module = importlib.import_module(module_group)
                except ImportError as e:
                    logging.error(f"{ERROR_COLOR} Error importing module: {e} {Style.reset}")
                    raise HTTPException(status_code=500,
                                        detail=f"{ERROR_COLOR} Error importing module: {e} {Style.reset}")

                with ThreadPoolExecutor() as executor:
                    resolved_url = await asyncio.get_event_loop().run_in_executor(executor, module.short_start,
                                                                                  shorturl, short_domain, shortid)

                protocol, resolved_domain, short_code = await domain_from_url(resolved_url)

                valid_domains = {faucet_domain, 'test.test'}
                if resolved_domain in valid_domains:
                    async with aiofiles.open(f"{shortid}.txt", "w", encoding="utf-8") as file:
                        await file.write(f"{resolved_url}")
                    return f"Successfully shortid = '{shortid}'"
                else:
                    shorturl = resolved_url
                    continue
            except AttributeError as e:
                logging.error(f"{ERROR_COLOR} Module does not have 'function': {e} {Style.reset}")
                raise HTTPException(status_code=500,
                                    detail=f"{ERROR_COLOR} Module does not have 'function': {e} {Style.reset}")


# (en) FastAPI POST route to handle short URL requests
# (ru) Маршрут FastAPI POST для обработки запросов коротких URL
@app.post("/short")
async def short(shorturl: str = Form(...), faucet: str = Form(...)):
    technical_break = "no"

    if technical_break == "yes":
        logging.info(f"{WARNING_COLOR} Sorry! technical break {Style.reset}")
        return "Sorry! technical break"

    if not shorturl or not faucet:
        raise HTTPException(status_code=400,
                            detail=f"{ERROR_COLOR} Sorry! Empty queries are not allowed {Style.reset}")

    shortid = await generate_random_id(10)
    asyncio.create_task(background_short_check(shortid, shorturl, faucet))
    logging.warning(f"{WARNING_COLOR} START ID: {shortid} {Style.reset}")
    return f"YOUR ID = {shortid}"


# (en) Asynchronous function to perform background checks
# (ru) Асинхронная функция для выполнения фоновых проверок
async def background_short_check(shortid, shorturl, faucet):
    async with semaphore:
        await result_file(shortid, shorturl, faucet)


# (en) FastAPI POST route to check the status of a short URL
# (ru) Маршрут FastAPI POST для проверки статуса короткого URL
@app.post("/check")
async def check(my_id: str = Form(...)):
    if not my_id:
        raise HTTPException(status_code=400,
                            detail=f"{ERROR_COLOR} Sorry! my_id empty queries are not allowed {Style.reset}")

    try:
        if os.path.isfile(f"{my_id}.txt"):
            async with aiofiles.open(f"{my_id}.txt", "r", encoding="utf-8") as file:
                first_line = await file.readline()
                solve_line = first_line.rstrip('\n')
            os.remove(f"{my_id}.txt")
            logging.info(
                f"{SUCCESS_COLOR} Successfully! ID: '{my_id}' SOLVE SHORT: '{solve_line}' {Style.reset}")
            return f"Successfully! solve short = {solve_line}"
        else:
            return "Short Link is not ready"
    except OSError as e:
        logging.error(f"Error reading or deleting file: {e}")
        raise HTTPException(status_code=500,
                            detail=f"{ERROR_COLOR} Error reading or deleting file: {e} {Style.reset}")


# (en) FastAPI POST route to update the proxy list
# (ru) Маршрут FastAPI POST для обновления списка прокси
@app.post("/proxy")
def check(category: str = Form(...)):
    if not category:
        raise HTTPException(status_code=400,
                            detail=f"{ERROR_COLOR} Sorry! category empty queries are not allowed {Style.reset}")

    try:
        scrapper = Scrapper(category=category, print_err_trace=False)
        data = scrapper.getProxies()

        if data and data.proxies:
            result = "\n".join([f"{proxy.ip}:{proxy.port}" for proxy in data.proxies])

            # Записываем результат в файл proxy_list.txt
            with open("proxy_list.txt", "w", encoding="utf-8") as file:
                file.write(result)
            logging.warning(f"{SUCCESS_COLOR}PROXY INFO: Proxies updated successfully {Style.reset}")
            return "Successfully"
        else:
            logging.error(f"{ERROR_COLOR} PROXY INFO: Proxy update error {Style.reset}")
            return "Error"

    except ScrapperException as e:
        raise HTTPException(status_code=500, detail=f"Scrapper error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


# (en) Main block to run the FastAPI application using Uvicorn
# (ru) Основной блок для запуска приложения FastAPI с использованием Uvicorn
if __name__ == '__main__':
    import uvicorn

    semaphore = asyncio.Semaphore(3)
    uvicorn.run(app, host="127.0.0.1", port=8000)
