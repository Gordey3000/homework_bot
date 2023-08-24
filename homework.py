import logging
import os
import time
from http import HTTPStatus
import requests
import telegram
from dotenv import load_dotenv
from exceptions import HTTPRequestError

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename='program.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)

PRACTICUM_TOKEN = os.getenv('YA_TOKEN')
TELEGRAM_TOKEN = os.getenv('TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Функция проверяет доступность переменных."""
    try:
        return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])
    except Exception:
        return 'Ошибка доступа к переменным'


def send_message(bot, message):
    """Функция отправки сообщения в чат."""
    logging.error('Попытка отправки сообщения')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception:
        raise Exception('Ошибка отправки сообщения')
    else:
        logging.debug('Сообщение в чат отправлено')


def get_api_answer(timestamp):
    """Функция выполняет запрос к единственному эндпоинту API-сервиса."""
    payload = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(ENDPOINT,
                                         headers=HEADERS,
                                         params=payload)
    except Exception as error:
        logging.error(f'Эндпоинт {ENDPOINT} недоступен: {error}')
    if homework_statuses.status_code != HTTPStatus.OK:
        raise HTTPRequestError(homework_statuses)
    return homework_statuses.json()


def check_response(response):
    """Функция проверяет ответ API на соответствие."""
    if type(response) != dict:
        logging.error()
        raise TypeError('Структура данных не соответствует ожидаемой')
    if 'homeworks' not in response:
        logging.error()
        raise KeyError('Отсутствует ключ homeworks в ответе API')
    elif 'current_date' not in response:
        logging.error()
        raise KeyError('Отсутсвует ключ current_date в ответе API')
    elif type(response['homeworks']) != list:
        logging.error()
        raise TypeError('Ответы API приходт не в виде списка')
    return response['homeworks'][0]


def parse_status(homework):
    """Функция извлекает информацию о статусе домашней работы."""
    if 'homework_name' not in homework:
        logging.error()
        raise KeyError('Отсутствует ключ homework_name в ответе API')
    if 'status' not in homework:
        logging.error()
        raise Exception('Отсутствует ключ status в ответе API')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        logging.error()
        raise Exception('Неожиданный статус домашней работы:'
                        f' {homework_status}')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    if not check_tokens():
        logging.critical('Отсутствие обязательных переменных окружения.')
        return
    while True:
        try:
            response = get_api_answer(timestamp)
            if response:
                homework = check_response(response)
                if homework:
                    message = parse_status(check_response(response))
                    if message:
                        send_message(bot, message)
        except Exception as error:
            logging.error(f'Сбой в работе программы: {error}')
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
