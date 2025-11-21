import pandas as pd
from agno.tools.base import Tool
from difflib import get_close_matches
from fpdf import FPDF
import re


class MenuTool(Tool):
    def __init__(self, path):
        self.menu = pd.read_csv(
            path,
            header=None,
            names=["Restaurant", "Category", "Dish", "Price", "Description"]
        )

        # ✅ Clean data (categories/dish/desc)
        self.menu["Category"] = self.menu["Category"].astype(str).str.lower().str.strip()
        self.menu["Dish"] = self.menu["Dish"].astype(str).str.lower().str.strip()
        self.menu["Description"] = self.menu["Description"].fillna("").astype(str).str.lower().str.strip()

        # ✅ Robust price cleaning
        def clean_price_cell(val):
            if pd.isna(val):
                return None
            s = str(val)
            s = re.sub(r"[^\d.,]", "", s)
            s = s.replace(",", "")
            return s if s != "" else None

        self.menu["Price"] = self.menu["Price"].apply(clean_price_cell)
        self.menu["Price"] = pd.to_numeric(self.menu["Price"], errors="coerce")

    # ----------------- CATEGORY DETECTION -----------------
    def detect_category(self, query):
        query = query.lower().strip()
        categories = list(self.menu["Category"].dropna().unique())

        for cat in categories:
            if query == cat or cat in query:
                return cat

        match = get_close_matches(query, categories, n=1, cutoff=0.7)
        if match:
            return match[0]

        category_map = {
            "smoothies": "smoothies",
            "juice": "fresh juice",
            "tea": "homemade ice tea",
            "coffee": "cold coffee",
            "frappes": "frappes",
            "pizzas": "wood fired pizzas",
            "dessert": "desserts",
            "burger": "burgers",
            "sandwich": "sandwiches",
            "soup": "soups",
            "salad": "salads",
            "egg": "all day eggs",
            "breakfast": "all day sweet breakfast",
            "seafood": "seafood mains",
            "beef": "beef & chicken mains",
            "chicken": "beef & chicken mains",
            "pasta": "pastas",
            "gelato": "gelato shakes",
            "cocktail": "cocktails",
            "special": "specials menu",
            "extra": "extra",
        }

        for key, val in category_map.items():
            if key in query:
                return val

        return None

    # ----------------- PRICE DETECTION -----------------
    def detect_price_limit(self, query):
        """
        Detects price limits in a natural-language query.
        Returns:
          ("between", low, high) OR ("under", val) OR ("over", val) OR None
        """
        q = (query or "").lower()
        q = re.sub(r"rs\s*(\d+)", r"\1", q)
        q = re.sub(r"₨\s*(\d+)", r"\1", q)

        # between X and Y
        between_match = re.search(
            r"between\s*([\d,]+(?:\.\d+)?)\s*(?:and|to|-)\s*([\d,]+(?:\.\d+)?)",
            q
        )
        if between_match:
            low = float(between_match.group(1).replace(",", ""))
            high = float(between_match.group(2).replace(",", ""))
            return ("between", low, high)

        # under / below / less than
        under_match = re.search(r"(?:under|below|less than)\s*([\d,]+(?:\.\d+)?)", q)
        if under_match:
            val = float(under_match.group(1).replace(",", ""))
            return ("under", val)

        # over / above / more than / greater than
        over_match = re.search(r"(?:over|above|more than|greater than)\s*([\d,]+(?:\.\d+)?)", q)
        if over_match:
            val = float(over_match.group(1).replace(",", ""))
            return ("over", val)

        return None

    # ----------------- KEYWORD FILTER -----------------
    def filter_by_keywords(self, df, query):
        ignore_words = {"price", "of", "show", "tell", "me", "all", "menu",
                        "under", "below", "over", "above", "rs", "₨", "from"}
        keywords = [w for w in re.split(r"\s+|\-|,", query)
                    if w and w not in ignore_words and len(w) > 1 and not re.search(r"\d", w)]

        if not keywords:
            return df

        pattern = "|".join(map(re.escape, keywords))
        return df[
            df["Dish"].str.contains(pattern, case=False, na=False)
            | df["Description"].str.contains(pattern, case=False, na=False)
            | df["Category"].str.contains(pattern, case=False, na=False)
        ]

    # ----------------- TEXT CLEANER -----------------
    def clean_text(self, text):
        """Clean and normalize text for PDF output."""
        if isinstance(text, str):
            text = (text.replace("’", "'")
                        .replace("–", "-")
                        .replace("‘", "'")
                        .replace("“", '"')
                        .replace("”", '"'))
            return re.sub(r'\s+', ' ', text.strip())
        return str(text)

    # ----------------- PDF GENERATOR -----------------
    def generate_menu_card(self, df):
        # If somehow df is empty or too small, use the full menu
        if df.empty or len(df) < 10:
            print("[DEBUG] Detected small dataset — using full menu for PDF.")
            df = self.menu.copy()

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # ✅ Use a Unicode-safe font (fixes Latin-1 crash)
        try:
            pdf.add_font('DejaVu', '', 'C:\\Windows\\Fonts\\DejaVuSans.ttf', uni=True)
            font_name = 'DejaVu'
        except:
            pdf.add_font('Arial', '', 'C:\\Windows\\Fonts\\Arial.ttf', uni=True)
            font_name = 'Arial'

        pdf.set_font(font_name, "B", 16)
        pdf.cell(0, 10, "Xander's Restaurant Menu", ln=True, align="C")
        pdf.ln(5)
        pdf.set_font(font_name, "", 12)

        current_cat = None

        for _, row in df.iterrows():
            if pdf.get_y() > 250:
                pdf.add_page()
                pdf.set_font(font_name, "", 12)

            if row["Category"] != current_cat:
                current_cat = row["Category"]
                pdf.ln(5)
                pdf.set_font(font_name, "B", 14)
                pdf.cell(0, 10, self.clean_text(str(current_cat).title()), ln=True)
                pdf.set_font(font_name, "", 12)

            dish = self.clean_text(str(row["Dish"]).title())
            price = f"Rs{row['Price']:,.0f}" if not pd.isna(row["Price"]) else "N/A"
            desc = self.clean_text(str(row["Description"]).capitalize())

            pdf.cell(0, 8, f"{dish} - {price}", ln=True)
            pdf.set_font(font_name, "I", 10)
            pdf.multi_cell(0, 6, desc)
            pdf.set_font(font_name, "", 12)

        pdf.output("menu_card.pdf")
        print("[DEBUG] ✅ PDF successfully generated with full menu.")

    # ----------------- MAIN RUN LOGIC -----------------
    def run(self, query: str) -> str:
        print(f"[DEBUG] MenuTool called with query: {query}")
        query = (query or "").lower().strip()
        results = self.menu.copy()

        # ----- Price filter -----
        price_cond = self.detect_price_limit(query)
        if price_cond:
            if price_cond[0] == "between":
                _, low, high = price_cond
                print(f"[DEBUG] Filtering dishes between ₨{low:.2f} and ₨{high:.2f}")
                results = results[results["Price"].notna() & (results["Price"] >= low) & (results["Price"] <= high)]
            elif price_cond[0] == "under":
                _, limit = price_cond
                print(f"[DEBUG] Filtering dishes under ₨{limit:.2f}")
                results = results[results["Price"].notna() & (results["Price"] <= limit)]
            elif price_cond[0] == "over":
                _, limit = price_cond
                print(f"[DEBUG] Filtering dishes above ₨{limit:.2f}")
                results = results[results["Price"].notna() & (results["Price"] >= limit)]

        # ----- Category filter -----
        category = self.detect_category(query)
        if category and (not price_cond or len(results) > 0):
            print(f"[DEBUG] Category detected: {category}")
            results = results[results["Category"] == category]

        # ----- Specific dish query -----
        dish_query = re.sub(
            r"\b(price|cost|rate|tell me|show me|of|for|how much|what is the price of|what is the price)\b",
            "",
            query,
        ).strip()
        dish_query = re.sub(r"\bfrom menu\b", "", dish_query).strip()

        if dish_query:
            exact_match = self.menu[self.menu["Dish"].str.lower() == dish_query]
            if not exact_match.empty:
                row = exact_match.iloc[0]
                return f"**{row['Dish'].title()}** — ₨{row['Price']:,.0f}\n*{row['Description']}*"

            close = get_close_matches(dish_query, list(self.menu["Dish"].unique()), n=1, cutoff=0.7)
            if close:
                row = self.menu[self.menu["Dish"] == close[0]].iloc[0]
                print(f"[DEBUG] Close dish match found: {close[0]}")
                return f"**{row['Dish'].title()}** — ₨{row['Price']:,.0f}\n*{row['Description']}*"

            partial = self.menu[self.menu["Dish"].str.contains(re.escape(dish_query), case=False, na=False)]
            if not partial.empty and len(partial) <= 5:
                out = "### 🍽 Dish Details\n\n"
                for _, row in partial.iterrows():
                    out += f"**{row['Dish'].title()}** — ₨{row['Price']:,.0f}\n*{row['Description']}*\n\n"
                return out

        # ----- Keyword fallback -----
        if not price_cond and not category:
            results = self.filter_by_keywords(results, query)

        # ----- Handle empty -----
        if results.empty:
            return "😔 Sorry, no matching dishes found. Try another category or keyword."

        results = results.reset_index(drop=True)
        title = category.title() if category else "Menu"
        output = f"### 🍴 {title} Items\n\n"

        for _, row in results.iterrows():
            price_str = f"₨{row['Price']:,.0f}" if not pd.isna(row["Price"]) else "N/A"
            output += f"**{row['Dish'].title()}** — {price_str}\n"
            if row["Description"]:
                output += f"*{row['Description'].capitalize()}*\n\n"

        # ----- PDF generation -----
        if "pdf" in query or "menu card" in query:
            print("[DEBUG] Generating menu card PDF (full CSV)...")
            self.generate_menu_card(self.menu)
            output += "\n📄 Generated **menu_card.pdf** for you!"

        return output
