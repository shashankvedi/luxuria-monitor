from curl_cffi import requests # Stealth Library
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import os
import random
import time

# --- CONFIGURATION ---
def get_dates():
    # Check 14 days in advance to ensure rooms are available
    checkin_date = datetime.now() + timedelta(days=14)
    checkout_date = checkin_date + timedelta(days=1)
    return checkin_date.strftime("%Y-%m-%d"), checkout_date.strftime("%Y-%m-%d")

checkin, checkout = get_dates()

# --- YOUR EXACT URLS (Verified) ---
COMPETITORS = [
    { "name": "Luxuria by Moustache", "url": f"https://www.booking.com/hotel/in/luxuria-varanasi-by-moustache.en-gb.html?checkin={checkin}&checkout={checkout}" },
    { "name": "Minimalist Varanasi", "url": f"https://www.booking.com/hotel/in/minimalist-varanasi-city-centre.en-gb.html?checkin={checkin}&checkout={checkout}" },
    { "name": "Quality Inn Varanasi", "url": f"https://www.booking.com/hotel/in/quality-inn-city-centre-varanasi.en-gb.html?checkin={checkin}&checkout={checkout}" },
    { "name": "Hotel Balaji Palace", "url": f"https://www.booking.com/hotel/in/balaji-palace-varanasi2.en-gb.html?checkin={checkin}&checkout={checkout}" },
    { "name": "Pearl Courtyard", "url": f"https://www.booking.com/hotel/in/atithi-satkaar.en-gb.html?checkin={checkin}&checkout={checkout}" },
    { "name": "Hotel Veda Vatica", "url": f"https://www.booking.com/hotel/in/veda-vatica-varanasi2.en-gb.html?checkin={checkin}&checkout={checkout}" },
    { "name": "Hotel Hardik", "url": f"https://www.booking.com/hotel/in/hardik-palacio.en-gb.html?checkin={checkin}&checkout={checkout}" },
    { "name": "Hotel Dolphin", "url": f"https://www.booking.com/hotel/in/dolphin-international-varanasi.en-gb.html?checkin={checkin}&checkout={checkout}" },
    { "name": "Coco Cabana", "url": f"https://www.booking.com/hotel/in/coco-cabana-varanasi.en-gb.html?checkin={checkin}&checkout={checkout}" }
]

DATA_FILE = "prices.json"

def get_inventory(url):
    try:
        # IMPERSONATE CHROME (The Secret Weapon)
        # This makes the server think we are a real Chrome 110 browser
        response = requests.get(url, impersonate="chrome110", timeout=30)
        
        # Check if we got a valid page
        if response.status_code != 200:
            print(f"   [ERROR] Status Code: {response.status_code}")
            return {}
            
        soup = BeautifulSoup(response.text, 'html.parser')
        inventory = {}
        
        # Debug Title
        if soup.title:
            print(f"   [Title] {soup.title.string.strip()[:40]}...")

        # 1. Main Table Scan (Desktop View)
        rows = soup.select('tr')
        found_any = False
        
        for row in rows:
            # Find Name
            name_elem = row.select_one('.hprt-roomtype-icon-link')
            if not name_elem: name_elem = row.select_one('[data-testid="room-name"]')
            
            # Find Price
            price_elem = row.select_one('.bui-price-display__value')
            if not price_elem: price_elem = row.select_one('[data-testid="price-and-discounted-price"]')
            if not price_elem: price_elem = row.select_one('.prco-valign-middle-helper')
            
            if name_elem and price_elem:
                found_any = True
                r_name = name_elem.text.strip().replace("\n", " ")
                # Clean Price
                r_price_txt = ''.join(c for c in price_elem.text if c.isdigit() or c == '.')
                if r_price_txt:
                    p = float(r_price_txt)
                    # Logic: Keep lowest price for this room name
                    if r_name not in inventory or p < inventory[r_name]:
                        inventory[r_name] = p

        # 2. Card Scan (Mobile/Search Redirect)
        if not found_any:
            cards = soup.select('[data-testid="property-card"]')
            for card in cards:
                title = card.select_one('[data-testid="title"]')
                price = card.select_one('[data-testid="price-and-discounted-price"]')
                if title and price:
                    p = float(''.join(c for c in price.text if c.isdigit()))
                    inventory[title.text.strip()] = p

        return inventory

    except Exception as e:
        print(f"Error scraping {url}: {e}")
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
    
    print(f"--- STEALTH SCAN STARTED: {today_str} ---")
    
    for hotel in COMPETITORS:
        print(f"Scanning: {hotel['name']}...")
        time.sleep(random.uniform(3, 7)) # Sleep to prevent rate-limiting
        
        data = get_inventory(hotel['url'])
        
        if data:
            print(f" -> Found {len(data)} room types.")
            new_entry["data"][hotel['name']] = data
        else:
            print(f" -> No data found (Check Logs).")
            new_entry["data"][hotel['name']] = {}

    history.append(new_entry)
    if len(history) > 50: history = history[-50:]

    with open(DATA_FILE, 'w') as f:
        json.dump(history, f, indent=2)
    
    print("--- Scan Complete ---")

if __name__ == "__main__":
    main()
