import requests
import time

def fetch_matches():
    for attempt in range(3):
        print("Попытка ", attempt + 1, "\n")
        try:    
            response = requests.get("https://api.opendota.com/api/publicMatches", timeout=10)
            if response.status_code == 200:
                print("Запрос был успешно выполнен")
                return response.json()
            else:
                print("Не удалось выполнить запрос, ошибка: ", response.status_code, "\n")
        except requests.exceptions.RequestException:
            print("Не удалось получить ответ", "\n")
        time.sleep(5)
    else:
        print("Все попытки неудачны")
        return []
matches = fetch_matches()
print(len(matches))