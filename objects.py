import pymysql
import requests
import json
import datetime
import random
from typing import Any
import os
import time as tm

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
        # try:
        #     file = open('cookies.json','r',encoding='utf-8')
        #     for i in json.loads(file.read()):
        #         if self.session.cookies.get(i[0]):
        #             self.session.cookies[i[0]] = i[1]
        #         else:
        #             self.session.cookies.set(i[0],i[1])

                
        #     return True
        # except FileNotFoundError:
        data = {'_xsrf':self.session.cookies.get('_xsrf'),
                'username':self.username,
                'password':self.password,
                'accountType':'APPLICANT'}
        check = self.session.post("https://hh.ru/account/login?backurl=%2%",data=data)
        # print(check.status_code)
        # print(check.text)
        # if check.status_code == 200:
            # print('User Loginning')
            # return True
        # self.session.post("https://hh.ru/account/login?backurl=%2%",data=data)
        if json.loads(check.text)['hhcaptcha']['isBot'] == True:
            if os.path.isfile('./cookies.json') and os.stat('./cookies.json').st_birthtime > tm.time() - 1 * 86400:
                file = open('cookies.json','r',encoding='utf-8')
                for i in json.loads(file.read()):
                    self.session.cookies.set(i[0],i[1])
                return True
            os.remove('./cookies.json')
            key = json.loads(self.session.post("https://hh.ru/captcha?lang=RU").text)['key']
            r = self.session.get("https://hh.ru/captcha/picture",params={'key':key},stream=True)
            with open('i.png','wb') as f:
                for chunk in r:
                    f.write(chunk)
            captcha_text = input('Input chaptcha text (i.png): ')
            data['captchaText'] = captcha_text
            data['captchaKey'] = key
            data['captchaState'] = json.loads(check.text)['hhcaptcha']['captchaState']
            self.session.post("https://hh.ru/account/login?backurl=%2%",data=data).text
            del data['captchaText']
            del data['captchaKey']
            del data['captchaState']
        open('cookies.json','w',encoding='utf-8').write(json.dumps(self.session.cookies.items()))
        
        return True

        

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
                                         'undirectable': True })
        if result.status_code == 200:
            print('Success update resume',self.name)
            return time_update
        else:
            print('Error update')
            print(result.text)
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
        cover_letter = [f'''Здравствуйте,

Меня заинтересовала ваша вакансия "{self.name_vacancy}"

Так как я знаком с вашим стеком технологий и некоторые из них использовал в своих проектах, считаю, что я буду подходящим кандидатом. 

Я стремлюсь к постоянному саморазвитию и улучшению своих профессиональных навыков, готов к новым вызовам.''',
f'''Здравствуйте,

Меня заинтересовала ваша вакансия "{self.name_vacancy}". Так как я знаком с вашим стеком технологий и некоторые из них использовал в своих проектах, считаю, что я буду подходящим кандидатом.

Я стремлюсь к постоянному саморазвитию и улучшению своих профессиональных навыков, готов к новым вызовам. Ваша компания представляет для меня отличную возможность внести свой вклад и развиваться в инновационной среде.

Буду признателен за возможность обсудить детали вакансии и моего потенциального вклада в вашу команду.''',
f'''Здравствуйте,

Хотел бы выразить свой интерес к вашей вакансии "{self.name_vacancy}". Работа в вашей компании представляется мне отличной возможностью для профессионального и личностного роста.

Считаю, что мой опыт работы с вашим технологическим стеком и стремление к постоянному самосовершенствованию делают меня подходящим кандидатом для этой позиции.

Буду рад обсудить детали вакансии и моего потенциального вклада в вашу команду.''']
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