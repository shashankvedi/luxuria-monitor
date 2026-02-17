import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import os
import random
import time

# --- CONFIGURATION ---
def get_dates():
    # Check 2 weeks ahead to ensure availability (Avoids "Sold Out" errors)
    checkin_date = datetime.now() + timedelta(days=14)
    checkout_date = checkin_date + timedelta(days=1)
    return checkin_date.strftime("%Y-%m-%d"), checkout_date.strftime("%Y-%m-%d")

checkin, checkout = get_dates()

# --- YOUR EXACT URLS ---
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
    # ROTATING USER AGENTS (To prevent blocking)
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
    ]
    
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Upgrade-Insecure-Requests": "1",
        "Referer": "https://www.google.com/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        # Check if blocked
        if response.status_code == 403 or "Just a moment" in response.text:
            print(f"   [BLOCKED] Server blocked the request.")
            return {}

        soup = BeautifulSoup(response.text, 'html.parser')
        inventory = {}
        
        # --- STRATEGY: SCAN ALL ELEMENTS ---
        # 1. Main Table Scan
        rows = soup.select('tr')
        for row in rows:
            # Name
            name = row.select_one('.hprt-roomtype-icon-link') or row.select_one('[data-testid="room-name"]')
            # Price
            price = row.select_one('.bui-price-display__value') or row.select_one('[data-testid="price-and-discounted-price"]')
            
            if name and price:
                r_name = name.text.strip().replace("\n", " ")
                r_price_txt = ''.join(c for c in price.text if c.isdigit() or c == '.')
                if r_price_txt:
                    p = float(r_price_txt)
                    if r_name not in inventory or p < inventory[r_name]:
                        inventory[r_name] = p

        # 2. Card Scan (Fallback)
        if not inventory:
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
    
    print(f"--- STARTING SCAN: {today_str} ---")
    
    for hotel in COMPETITORS:
        print(f"Scanning: {hotel['name']}...")
        time.sleep(random.uniform(3, 8)) # Sleep longer to be safe
        
        data = get_inventory(hotel['url'])
        
        if data:
            print(f" -> Found {len(data)} room types.")
            new_entry["data"][hotel['name']] = data
        else:
            print(f" -> No data found.")
            new_entry["data"][hotel['name']] = {}

    history.append(new_entry)
    if len(history) > 50: history = history[-50:]

    with open(DATA_FILE, 'w') as f:
        json.dump(history, f, indent=2)
    
    print("--- Scan Complete ---")

if __name__ == "__main__":
    main()
