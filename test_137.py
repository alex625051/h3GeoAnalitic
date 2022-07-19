from google.oauth2 import service_account
import time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import psycopg2
from psycopg2 import Error
import datetime
import requests
from bs4 import BeautifulSoup as bs

oldCurr = '0'

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SERVICE_ACCOUNT_FILE = 'credentials.json'
SAMPLE_SPREADSHEET_ID = '1wblE8-OdpF3avmnZhDvsShxG6Z2EFvBpXgDyiZngSnU'
SAMPLE_RANGE_NAME = 'Лист1!A1:D'
POSTGRESuser="postgres"
POSTGRESpassword="111111"
POSTGREShost="127.0.0.1"
POSTGRESport="2233"
POSTGRESdatabase="postgres"


credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)


def getValuesFromSheet():
    try:
        service = build('sheets', 'v4', credentials=credentials)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range=SAMPLE_RANGE_NAME).execute()
        values = result.get('values', [])
        return values
    except HttpError as err:
        print(err)


def updateTable(data=[], usd=0.0):
    connection = None

    data = [(int(row[0]), int(row[1]), float(row[2].replace(',', '.')), row[3],
             '{:.2}'.format(float(row[2].replace(',', '.')) * usd)) for row in data]
    try:
        # Подключиться к существующей базе данных
        connection = psycopg2.connect(user=POSTGRESuser,
                                      # пароль, который указали при установке PostgreSQL
                                      password=POSTGRESpassword,
                                      host=POSTGREShost,
                                      port=POSTGRESport,
                                      database=POSTGRESdatabase)

        cursor = connection.cursor()
        cursor.execute('SELECT "заказ №"  from test')
        current_rows = tuple([a[0] for a in cursor.fetchall()])
        new_rows = tuple([a[1] for a in data])
        cursor.execute(f'DELETE from test WHERE "заказ №" NOT IN {new_rows} ')
        for order in data:
            cursor.execute(f'DELETE from test WHERE "заказ №"= {order[1]} ')
        postgres_insert_query = f""" INSERT INTO test ("№", "заказ №", "стоимость" , "срок поставки","стоимость в руб.")
                                           VALUES (%s,%s,%s,%s,%s)"""
        cursor.executemany(postgres_insert_query, data)
        connection.commit()
        count = cursor.rowcount
        print(count, "Данные успешно добавлены в таблицу test")

    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Соединение с PostgreSQL закрыто")


def currency_parsing():
    global oldCurr

    def getCurrentDate():
        ret = {}
        """"
        Получаем текущию дату
        и по умолчанию в параметрах устанавливаем её.
        """
        dt = datetime.datetime.now()
        ret['day_h'] = str(dt.day)
        ret['month_h'] = str(dt.month)
        ret['year_h'] = str(dt.year)
        return ret

    """
    парсим курсы валют по API ЦБ РФ.
    Получаем дату для получения курса валют.
    Если число или месяц от 1-9 тогда мы добавляем значения '0'
    для правильного запроса формата 'dd/mm/yyyy'
    """;
    currentDate = getCurrentDate();
    d = currentDate['day_h']
    m = currentDate['month_h']
    y = currentDate['year_h']
    if len(d) == 1:
        d = '0' + d
    if len(m) == 1:
        m = '0' + m

    # Делаем запрос на сайт,передаем ему параметр.
    url = 'http://www.cbr.ru/scripts/XML_daily.asp?'
    params = {
        'date_req': '{0}/{1}/{2}'.format(d, m, y)
    }

    request = requests.get(url, params)
    soup = bs(request.content, 'xml')
    if soup:
        find_usd = soup.find(ID='R01235').Value.string
        oldCurr = find_usd
    else:
        if oldCurr > 0:
            find_usd = oldCurr
        else:
            find_usd = '60'
    return float(find_usd.replace(',', '.'))


def main():
    while True:
        valuesFromSheet = getValuesFromSheet()
        valuesFromSheet_data = valuesFromSheet[1::]
        usd = currency_parsing()
        updateTable(usd=usd, data=valuesFromSheet_data)
        time.sleep(5)


if __name__ == '__main__':
    main()
