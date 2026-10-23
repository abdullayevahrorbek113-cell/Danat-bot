import requests
from config import PROVIDER_API_KEY

def send_auto_donate(game: str, player_id: str, product_sku: str):
    url = "https://api.provayder-sayti.uz/v1/order"
    headers = {"Authorization": f"Bearer {PROVIDER_API_KEY}"}
    data = {
        "game": game,
        "player_id": player_id,
        "sku": product_sku
    }
    
    try:
        # Haqiqiy provayder API ulanganda ushbu qatorlarni faollashtirasiz:
        # response = requests.post(url, json=data, headers=headers)
        # return response.json().get("status") == "success"
        
        return True # Sinov uchun avtomatik muvaffaqiyatli deb qaytaradi
    except Exception as e:
        print(f"API Xatoligi: {e}")
        return False
