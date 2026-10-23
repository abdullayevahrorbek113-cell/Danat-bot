import requests
from config import PROVIDER_API_URL, PROVIDER_API_KEY

def send_auto_donate(game: str, player_id: str, product_name: str):
    headers = {"Authorization": f"Bearer {PROVIDER_API_KEY}"}
    data = {
        "game": game,
        "player_id": player_id,
        "product": product_name
    }
    
    try:
        # Haqiqiy API ulash uchun pastdagi izohni ochasiz:
        # response = requests.post(PROVIDER_API_URL, json=data, headers=headers, timeout=10)
        # return response.status_code == 200 and response.json().get("status") == "success"
        
        return True # Hozircha avtomatik bajarilgan deb qabul qiladi
    except Exception as e:
        print(f"API Xatoligi: {e}")
        return False
