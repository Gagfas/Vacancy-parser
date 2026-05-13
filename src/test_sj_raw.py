import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('SJ_KEY')
if not api_key:
    print('Нет SJ_KEY в .env')
    exit()

url = "https://api.superjob.ru/2.0/vacancies/"
headers = {'X-Api-App-Id': api_key}

params = {
    'keyword': 'Python разработчик',
    'page': 0,
    'count': 2,
}

print('Сырые данные от Superjob')
response = requests.get(url, params=params, headers=headers)
if response.status_code == 200:
    data = response.json()
    with open('sj_raw_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print('Даннные сохранены')

    objects = data.get('objects', [])
    if objects:
        print('\n Структура первой вакансии:')
        print('='*60)
        obj = objects[0]

        for key, value in obj.items():
            if isinstance(value, str) and len(value) > 100:
                print(f'{key}: {value[:100]}...')
            elif isinstance(value, dict):
                print(f"   {key}: {json.dumps(value, ensure_ascii=False)[:100]}")
            else:
                print(f'{key}:{value}')
        
        print(f'\n Поля с описанием:')
        description_fields = ['candidat', 'vacancyRichText', 'work', 'compensation', 'client']
        for field in description_fields:
            value = obj.get(field, '')
            if value:
                print(f'\n ---{field}---')
                print(f'   {str(value)[:200]}')
    else:
        print(f'Ошибка {response.status_code}')
        print(response.text[:200])
