#https://www.weatherapi.com/docs/ base site
#http://api.weatherapi.com/v1 api

import PySimpleGUI as sg
import requests
import json
import re 
from datetime import date, timedelta, datetime
import sqlite3
import time

def main() :

    # izveido savienojumu ar db 
    connection = sqlite3.connect("Laikapstakliem.db")
    curs = connection.cursor()

    # izveido db ja tadas nav
    curs.execute('CREATE TABLE IF NOT EXISTS "Pieprasijums" ("ID_Pieprasijums"	INTEGER NOT NULL UNIQUE, "Laiks"	TEXT NOT NULL,"Datums"	TEXT NOT NULL, "Opcija_ID"	INTEGER NOT NULL, "Izvadits"	INTEGER NOT NULL, PRIMARY KEY("ID_Pieprasijums" AUTOINCREMENT))')
    curs.execute('CREATE TABLE IF NOT EXISTS "Opcija" ("ID_Opcija"	INTEGER NOT NULL UNIQUE, "Nosaukums"	TEXT, "Box1"	INTEGER NOT NULL, "Box2"	INTEGER NOT NULL, "Box3"	INTEGER NOT NULL, PRIMARY KEY("ID_Opcija" AUTOINCREMENT))')
        
    # izveido saskarni
    layout = [
        [sg.Text('Izvēlieties vēlamo opciju:')],
        [sg.Combo(['Pašreizējie laikapstākļi', 'Prognozes', 'Prognožu vēsture'], key='-DROPDOWN-', enable_events=True)],

        [sg.Text('Pilsēta:', visible=False, key='-TEXT1-'), sg.Input(key='-INPUT1-', visible=False)],
        [sg.Checkbox('Temperatūra', key='-CHECKBOX1-', visible=False, enable_events=True),
         sg.Checkbox('Vēja ātrums un virziens', key='-CHECKBOX2-', visible=False, enable_events=True),
         sg.Checkbox('Mākoņi un UV indekss', key='-CHECKBOX3-', visible=False, enable_events=True)],

        [sg.Text('Pilsēta:', visible=False, key='-TEXT2-'), sg.Input(key='-INPUT2-', visible=False)],
        [sg.Text('Datums: (Max - 14 dienas uz priekšu)', visible=False, key='-DATE1-'),
         sg.InputText(key='-DATE2-', visible=False),
         sg.CalendarButton("Izvēlieties datumu",close_when_date_chosen=True, target="-DATE2-", format='%Y:%m:%d', visible=False, key='-DATE3-')],
        [sg.Checkbox('Temperatūra', key='-CHECKBOX4-', visible=False),
         sg.Checkbox('Vēja ātrums', key='-CHECKBOX5-', visible=False),
         sg.Checkbox('Nokrišņi', key='-CHECKBOX6-', visible=False)],

        [sg.Text('Pilsēta:', visible=False, key='-TEXT3-'), sg.Input(key='-INPUT3-', visible=False)],
        [sg.Text('Datums: (Min - 2024-01-01)', visible=False, key='-DATE4-'),
         sg.InputText(key='-DATE5-', visible=False),
         sg.CalendarButton("Izvēlieties datumu",close_when_date_chosen=True, target="-DATE5-", format='%Y:%m:%d', visible=False, key='-DATE6-')],
        [sg.Checkbox('Temperatūra', key='-CHECKBOX7-', visible=False),
         sg.Checkbox('Vēja ātrums', key='-CHECKBOX8-', visible=False),
         sg.Checkbox('Nokrišņi', key='-CHECKBOX9-', visible=False)],

        [sg.Button('Palaist')],
        [sg.Text('', size=(40, 5), key='-OUTPUT-')]
    ]

    # lists veja virzieniem
    virzieni = {'Z': range(0,23) and range(338,359), 'ZA':range(23,68), 'A':range(68,113), 'DA':range(113,158), 'D':range(158,203), 'DR':range(203,248), 'R':range(248,293), 'ZR':range(293,338)}


    # funkcijas, ko izmanto vēlāk
    def looping(req_key, boolean, range1, range2):
        for i in range(range1, range2):
            window[f'-{req_key}{i}-'].update(visible=boolean)

    def is_date_in_range(date, start_date, end_date):
        return start_date <= date <= end_date

    def api_req1(izvele, vieta):
        dati = requests.get(f"http://api.weatherapi.com/v1/{izvele}.json?key=60bfb479aa644ef8be281544241904&q={vieta}").json()
        return dati

    def api_req2(izvele, vieta, diena):
        dati = requests.get(f"http://api.weatherapi.com/v1/{izvele}.json?key=60bfb479aa644ef8be281544241904&q={vieta}&dt={diena}").json()
        return dati

    # izveido logu
    window = sg.Window('LAIKAPSTĀKĻI', layout, use_default_focus=False)

    # loops
    while True:
        event, values = window.read()
        # ja lietotājs aizver logu aizvērt programmu
        if event == sg.WINDOW_CLOSED:
            break

        # ja lietotajs atver logu
        if event == '-DROPDOWN-':
            selected_option = values['-DROPDOWN-']
            if selected_option:
                window.refresh()
                # parupejas lai redz tikai atbilstoso info
                looping('DATE', False, 1, 7)
                looping('CHECKBOX', False, 1, 10)
                for i in range(1, 4):
                    window[f'-TEXT{i}-'].update(visible=False)
                    window[f'-INPUT{i}-'].update(visible=False)
                    
                if selected_option == 'Pašreizējie laikapstākļi':
                    window['-TEXT1-'].update(visible=True)
                    window['-INPUT1-'].update(visible=True)
                    looping('CHECKBOX', True, 1, 4)

                elif selected_option == 'Prognozes':
                    window['-TEXT2-'].update(visible=True)
                    window['-INPUT2-'].update(visible=True)
                    looping('DATE', True, 1, 4)
                    looping('CHECKBOX', True, 4, 7)

                elif selected_option == 'Prognožu vēsture':
                    window['-TEXT3-'].update(visible=True)
                    window['-INPUT3-'].update(visible=True)
                    looping('DATE', True, 4, 7)
                    looping('CHECKBOX', True, 7, 10)

        # ja uzspiez palaist pogu
        if event == 'Palaist':
            message = ''
            izvadits = False
            data_izvadits = 0
            selected_option = values['-DROPDOWN-']
            if selected_option:
                t = time.localtime()
                data_laiks = time.strftime("%H:%M:%S", t)
                data_datums = date.today()
                data_nosaukums = None
                data_box1 = 0
                data_box2 = 0
                data_box3 = 0
                # parada atbilstoso zinu loga takariba no izveles
                if selected_option == 'Pašreizējie laikapstākļi':
                    data_nosaukums = 'Pašreizējie laikapstākļi'
                    izvele = "current"
                    vieta = values['-INPUT1-']
                    temp = api_req1(izvele, vieta)['current']['temp_c']
                    veja_atrums =  api_req1(izvele, vieta)['current']['wind_kph']
                    gradi =  api_req1(izvele, vieta)['current']['wind_degree']
                    for virziens, kopa in virzieni.items():
                        if gradi in kopa:
                            veja_virziens = virziens
                            break
                    uv_indekss = api_req1(izvele, vieta)['current']['uv'] #lielaks ir sliktak
                    makoni = api_req1(izvele, vieta)['current']['cloud'] #procentos
                    if values['-CHECKBOX1-'] == True:
                        data_box1 = 1
                        message = message + f'Temperatūra: {temp}\N{DEGREE SIGN}C\n'
                        izvadits = True
                        data_izvadits = 1
                    if values['-CHECKBOX2-'] == True:
                        data_box2 = 1
                        message = message + f'{veja_virziens} vējš - Ātrums: {veja_atrums}km/h\n'
                        izvadits = True
                        data_izvadits = 1
                    if values['-CHECKBOX3-'] == True:
                        data_box3 = 1
                        message = message + f'Mākoņi: {makoni}% - UV indekss: {uv_indekss}\n'
                        izvadits = True
                        data_izvadits = 1
                    if not izvadits:
                        message = "Atzīmējiet kādu no izvēlēm"

                elif selected_option == 'Prognozes':
                    data_nosaukums = 'Prognozes'
                    datums = values['-DATE2-']
                    vieta = values['-INPUT2-']
                    datums = datums.replace(':', '-')
                    tagad = str(date.today())
                    beigas = str(date.today() + timedelta(days=14))
                    if is_date_in_range(datums, tagad, beigas) == False:
                        window['-DATE2-'].update('Ievadiet ATBILSTOŠU datumu')
                        message = 'Neizdevās'
                    else:
                        izvele = "forecast"
                        maxtemp = api_req2(izvele, vieta, datums)['forecast']['forecastday'][0]['day']['maxtemp_c']
                        mintemp = api_req2(izvele, vieta, datums)['forecast']['forecastday'][0]['day']['mintemp_c']
                        vidtemp = api_req2(izvele, vieta, datums)['forecast']['forecastday'][0]['day']['avgtemp_c']
                        maxatrums = api_req2(izvele, vieta, datums)['forecast']['forecastday'][0]['day']['maxwind_kph']
                        lietus = api_req2(izvele, vieta, datums)['forecast']['forecastday'][0]['day']['daily_chance_of_rain']
                        if values['-CHECKBOX4-'] == True:
                            data_box1 = 1
                            message = message + f'Max temp: {maxtemp}\N{DEGREE SIGN}C - Min temp: {mintemp}\N{DEGREE SIGN}C - Vid temp: {vidtemp}\N{DEGREE SIGN}C\n'
                            izvadits = True
                            data_izvadits = 1
                        if values['-CHECKBOX5-'] == True:
                            data_box2 = 1
                            message = message + f'Maksimālais vēja ātrums: {maxatrums}km/h\n'
                            izvadits = True
                            data_izvadits = 1
                        if values['-CHECKBOX6-'] == True:
                            data_box3 = 1
                            message = message + f'Nokrišņu iespēja: {lietus}%\n'
                            izvadits = True
                            data_izvadits = 1
                        if not izvadits:
                            message = "Atzīmējiet kādu no izvēlēm"

                elif selected_option == 'Prognožu vēsture':
                    data_nosaukums = 'Prognožu vēsture'
                    vieta = values['-INPUT3-']
                    datums = values['-DATE5-']
                    datums = datums.replace(':', '-')
                    tagad = str(date.today())
                    if is_date_in_range(datums, '2024-01-01', tagad) == False:
                        window['-DATE5-'].update('Ievadiet ATBILSTOŠU datumu')
                        message = 'Neizdevās'
                    else:
                        izvele = "history"
                        maxtemp = api_req2(izvele, vieta, datums)['forecast']['forecastday'][0]['day']['maxtemp_c']
                        mintemp = api_req2(izvele, vieta, datums)['forecast']['forecastday'][0]['day']['mintemp_c']
                        vidtemp = api_req2(izvele, vieta, datums)['forecast']['forecastday'][0]['day']['avgtemp_c']
                        maxatrums = api_req2(izvele, vieta, datums)['forecast']['forecastday'][0]['day']['maxwind_kph']
                        lietus = api_req2(izvele, vieta, datums)['forecast']['forecastday'][0]['day']['daily_chance_of_rain']
                        if values['-CHECKBOX7-'] == True:
                            data_box1 = 1
                            message = message + f'Max temp: {maxtemp}\N{DEGREE SIGN}C - Min temp: {mintemp}\N{DEGREE SIGN}C - Vid temp: {vidtemp}\N{DEGREE SIGN}C\n'
                            izvadits = True
                            data_izvadits = 1
                        if values['-CHECKBOX8-'] == True:
                            data_box2 = 1
                            message = message + f'Maksimālais vēja ātrums: {maxatrums}km/h\n'
                            izvadits = True
                            data_izvadits = 1
                        if values['-CHECKBOX9-'] == True:
                            data_box3 = 1
                            message = message + f'Nokrišņu iespēja: {lietus}%\n'
                            izvadits = True
                            data_izvadits = 1
                        if not izvadits:
                            message = "Atzīmējiet kādu no izvēlēm"
                window['-OUTPUT-'].update(message)
                ievads = f'INSERT INTO Opcija ("Nosaukums", "Box1", "Box2", "Box3")VALUES ("{data_nosaukums}", {data_box1}, {data_box2}, {data_box3})'
                curs.execute(ievads)
                data_opcija = curs.lastrowid
                curs.execute(f'INSERT INTO Pieprasijums ("Laiks", "Datums", "Opcija_ID", "Izvadits")VALUES ("{data_laiks}", "{data_datums}", {data_opcija}, {data_izvadits});')

                # commit izmaiņas datubāzē - tagad tās varēs redzēt arī citi
                connection.commit() 
                
    window.close()
    # # Aizver konekciju 
    connection.close()
main()