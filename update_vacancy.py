from ssl import SSLError
import threading
import time
import requests
import json
from objects import MySql,Config 

config = Config('config.json')

parameters = config.parameters.parameters.raw_parameters

lock_thread = threading.RLock()

mysql = MySql(config.parameters.MySql.ip,
              config.parameters.MySql.port,
              config.parameters.MySql.username,
              config.parameters.MySql.password)
mysql.connect()

def responce_get(url, parameter):
    try:
        result = requests.get(url,parameter)
    except Exception:
        result = responce_get(url,parameter)
    return result

def check_open_vacancy(url):
    # print('Check vacancy',url)
    site_responce = responce_get(url,parameters)
    vacancy_site = json.loads(site_responce.content)

    if vacancy_site.get('type',{'id':'Not_found'})['id'] != 'open':
        lock_thread.acquire()
        print('Вакансия по ссылке:',url,'перестала быть актуальной')
        mysql.query('update hh_bot.vacancies set type=2 where url=%s',[url,])
        lock_thread.release()
    else:
        lock_thread.acquire()
        print('Вакансия по ссылке:',url,'актуальна')
        mysql.query('update hh_bot.vacancies set type=1 where url=%s',[url,])
        lock_thread.release()

def update_vacancy():
    print('Start update vacancies')
    select = mysql.query('select url from hh_bot.vacancies where now() >= timestampadd(hour,1,check_time) or check_time is Null;')
    if select:
        url_vacancies = [i[0] for i in mysql.query('select url from hh_bot.vacancies where now() >= timestampadd(hour,1,check_time) or check_time is Null;')]
        print("Check",len(url_vacancies),"vacancies")
        for index,i in enumerate(url_vacancies):
            t = threading.Thread(target=check_open_vacancy,
                                args=(i,)
                                ).start()
            if (index+1)%5 == 0:
                time.sleep(5)

if __name__ == '__main__':
    update_vacancy()
    print("End Update Vacancies")