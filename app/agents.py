from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.duckduckgo import DuckDuckGoTools
from menutool import MenuTool
from faqtool import FaqDataTool
import pandas as pd
import os
from dotenv import load_dotenv

# -------------------- ENVIRONMENT SETUP --------------------
load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

# -------------------- TOOLS INITIALIZATION --------------------
menu_tool = MenuTool(path=r"C:\Users\AA\Desktop\agent\xanders_menu.csv")
faq_tool = FaqDataTool()

# -------------------- AGENTS SETUP --------------------
menu_agent = Agent(
    name="Menu Expert",
    role="Answer questions about food menu, prices, and generate menu cards.",
    model=Groq(id="llama-3.1-8b-instant"),
    tools=[menu_tool],
    instructions=(
        "You are a friendly restaurant assistant. "
        "Use the menu tool to answer any questions about dishes, prices, and availability. "
        "Always return the tool output exactly as given, do not change any prices or names. "
        "If the user asks for a 'menu card', call the menu tool to generate it. "
        "Always use the MenuTool to fetch menu details. "
        "Never guess or make up prices. "
        "Return the result exactly as shown in the CSV file. "
        "Always sound helpful and conversational."
    ),
    show_tool_calls=True,
    markdown=True
)

faq_agent = Agent(
    name="FAQ Assistant",
    role="Answer customer FAQs about branches, timings, contact info, etc.",
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[faq_tool],
    instructions=(
        "You are the official FAQ assistant for Xander’s Restaurant. "
        "You must always use the FaqDataTool to fetch information from the Xander’s website "
        "(https://xanders.pk). The tool already scrapes the About Us and Contact Us pages. "
        "When a user asks about branch info (e.g. Tipu Sultan, Clifton), timings, phone numbers, or policies, "
        "search that information within the text provided by FaqDataTool. "
        "Only answer based on what is found in that website data. "
        "If not found, say 'Sorry, I couldn’t find that information on the website.' "
        "Never talk about historical or unrelated topics. "
        "Focus only on Xander’s Restaurant branches and info."
    ),
    show_tool_calls=False,
    markdown=True
)

web_agent = Agent(
    name="Web Researcher",
    role="Search for recent food trends and information",
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[DuckDuckGoTools()],
    instructions=(
        "Search for information when asked about food trends, nutrition facts, "
        "or competitor information. Always include sources."
    ),
    show_tool_calls=True,
    markdown=True
)

restaurant_team = Agent(
    team=[menu_agent, faq_agent, web_agent],
    model=Groq(id="llama-3.3-70b-versatile"),
    instructions=[
        "You're the main assistant for Xander's Restaurant.",
        "You are not allowed to use tool-based function calls like `transfer_task_to_*`. Only route messages to one of the team agents.",
        "Route queries to the appropriate agent:",
        "- Use Menu Expert for anything about food, menu, prices.",
        "- Use FAQ Assistant for ingredient, allergy, policy questions.",
        "- Use Web Researcher for trends, nutrition facts, or external info.",
        "Do not invent or call functions yourself — let the correct agent handle it.",
        "Be friendly, helpful, and maintain a professional tone."
    ],
    show_tool_calls=True,
    markdown=True
)

# -------------------- SMART MENU DETECTION --------------------
def is_menu_query(query, menu_tool):
    """Detect if the query relates to restaurant menu or categories."""
    query = query.lower()

    # ✅ Main keywords and your full category list
    menu_keywords = [
        "menu", "dish", "dishes", "price", "food", "order", "under", "below",
        "homemade ice tea", "fresh juice", "specials menu", "all day eggs",
        "all day sweet breakfast", "soups", "appetizers", "salads", "sandwiches",
        "burgers", "seafood mains", "beef & chicken mains", "pastas",
        "wood fired pizzas", "gelato tub", "desserts", "beverages",
        "cold coffee", "frappes", "gelato shakes", "cocktails", "smoothies",
        "extra"
    ]

    # ✅ Step 1: Keyword match
    if any(keyword in query for keyword in menu_keywords):
        return True

    # ✅ Step 2: Match directly from CSV (category or dish)
    if hasattr(menu_tool, "menu"):
        categories = [c.lower() for c in menu_tool.menu["Category"].unique() if isinstance(c, str)]
        dishes = [d.lower() for d in menu_tool.menu["Dish"].unique() if isinstance(d, str)]
        if any(cat in query for cat in categories):
            return True
        if any(dish in query for dish in dishes):
            return True

    return False

# ----------------- FORCE FAQ AGENT TO USE TOOL ONLY -----------------
def run_faq(query: str):
    print("[DEBUG] Using DIRECT FAQ TOOL (NO LLM) ⚡")
    return faq_tool.answer(query)


# -------------------- MAIN EXECUTION LOOP --------------------
if __name__ == "__main__":
    while True:
        user_query = input("\nCustomer: ")
        if user_query.lower() in ["exit", "quit"]:
            print("Goodbye! Have a nice day.")
            break

        # ✅ Auto-route Menu Queries
        if is_menu_query(user_query, menu_tool):
            print("\n[DEBUG] Routed to MenuTool ✅ (Auto-detected menu query)")
            response = menu_tool.run(user_query)
            print(f"\nAssistant (Menu Expert):\n{response}")

        # ✅ FAQ Queries → Uses your new DIRECT FAQ TOOL (run_faq)
        elif any(keyword in user_query.lower() for keyword in [
            "branch", "location", "clifton", "tipu sultan", "bukhari",
            "contact", "timing", "hours", "number", "address",
            "policy", "allergy", "ingredient", "gluten"
        ]):
            print("\n[DEBUG] Routed to FAQ Tool Only (No LLM) ✅")
            response = run_faq(user_query)
            print(f"\nAssistant (FAQ):\n{response}")

        # ✅ All Other Queries → LLM Team
        else:
            print("\n[DEBUG] Routed to Main Agent Team (LLM Coordination)")
            response = restaurant_team.run(user_query)
            print(f"\nAssistant:\n{response.content if hasattr(response, 'content') else response}")
