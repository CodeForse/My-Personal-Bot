import telebot
import requests
import numpy as np
from telebot import types
from datetime import time,date, datetime,timedelta
import schedule

import os
from pandas import array
from typing import List
import pydantic

from threading import Thread
from time import sleep, strptime
from aiogram import types
import json


# import pywhatkit
# import keyboard

import validators

 
TOKEN = "5539956122:AAGVPjHYFI5-mN0OXuVmkNpO3wzruU-8uuU"
api_key='6648940add8b78a3efaac738232a7aaf' 
bot=telebot.TeleBot(TOKEN)

scheduleRelatedWords=np.array(['schedule','sc','расписание','расп', 'рп'])
forecast_related_words=np.array(['weather','погода','weather forecast','прогноз погоды'])

class remainder_everyday(pydantic.BaseModel):
    id_chat:int
    remiand_text: str
    activation_time: str
class remainder_date(pydantic.BaseModel):
    remind_text: str
    activation_date: datetime
class Instruction(pydantic.BaseModel):
    key: str
    message_id: int 
#idea: call key and bot replies the message (text/photo/video/voice) it is needed for saving instructions inititally

def getWeatherForecastToday(city: str):  
    #https://api.openweathermap.org/data/2.5/onecall?lat=43.25&lon=76.95&units=metric&lang=ru&exclude=current,hourly,minutely&appid=6648940add8b78a3efaac738232a7aaf
    #to get daily not current
    urlApi=f'https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&lang=ru&appid={api_key}'
    request=requests.get(urlApi)
    data=request.json()
    descript=data['weather'][0]['description']
    temp=round(data['main']['temp'])
    return 'На улице '+str(temp)+'\nПогода: '+descript
    
def isTimeFormat(input):
    
    try:
        strptime(input, '%H:%M')
        return True
    except ValueError:
        return False
def isDateFormat(input):
    try:
        datetime.strptime(input,'%d.%m.%Y')
        return True
    except:
        return False

def getRemindsList(id):
    try:
        file=open('remainds_'+str(id)+'.json','r')
        strjson='['+file.read()+']'
        file.close()
        return pydantic.parse_obj_as(List[remainder_everyday],json.loads(strjson))
    except: bot.send_message(id,'No remainds found')
def getNotificationsList(id):
    try:
        file=open('notification_'+str(id)+'.json','r')
        strjson='['+file.read()+']'
        file.close()
        return pydantic.parse_obj_as(List[remainder_date],json.loads(strjson))
    except: bot.send_message(id,'No notifications found')

def getInstructionList(id):
    
        file=open('instructions_'+str(id)+'.json','r')
        strjson='['+file.read()+']'
        file.close()
        return pydantic.parse_obj_as(List[Instruction],json.loads(strjson))
def is_in_listInstr(chat_id:int,tag:str):
    try:
        file=open('instructions_'+str(chat_id)+'.json','r')
        strjson=file.read()
        file.close()
        return tag in strjson
    except: return False
def return_id_from_tag(chat_id:int,tag:str):
    inst_list=getInstructionList(chat_id)

    return next((it for it in inst_list if it.key==tag), None).message_id       
     
def morning_mess():
    for fname in os.listdir('.'):
        if os.path.isfile(fname) and 'remainds_'in fname :
            id=fname[fname.find('_')+1:fname.find('.')]
            bot.send_message(id,'Доброе утро)')
            bot.send_message(id,getWeatherForecastToday('Almaty'))
    


@bot.message_handler(commands=['buttons','control'])
def buttons(message):
    markup= types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    SendSchedule=types.InlineKeyboardButton('Schedule')
    SendWeatherForecast=types.InlineKeyboardButton('Weather')
    markup.add(SendSchedule)
    markup.add(SendWeatherForecast)
    bot.send_message(message.chat.id, 'Check it out', reply_markup=[markup])

#should be checked every 7:00 of a day - compare if the day is the day    
def notification_scedules():
    for fname in os.listdir('.'):    # change directory if needed
        if os.path.isfile(fname) and 'notification_'in fname :  
            
            
                if os.stat(fname).st_size!=0:
                    file=open(fname,'r') 
                    strjson='['+file.read()+']'
                    file.close()

                    notifs=pydantic.parse_obj_as(List[remainder_date],json.loads(strjson))
                    tmp=len(notifs)
                    indexes_toDel=[]
                    for notif in notifs:
                        if(notif.activation_date.date() <= datetime.today().date()):
                            id=fname[fname.find('_')+1:fname.find('.')]
                            bot.send_message(id,'Не забудь: '+notif.remind_text)
                            indexes_toDel.append(notifs.index(notif))

                    indexes_toDel.sort(reverse=True) #this way i pop without ruining next index pop
                    for index in indexes_toDel:                            
                        notifs.pop(index)                            
                    if len(notifs)!=tmp:
                        file=open(fname,'w+')#not optimized
            
            
                        i=0
                        for notif in notifs:# add order by time would be cool
                            if(i>0):
                                file.write(',')
                            else: i+=1
                            file.write  (remainder_date(remind_text=notif.remind_text,activation_date=notif.activation_date).json())
                        
                        file.close()


def schedules():
#    optimized for working for few people, different system if many users
    schedule.clear('daily-tasks')
    for fname in os.listdir('.'):    # change directory if needed
        if os.path.isfile(fname) and 'remainds_'in fname :   
            with open(fname) as file:
                if os.stat(fname).st_size!=0:
                    
                    strjson='['+file.read()+']'
            
                    reminds=pydantic.parse_obj_as(List[remainder_everyday],json.loads(strjson))
        
                    for rem in reminds:
            
                        schedule.every().day.at(rem.activation_time).do(bot.send_message,rem.id_chat,rem.remiand_text).tag('daily-tasks').tag(fname[len('remainds_'):fname.find('.')])
                            
    schedule.every().day.at('07:00').do(morning_mess).tag('daily-tasks')
    schedule.every().day.at('07:00').do(notification_scedules).tag('daily-tasks')
               
@bot.message_handler(commands=['allinst'])
def send_all_inst(message: types.Message):
    try:
        list=getInstructionList(message.chat.id)
        all_inst='-----All Instructions-----\n'
        i=1
        for obj in list:
            all_inst+=str(i)+') '+obj.key+'\n'
        all_inst+='\nIf you wish to delete some, write in a format >delete inst 1<'
        bot.send_message(message.chat.id,all_inst)
    except:
        bot.send_message(message.chat.id,'no instructions seems to be')
     
@bot.message_handler(commands=['all_reminds','вся_рутина','allrem'])
def get_all_reminds(message:types.Message):
    try:
        reminds=getRemindsList(message.chat.id)
        # it's ok if not many people but optimization sucks
        all_reminds='-----All Reminds-----\n'
        i=1
        for remind in reminds: #with db would be more cool
            all_reminds+=str(i)+') '+remind.remiand_text+' at '+remind.activation_time+'\n'
            i+=1
        all_reminds+='\nIf you wish to delete some, write in a format >delete rem 1<'
        bot.send_message(message.chat.id,all_reminds)
    except: bot.send_message(message.chat.id, 'no reminds seems to be')

@bot.message_handler(commands=['start','help'])
def starter(message:types.Message):
    text='Привет, '+message.chat.first_name+'.\n'\
        +'Я телеграмм бот by AA. \nВот что я могу:\n'\
        +'1)Чтобы добавить ежедневное напоминание напишите в формате >23:00 text_to_do<\n'\
        +'2)Чтобы получить весь список напоминаний или удалить используйте команду - /allrem\n'\
        +'3)Чтобы добавить разовое напоминание через какое-то время можно использовать >in n days text_to_do< или назначить дату>05.07.2022 text_to_do<\n'\
        +'4)Чтобы получить весь список разовых напоминаний или удалить используйте команду - /allnotif\n'\
        +'5)Могу хранить фотографию вашего расписания и отправлять погоду команда - /control\n'

        
    bot.send_message(message.chat.id,text)

@bot.message_handler(commands=['all_notif','all_notifiactions','allnotif','все_напоминания'])   
def get_all_notif(message:types.Message):
    try:
        notifs=getNotificationsList(message.chat.id)
        all_reminds='-----All Notifications-----\n'
        i=1
        for remind in notifs: #with db would be more cool
            all_reminds+=str(i)+') '+remind.remind_text+' on '+remind.activation_date.strftime('%d.%m.%Y')+'\n'
        
            i+=1
        all_reminds+='\nIf you wish to delete some, write in a format >delete notif 1<'
        bot.send_message(message.chat.id,all_reminds)
    except: bot.send_message(message.chat.id, 'no notifs seems to be')

@bot.message_handler(content_types='text')
def getUserText(message: types.Message):
    real_split=str(message.text).split()
    text_split=real_split[0]

    if(message.text.lower()=='set schedule'):
        bot.send_message(message.chat.id,'okey, send me a photo of the schedule')
        dialogChain=open('dialogChain_'+str(message.chat.id)+'.txt','w+') #yeah костыль
        dialogChain.write('set schedule')
        dialogChain.close()
        
    elif(scheduleRelatedWords.__contains__(message.text.lower())): #vice verse would be more cool
        bot.send_message(message.chat.id,'wait a sec')
        try:
            schedulePic=open('schedule_'+str(message.chat.id)+'.jpg','rb')
            bot.send_photo(message.chat.id,schedulePic) #obtain schedule from the server
        except: 
            bot.send_message(message.chat.id,'Before you should set the schedule-photo')
            dialogChain=open('dialogChain_'+str(message.chat.id)+'.txt','w+') #yeah костыль # на продакшине понял что все сразу кидают фото вместо команды даже я
            dialogChain.write('set schedule')
            dialogChain.close()
    
    elif(isTimeFormat(text_split)): #setter of remainder in format time + text
        remaind_text=message.text.replace(text_split,'',1)
        hour_n_minute=text_split.split(':')
        if(len(hour_n_minute[0])==1): text_split='0'+hour_n_minute[0]+':'+hour_n_minute[1]
        
        
        try:
            if(remaind_text[0]==' '):  remaind_text=remaind_text[1:]
            filename='remainds_'+str(message.chat.id)+'.json'
            try:file=open(filename,'a+')
            except:file=open(filename,'w+') #create file if needed
            if(os.stat(filename).st_size!=0):
                # file.seek(file.tell()-1, os.SEEK_END)
                # file.write('')
                file.write(',')
            # else: file.write('[')
            file.write  (remainder_everyday(id_chat=message.chat.id,remiand_text= remaind_text,activation_time= text_split).json())
            # file.write(']')
            file.close()
            bot.send_message(message.chat.id,'Окей, я буду напоминать каждый день')
            text_split=str(message.text).split()[0]

            schedules()  # now u don't need to reload app
        except: bot.send_message(message.chat.id,'Notification itself is not defined, Try again')
    
    # deleter of reminds
    elif('delete rem' in message.text.lower() and message.text.lower().split().__len__()==3):
        try:
            remNum=int(message.text.lower().split()[2])-1
            reminds=getRemindsList(message.chat.id)
            reminds.pop(remNum)
            file=open('remainds_'+str(message.chat.id)+'.json','w+')#not optimized
            
            
            i=0
            for remind in reminds:# add order by time would be cool
                if(i>0):
                    file.write(',')
                else: i+=1
                file.write  (remainder_everyday(id_chat=remind.id_chat,remiand_text= remind.remiand_text,activation_time= remind.activation_time).json())
            
            bot.send_message(message.chat.id,'done')
            file.close()
            
            schedules()
        except:
             bot.send_message(message.chat.id,'the remind is not found or error in request')

    # elif('play music' in message.text.lower()):#пасхалка?
    #     try:
    #         search_video=message.text[message.text.lower().find('play music')+len('play music'):]
            
    #         pywhatkit.playonyt(search_video)
    #     except: bot.send_message(message.chat.id,'nothing to be found')
    # elif('close music' == message.text.lower()):
    #     try:
    #         keyboard.press_and_release('ctrl+w')
    #     except: bot.send_message(message.chat.id,'nothing to be closed')
    
    #setter of notification
    elif(isDateFormat(text_split) and datetime.strptime(text_split,'%d.%m.%Y').date()>=datetime.today().date()):
        remaind_text=message.text.replace(text_split,'',1)

        try:
            if(remaind_text[0]==' '):  remaind_text=remaind_text[1:]
            filename='notification_'+str(message.chat.id)+'.json'
            try:file=open(filename,'a+')
            except:file=open(filename,'w+') #create file if needed
            if(os.stat(filename).st_size!=0):
                
                file.write(',')
            date=datetime.strptime(text_split,'%d.%m.%Y')
            date=date.replace(hour=7,minute=0)
            file.write  (remainder_date(remind_text= remaind_text,activation_date= date).json())
            
            file.close()
            bot.send_message(message.chat.id,'Окей, я напомню')
            schedules()
        except: bot.send_message(message.chat.id,'Notification itself is not defined, Try again')
    elif(text_split.lower()=='in' and (real_split[2].lower()=='days' or real_split[2].lower()=='day') and real_split[1].isdigit()):
        diff=int(real_split[1])
        
        date=datetime.today()+timedelta(diff)
        
        remaind_text=message.text[message.text.find(real_split[2])+len(real_split[2]):]

        try:
            if(remaind_text[0]==' '):  remaind_text=remaind_text[1:]
            filename='notification_'+str(message.chat.id)+'.json'
            try:file=open(filename,'a+')
            except:file=open(filename,'w+') #create file if needed
            if(os.stat(filename).st_size!=0):
                
                file.write(',')
            
            file.write  (remainder_date(remind_text= remaind_text,activation_date= date).json())
            
            file.close()
            bot.send_message(message.chat.id,'Окей, я напомню')
            schedules()
        except: bot.send_message(message.chat.id,'Notification itself is not defined, Try again')
        
    #delete notification by number
    elif('delete notif' in message.text.lower()and message.text.lower().split().__len__()==3):
        try:
            remNum=int(message.text.lower().split()[2])-1
            reminds=getNotificationsList(message.chat.id)
            reminds.pop(remNum)
            file=open('notification_'+str(message.chat.id)+'.json','w+')#not optimized
            
            # filename='_'+str(message.chat.id)+'.json'
            i=0
            for remind in reminds:# add order by time would be cool
                if(i>0):
                    file.write(',')
                else: i+=1
                file.write  (remainder_date(remind_text=remind.remind_text,activation_date=remind.activation_date).json())
            bot.send_message(message.chat.id,'done')
            file.close()
            
            #call schedules of notification
            schedules()
        except:
             bot.send_message(message.chat.id,'the remind is not found or error in request')
    elif(validators.url(message.text) and 'https://youtu.be/' in message.text): #for regular person to save, so i'll not cut regular part of any youtube link
        try:file=open('youtube_'+str(message.chat.id)+'.txt','a+')
        except:file=open('youtube_'+str(message.chat.id)+'.txt','w+')
        file.write(message.text+'\n')
        bot.send_message(message.chat.id,'Топ видео, я сохраню))')
    elif(message.text.lower() in forecast_related_words):
        bot.send_message(message.chat.id,getWeatherForecastToday('Almaty'))
   
   #setter instruction
    elif(message.text[0]=='"' and message.text[-1]=='"'):
        if(not is_in_listInstr(message.chat.id,message.text[1:-1])):
            bot.send_message(message.chat.id,'Инструкция под тэгом: '+message.text[1:-1])
            bot.send_message(message.chat.id,"Осталось только ее написать/прислать/сказать")
            bot.register_next_step_handler(message,set_instruction,message.text[1:-1])
        else: bot.send_message(message.chat.id,'С данным тэгом уже сущесвтует привязка')
    #getter instruction
    elif(is_in_listInstr(message.chat.id, message.text)):
        bot.send_message(message.chat.id,reply_to_message_id=return_id_from_tag(message.chat.id,message.text),text='Here we go')
    #delete instruction
    elif('delete inst' in message.text.lower() and message.text.lower().split().__len__()==3):
        try:
            instNum=int(message.text.lower().split()[2])-1
            insts=getInstructionList(message.chat.id)
            insts.pop(instNum)
            file=open('instructions_'+str(message.chat.id)+'.json','w+')#not optimized
                
                
            i=0
            for inst in insts:# add order by time would be cool
                if(i>0):
                    file.write(',')
                else: i+=1
                file.write(inst.json())
                
            bot.send_message(message.chat.id,'done')
            file.close()
        except:
            bot.send_message(message.chat.id,'the instructions is not found or error in request')

        
    
    else: bot.reply_to(message,message.text)
     
def set_instruction(message: types.Message,tag):
    
    # bot.send_message(message.chat.id,"соси камса",reply_to_message_id=message.message_id-2)
    # bot.send_message(message.chat.id,tag)

    filename='instructions_'+str(message.chat.id)+'.json'
    try: file=open(filename,'a+')
    except: file=open(filename,'w+')
    if(os.stat(filename).st_size!=0):
                
                file.write(',')
    file.write(Instruction(key=tag,message_id=message.message_id).json())
    bot.send_message(message.chat.id,'Сохранено')

    file.close()

@bot.message_handler(content_types='photo')   
def usingPhoto(message:types.Message):
    dialogChain=open('dialogChain_'+str(message.chat.id)+'.txt','r') 
    if(dialogChain.read().__contains__('set schedule')): #set schedule to the server, so we can use it later
        raw=message.photo[3].file_id
        path='schedule_'+str(message.chat.id)+'.jpg'
        file_info=bot.get_file(raw)
        downloadedPhoto=bot.download_file(file_info.file_path)

        schedule_file= open(path,'wb') 
        schedule_file.write(downloadedPhoto)
        bot.send_message(message.chat.id,'done')
    
    dialogChain.close()

def schedule_checker():
    while True:
        schedule.run_pending()
        sleep(1)

if __name__ == "__main__":
    
    
    schedules()
    
    Thread(target=schedule_checker).start() 

   
    bot.polling(none_stop=True)
