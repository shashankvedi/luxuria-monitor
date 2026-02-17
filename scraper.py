import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import os
import random
import time

# --- CONFIGURATION ---
def get_dates():
    # Check 2 weeks ahead to ensure we find room availability
    # (Checking "tomorrow" often shows Sold Out)
    checkin_date = datetime.now() + timedelta(days=14)
    checkout_date = checkin_date + timedelta(days=1)
    return checkin_date.strftime("%Y-%m-%d"), checkout_date.strftime("%Y-%m-%d")

checkin, checkout = get_dates()

# VERIFIED URLS
COMPETITORS = [
    { "name": "Luxuria by Moustache", "url": f"https://www.booking.com/hotel/in/luxuria-varanasi-by-moustache.html?checkin={checkin}&checkout={checkout}" },
    { "name": "Quality Inn Varanasi", "url": f"https://www.booking.com/hotel/in/quality-inn-city-centre-varanasi.html?checkin={checkin}&checkout={checkout}" },
    { "name": "Hotel Balaji Palace", "url": f"https://www.booking.com/hotel/in/balaji-palace-varanasi2.html?checkin={checkin}&checkout={checkout}" },
    { "name": "Pearl Courtyard", "url": f"https://www.booking.com/hotel/in/atithi-satkaar.html?checkin={checkin}&checkout={checkout}" },
    { "name": "Hotel Veda Heritage", "url": f"https://www.booking.com/hotel/in/veda-varanasi.html?checkin={checkin}&checkout={checkout}" },
    { "name": "Hotel Hardik", "url": f"https://www.booking.com/hotel/in/hardik-palacio.html?checkin={checkin}&checkout={checkout}" },
    { "name": "Hotel Dolphin", "url": f"https://www.booking.com/hotel/in/dolphin-international-varanasi.html?checkin={checkin}&checkout={checkout}" },
    { "name": "Vedangam", "url": f"https://www.booking.com/hotel/in/vedangam.html?checkin={checkin}&checkout={checkout}" }
]

DATA_FILE = "prices.json"

def get_inventory(url):
    # Modern Headers (Looks like a real Laptop)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        inventory = {}

        # --- STRATEGY: Scan for Modern React Elements (2026 Style) ---
        
        # 1. Find the Main Table Rows
        rows = soup.select('tr') # Get all rows, we filter inside
        
        found_any = False
        
        for row in rows:
            # Look for Room Name
            name_elem = row.select_one('.hprt-roomtype-icon-link')
            if not name_elem: 
                # Try finding name via other class
                name_elem = row.select_one('[data-testid="room-name"]')
            
            # Look for Price
            price_elem = row.select_one('[data-testid="price-and-discounted-price"]')
            if not price_elem:
                price_elem = row.select_one('.bui-price-display__value')
            
            if name_elem and price_elem:
                found_any = True
                r_name = name_elem.text.strip().replace("\n", " ")
                # Clean price: Remove ₹, commas, and spaces
                raw_price = ''.join(c for c in price_elem.text if c.isdigit() or c == '.')
                
                if raw_price:
                    r_price = float(raw_price)
                    # Logic: Keep lowest price for this room type
                    if r_name not in inventory or r_price < inventory[r_name]:
                        inventory[r_name] = r_price

        # 2. Fallback: Check for "Property Cards" (If redirected to search view)
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
    
    print(f"--- STARTING SCAN (14 Days Advance) ---")
    
    for hotel in COMPETITORS:
        print(f"Scanning: {hotel['name']}...")
        time.sleep(random.uniform(2, 5))
        
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
