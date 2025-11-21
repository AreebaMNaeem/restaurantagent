import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape_xanders_menu(url, restaurant_name):
    menu_items = []
    headers = {'User-Agent':
               'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
              }

    res = requests.get(url, headers=headers)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, 'html.parser')

    all_dishes = soup.find_all("div", class_="fditem-list")

    print(f"🔎 Found {len(all_dishes)} dish containers")

    for dish in all_dishes:
        # Find dish name
        name_tag = dish.find("div", class_="fdlist_1_name")
        dish_name = name_tag.get_text(strip=True) if name_tag else "Unknown"

        # Price
        price_tag = dish.find("span", class_="woocommerce-Price-amount")
        price = price_tag.get_text(strip=True) if price_tag else "N/A"

        # Description
        desc_tag = dish.find("div", class_="exwf-sdes")
        description = desc_tag.get_text(strip=True) if desc_tag else ""

        # Find nearest preceding category heading
        category_heading = dish.find_previous("h2", class_="mn-namegroup")
        category_name = category_heading.find('span').get_text(strip=True) if category_heading else "Unknown"

        menu_items.append({
            'Restaurant': restaurant_name,
            'Category': category_name,
            'Dish': dish_name,
            'Price': price,
            'Description': description
        })

    return menu_items

# Usage:
url = 'https://xanders.pk/menu/'
menu_data = scrape_xanders_menu(url, 'Xanders')

if menu_data:
    print(f"✅ Scraped {len(menu_data)} dishes. Sample:")
    print(menu_data[:3])
    pd.DataFrame(menu_data).to_csv('xanders_menu.csv', index=False, encoding='utf-8-sig')
    print("Saved as xanders_menu.csv")
else:
    print(" No menu data found.")
