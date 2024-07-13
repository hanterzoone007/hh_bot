import requests
import json
from objects import Vacancy, MySql, Area, Company,User,Resume,Config
import threading
import multiprocessing
import time
from xml.etree import ElementTree 
import datetime

config = Config('config.json')

parameters = config.parameters.parameters.raw_parameters

username = config.parameters.username
password = config.parameters.password

vacancies = []
resumes = []

lock_thread = threading.RLock()

mysql = MySql(config.parameters.MySql.ip,
              config.parameters.MySql.port,
              config.parameters.MySql.username,
              config.parameters.MySql.password)
mysql.connect()
user = User(username,
            password)



data_parasing = config.parameters.data_parsing.raw_parameters


def pagination_site_page(page,data_parsing):
    print('Page',page+1,'from',pages)
    data_parasing['page'] = page
    site_page = requests.get('https://api.hh.ru/vacancies',
            parameters,
            data=data_parsing)
    while not site_page.text.find('items')+1:
        site_page = requests.get('https://api.hh.ru/vacancies',
            parameters,
            data=data_parsing)
    
    lock_thread.acquire()
    vacancies.extend([ Vacancy(item['name'],
                                    item['url'],
                                    Area(item['area']['id'],item['area']['name']),
                                    item['id'],
                                    item['schedule']['name'],
                                    Company(item['employer']['id'],
                                            item['employer']['name'],
                                            item['employer']['url'])
                                            ,1)
                for item in json.loads(site_page.content)['items'] if item['id'] not in id_vacancie and item['employer']['trusted'] == True ] )
   
    lock_thread.release()

def insert_vacancy(vacancy:Vacancy):
    # print('insert Vacancy')
    if not mysql.query('select id from hh_bot.areas where id=%s;',[vacancy.object_area.id,]):
        mysql.query('insert into hh_bot.areas (id,name) values (%s,%s)',[(vacancy.object_area.id,vacancy.object_area.name_area)])
    if not mysql.query('select id from hh_bot.companyes where id=%s;',[vacancy.object_company.id,]):
        mysql.query('insert into hh_bot.companyes (id,name,url) values (%s,%s,%s)',[(vacancy.object_company.id,vacancy.object_company.company_name,vacancy.object_company.company_url),])  
    if not mysql.query('select id from hh_bot.vacancies where id=%s;',[vacancy.id,]):
        # print('Добавленна новая вакансия')
        mysql.query('insert into hh_bot.vacancies (id,url,name,id_area,id_company,schedule_vacancy,type) values (%s,%s,%s,%s,%s,%s,%s)',
                                                    [(vacancy.id,vacancy.url_vacancy,vacancy.name_vacancy,vacancy.object_area.id,vacancy.object_company.id,vacancy.schedule_vacancy,1),])
    

def get_resumes(user:User):
    r = user.session.get('https://vladivostok.hh.ru/applicant/resumes').text
    n = 0
    open('index.html',
         'w',
         encoding='utf-8'
         ).write(r)
    while r.find('<div class="applicant-resumes-card-wrapper noprint"')<0:
        r = user.session.get('https://vladivostok.hh.ru/applicant/resumes').text
        if n==10:
            exit()
        n+=1
    open('index.html',
         'w',
         encoding='utf-8'
         ).write(r)
        
    el = ElementTree.fromstring(r[r.find('<div class="applicant-resumes-card-wrapper noprint"')-96:r.find('<div class="applicant-resumes-card-wrapper noprint"')+r[r.find('<div class="applicant-resumes-card-wrapper noprint"')-96:][1:].find('<div class="bloko-column bloko-column_xs-4 bloko-column_s-8 bloko-column_m-8 bloko-column_l-10">')+1-96])
    resumes.extend([ Resume(i.attrib['href'][8:8+38],i[0].text) for i in el.findall('div/div/h3/a')])

def start_page_parsing(data_parsing,vacan):
    print('Get start page for start parsing')
    start_page = requests.get('https://api.hh.ru/vacancies',
                parameters,
                data=data_parsing)
    
    global pages
    pages = json.loads(start_page.content)['pages']
    
    print('Found',pages,'pages')
    
    threads = []
    for i in range(pages):
        t = threading.Thread(target=pagination_site_page,args=(i,data_parsing,))
        t.start()
        time.sleep(1)
        threads.append(t)
        
    for i in threads:
        i.join()
    vacan.extend(vacancies)
    

def process_start_page(num_process,vacan,id_vacancies):
    
    global id_vacancie
    id_vacancie = id_vacancies
    if num_process == 1:
        contries = requests.get('https://api.hh.ru/areas/countries',
                                parameters)
        countries = [i['id'] for i in json.loads(contries.content) if i['name']!= 'Россия']
        
        data_parasing['area'] = countries # process 1
    elif num_process == 2:
        data_parasing['text'] = 'python and description:удаленно' # process 2
    elif num_process == 3:
        data_parasing['schedule'] = 'remote'
    start_page_parsing(data_parasing,vacan)
    
def check_stage(id_vacacny:int,user:User,mysql:MySql):
    url_vacancy = 'https://hh.ru/vacancy/'+str(id_vacacny)
    response = user.session.get(url_vacancy).text
    text = response[response.find('<div class="vacancy-response__already-replied">'):response[response.find('<div class="vacancy-response__already-replied">'):].find('</div>')+7]
    pass

if __name__ == '__main__':
    print('Prepear for parsing')
    id_vacancies = [str(i[0]) for i in mysql.query('select id from hh_bot.vacancies')]
    vacancies_local = multiprocessing.Manager().list()
    processes = []
    for j in range(1,4):
        proc_str = multiprocessing.Process(target=process_start_page,args=(j,vacancies_local,id_vacancies))
        proc_str.start()
        processes.append(proc_str)

    for j in processes:
        j.join()
    
    vacancies.extend(vacancies_local)
    # end prepear stage
    
    if len(vacancies)>0:
        print(f'Start insert {len(vacancies)} vacancies')
        for i in vacancies:
            insert_vacancy(i)
            

    # subproc = multiprocessing.Process(target=update_vacancy) # вынести в отдельный файл исполнения
    # subproc.start()
    user.login()
    get_resumes(user)
    for resume in resumes:
        print('Check time',resume.name)
        if not mysql.query('select * from hh_bot.resumes where hash_id=%s',
                           [resume.id,]):
            time_update = resume.resume_up_datetime(user)
            mysql.query('insert into hh_bot.Resumes (hash_id,name,date_update) values (%s,%s,%s)',
                        [(resume.id,resume.name,time_update),])
        else:
            next_date = mysql.query('select date_next from hh_bot.resumes where hash_id=%s',
                                    [resume.id,]
                                    )[0][0]
            date_now = datetime.datetime.now()
            delta = date_now-next_date
            if delta.days>=0:
                time_update = resume.resume_up_datetime(user)
                mysql.query('update hh_bot.resumes set date_update=%s where hash_id=%s',
                            [(time_update.strftime("%Y-%m-%d %H:%M:%S"),resume.id,),])
        time.sleep(5)
        
    accepte_id = [Vacancy(id=i[0],
                          url=i[1],
                          name=i[2],
                          area=Area(i[3],mysql.query("select * from hh_bot.areas where id=%s",([i[3],],))[0][1]),
                          company=Company(*mysql.query("select * from hh_bot.companyes where id=%s",([i[4],],))[0]),
                          type=i[6],
                          schedule=i[5]
                          ) for i in mysql.query("select * from hh_bot.vacancies where type != 2 and name like '%python%' and name not like '%Преподаватель%' and name not like '%Java +%' and id not in (select id_vacancy from hh_bot.accept_vacancies) and id not in (select id_vacancy from hh_bot.error_accept_vacancies)")
                          ]
    

    for i in accepte_id:
        print('Want accept on vacancy',i.name_vacancy)
        for j in resumes:
            if j.name == 'Python Developer':
                print('Accept on vacancy',i.name_vacancy)
                print(i.accept(user,j,mysql))
                time.sleep(4)

    # subproc.join()
    print('End programm')
