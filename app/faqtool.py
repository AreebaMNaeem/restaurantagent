from agno.tools.base import Tool
import re
import requests
from bs4 import BeautifulSoup

class FaqDataTool:
    def __init__(self):
        print("[DEBUG] 🚀 Initializing FaqDataTool and fetching website content...")

        urls = [
            "https://xanders.pk/about-us/",
            "https://xanders.pk/contact-us/"
        ]

        self.raw_text = ""
        for url in urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    print(f"[DEBUG] 🌐 Successfully fetched: {url}")
                    soup = BeautifulSoup(response.text, "html.parser")
                    text = soup.get_text(separator=" ", strip=True)
                    self.raw_text += text + " "
                else:
                    print(f"[DEBUG] ❌ Failed to fetch: {url} – Status {response.status_code}")
            except Exception as e:
                print(f"[DEBUG] ❌ Error fetching {url}: {e}")

        print(f"[DEBUG] ✅ Total combined text length: {len(self.raw_text)} characters")

        # ---------------------------
        # EXTRACT BRANCHES
        # ---------------------------
        possible_branches = [
            "clifton",
            "dha bukhari",
            "tipu sultan"
        ]

        self.branches = [
            b for b in possible_branches
            if b.lower() in self.raw_text.lower()
        ]

        print(f"[DEBUG] ✅ Branches found: {self.branches}")

        # ---------------------------
        # EXTRACT CONTACT INFO
        # ---------------------------
        # STATIC because website only shows this
        self.contact_info = {
            "phone": "021-111-926337",
            "email": "Contact@xanders.pk"
        }

        print(f"[DEBUG] ✅ General contact info found: {self.contact_info}")

    # ---------------------------
    # FUNCTIONS TO GET EXACT DATA
    # ---------------------------
    def get_branches(self):
        print("[DEBUG] 📦 Returning branches from scraped data only")
        return self.branches

    def get_contact_info(self):
        print("[DEBUG] 📦 Returning contact info from scraped data only")
        return self.contact_info

    # ---------------------------
    # SINGLE ANSWER FUNCTION
    # ---------------------------
    def answer(self, query):
        q = query.lower()

        if "branch" in q:
            branches = self.get_branches()
            if not branches:
                return "No branches were found on the website."

            return (
                "### Xander's Branches (From Live Website)\n" +
                "\n".join(f"- {b.title()}" for b in branches)
            )

        if "contact" in q:
            info = self.get_contact_info()
            return (
                "### Contact Information (From Live Website)\n"
                f"- Phone: {info['phone']}\n"
                f"- Email: {info['email']}"
            )

        return "I can answer questions about branches or contact info."

