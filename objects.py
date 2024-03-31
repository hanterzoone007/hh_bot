import pymysql
import requests
import json
import datetime
import random
from typing import Any

class MySql:

    def __init__(self,host,port,username,password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def connect(self):
        self.connect = pymysql.connect(host=self.host,
                                       port=self.port,
                                       user=self.username,
                                       password=self.password,
                                       autocommit=True)
    
    def query(self,query,params=None):
        with self.connect.cursor() as cursor:
            if params:
                cursor.executemany(query,params)
            else:
                cursor.execute(query)
            return cursor.fetchall()

class User:
    def __init__(self,
                 username:str,
                 password:str,
                 ):
        self.__username = username
        self.__password = password
        self.session = requests.session()
        self.session.headers.update({'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64)\
          AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
        self.session.get('https://hh.ru/')
    
    @property
    def username(self):
        return self.__username
    
    @property
    def password(self):
        return self.__password

    def login(self):
        data = {'_xsrf':self.session.cookies.get('_xsrf'),
                'username':self.username,
                'password':self.password,
                'accountType':'APPLICANT'}
        self.session.post("https://hh.ru/account/login?backurl=%2%",data=data)
        

class Base:
    def __init__(self,id):
        self.__id = id

    @property
    def id(self):
        return self.__id

class Company(Base):
    def __init__(self,id,name,url):
        super().__init__(id)
        self.company_name = name
        self.company_url = url

    def __str__(self):
        return self.company_name


class Resume(Base):
    def __init__(self,id,name):
        self.name = name
        super().__init__(id)
    
    def resume_up_datetime(self,
                           user:User,
                           ) -> datetime.datetime|bool:
        time_update = datetime.datetime.now()        
        result = user.session.post('https://vladivostok.hh.ru/applicant/resumes/touch',
                                   data={'_xsrf':user.session.cookies.get('_xsrf'),
                                         'resume': self.id,
                                         'undirectable': True }).status_code
        if result == 200:
            print('Success update resume',self.name)
            return time_update
        else:
            print('Error update')
            return False

class Area(Base):
    def __init__(self,id,name):
        super().__init__(id)
        self.name_area = name

    def __str__(self):
        return self.name_area        

class Vacancy(Base):
    def __init__(self,name:str,url:str,area:Area,id:int,schedule:str,company:Company,type):
        self.name_vacancy = name
        self.url_vacancy = url
        self.object_area = area
        self.object_company = company
        self.schedule_vacancy = schedule
        self.type = type
        super().__init__(id)


    def get_description( self ):
        self.description = json.loads(requests.get(self.url_vacancy).text)["description"]

    def set_status( self, id_status:int ):
        self.status = id_status

    def __str__(self):
        max_len = max([ len(i) for i in 'Vacancy: {}\nURL: {}\nArea: {}\nCompany: {}'.format(*self.__dict__.values()).split('\n')])
        return '*'*max_len+'\nVacancy: {}\nURL: {}\nArea: {}\nCompany: {}\n'.format(*self.__dict__.values())+'*'*max_len

    def get_params(self):
        return self.__dict__
    
    def accept(self, user:User,resume:Resume,mysql:MySql):
        cover_letter = [f'''Уважаемый рекрутер,

Я обращаюсь к вам, чтобы выразить свой интерес к вакансии {self.name_vacancy}. Мое разностороннее профессиональное образование и опыт работы позволяют мне принести дополнительную ценность в вашу компанию. Я готов показать, как мои уникальные навыки могут быть полезны для вашей команды на практике.

Буду рад обсудить возможность встречи и предоставить дополнительную информацию о себе. С нетерпением жду возможности поближе познакомиться с вашей компанией.

С уважением,
Владислав Динкилакер

'''+'Отправленно с помощью бота, подробности по почте в резюме',
f'''Уважаемый рекрутер,

Здравствуйте! Я заинтересован в возможности присоединиться к вашей компании в качестве {self.name_vacancy}. Мой опыт работы и профессиональные навыки позволяют мне быть ценным участником вашей команды. Буду рад предоставить дополнительную информацию о себе и обсудить возможное сотрудничество.

С уважением,
Владислав Динкилакер

'''+'Отправленно с помощью бота, подробности по почте в резюме',
f'''Уважаемый рекрутер,

Я заинтересован в возможности присоединиться к вашей компании в качестве {self.name_vacancy}. Мой опыт работы и профессиональные навыки позволяют мне эффективно выполнять поставленные задачи. Буду рад предоставить дополнительную информацию о себе и ответить на ваши вопросы.

С уважением,
Владислав Динкилакер

'''+'Отправленно с помощью бота, подробности по почте в резюме',
f'''Уважаемый рекрутер,

Я заинтересован в возможности присоединиться к вашей компании в качестве {self.name_vacancy}. Моя целеустремленность и профессиональные навыки позволяют мне быть ценным участником вашей команды. Готов обсудить возможность встречи и предоставить дополнительную информацию о своем опыте.

С уважением,
Владислав Динкилакер

'''+'Отправленно с помощью бота, подробности по почте в резюме',
f'''Уважаемый рекрутер,

Я обращаюсь к вам с просьбой рассмотреть меня на позицию {self.name_vacancy} в вашей компании. Я уверен, что мой опыт и навыки позволят мне эффективно внести вклад в работу вашей команды. Буду рад ответить на ваши вопросы и предоставить дополнительную информацию о себе.

С уважением,
Владислав Динкилакер

'''+'Отправленно с помощью бота, подробности по почте в резюме']
        accept_vacancy_params ={
        '_xsrf': user.session.cookies.get('_xsrf'),
        'vacancy_id': self.id,
        'resume_hash': resume.id,
        'ignore_postponed': 'true',
        'incomplete': 'false',
        'mark_applicant_visible_in_vacancy_country': 'false',
        'letter':random.choice(cover_letter), # сопроводительное письмо
        'lux': 'true',
        'withoutTest': 'no',
        'hhtmFromLabel': 'undefined',
        'hhtmSourceLabel': 'undefined',
        }

        result = user.session.post('https://vladivostok.hh.ru/applicant/vacancy_response/popup',data=accept_vacancy_params)
        
        if result.status_code == 200:
            id_resume_current = mysql.query("select id from hh_bot.resumes where hash_id=%s",([resume.id,],))[0][0]
            mysql.query('insert into hh_bot.accept_vacancies (id_vacancy, id_resume,id_stage) values (%s,%s,1);',([self.id,id_resume_current],))
            return 'Succes Accept Vacancy' 
        else:
            if bool(user.session.get('https://hh.ru/vacancy/'+str(self.id)).text.find('<div class="vacancy-response"><div class="vacancy-response__already-replied">')+1):
                id_resume_current = mysql.query("select id from hh_bot.resumes where hash_id=%s",([resume.id,],))[0][0]
                mysql.query('insert into hh_bot.accept_vacancies (id_vacancy, id_resume,id_stage) values (%s,%s,1);',([self.id,id_resume_current],))
                return (result.status_code,'Maybe you accept this vacancy. Check this url: https://hh.ru/vacancy/'+str(self.id))
            else:
                mysql.query('insert into hh_bot.error_accept_vacancies (id_vacancy,url_vacancy,error_text) values (%s,%s,%s)',([self.id,'https://hh.ru/vacancy/'+str(self.id),result.text],))
                res_text = json.loads(result.text)
                return res_text['error']
        


##### Cpnfig ####
class Config:
    def __init__(self,path):
        self.parameters = Parameters(json.loads(open(path,'r',encoding='utf-8').read()))
        



class Parameters:
    def __init__(self,value=None):
        self.raw_parameters = value
        # print(value)
        if value:
            if type(value) == str  or type(value) == int or type(value) == float:
                self.value = value
            elif type(value) == tuple or type(value) == list:
                for i in range(len(value)):
                    setattr(self,'_'+str(i),value[i])
            else:
                for i in value.keys():
                    setattr(self,i,value[i])
            

    def __setattr__(self, __name: str, __value: Any):
        if __name != 'raw_parameters':
            if type(__value) == tuple or type(__value) == list or type(__value) == dict:
                self.__dict__[__name] = Parameters(__value)
            else:
                self.__dict__[__name] = __value
        else:
            self.__dict__[__name] = __value