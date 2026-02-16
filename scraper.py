import requests
import json
from datetime import datetime, timedelta
import os
import time

# --- YOUR API KEY ---
API_KEY = "3d3e266746mshd947bdb9d343c11p106f3bjsne07eb9f781e3"

# --- CONFIGURATION ---
def get_dates():
    tomorrow = datetime.now() + timedelta(days=1)
    day_after = tomorrow + timedelta(days=1)
    return tomorrow.strftime("%Y-%m-%d"), day_after.strftime("%Y-%m-%d")

checkin, checkout = get_dates()

# --- COMPETITORS (Hotel IDs) ---
HOTELS = [
    { "name": "Luxuria by Moustache", "id": "11187766" },
    { "name": "Quality Inn Varanasi", "id": "906752" },
    { "name": "Hotel Balaji Palace", "id": "10972456" },
    { "name": "Pearl Courtyard", "id": "5322307" },
    { "name": "Hotel Veda Heritage", "id": "9722369" },
    { "name": "Hotel Hardik", "id": "8343763" },
    { "name": "Hotel Dolphin", "id": "452796" },
    { "name": "Vedangam", "id": "8859943" }
]

DATA_FILE = "prices.json"

def get_price_from_api(hotel_id):
    url = "https://apidojo-booking-v1.p.rapidapi.com/properties/get-detail"
    
    querystring = {
        "hotel_id": hotel_id,
        "search_id": "1",
        "arrival_date": checkin,
        "departure_date": checkout,
        "adults_number": "2",
        "room_qty": "1",
        "currency_code": "INR",
        "languagecode": "en-us"
    }

    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "apidojo-booking-v1.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=30)
        data = response.json()
        inventory = {}

        # Parse API Response (Standard Structure)
        # We look for the "block" list which contains pricing info
        if "block" in data:
            for block in data["block"]:
                # Get Price
                price_data = block.get("min_price", {})
                price = price_data.get("price")
                
                # Get Room Name (from room_id)
                room_id = block.get("room_id")
                # Try to match ID to description in 'rooms' dict if available
                room_name = f"Room Type {room_id}" # Fallback name
                
                if "rooms" in data:
                    r_info = data["rooms"].get(str(room_id))
                    if r_info:
                        room_name = r_info.get("description", room_name)

                if price:
                    p = float(price)
                    # Clean Name
                    room_name = room_name.split(" - ")[0].strip()
                    
                    if room_name not in inventory or p < inventory[room_name]:
                        inventory[room_name] = p
                        
        return inventory

    except Exception as e:
        print(f"Error fetching {hotel_id}: {e}")
        return {}

def main():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            try: history = json.load(f)
            except: history = []
    else:
        history = []

    today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_entry = { "date": today_str, "data": {} }
    
    print(f"--- API SCAN STARTED: {today_str} ---")
    
    for hotel in HOTELS:
        print(f"Fetching: {hotel['name']}...")
        time.sleep(0.5) # Be polite to API
        
        data = get_price_from_api(hotel['id'])
        
        if data:
            print(f" -> Success: {len(data)} room types.")
            new_entry["data"][hotel['name']] = data
        else:
            print(f" -> No data returned.")
            new_entry["data"][hotel['name']] = {}

    history.append(new_entry)
    if len(history) > 50: history = history[-50:]

    with open(DATA_FILE, 'w') as f:
        json.dump(history, f, indent=2)
    
    print("--- SCAN COMPLETE ---")

if __name__ == "__main__":
    main()
