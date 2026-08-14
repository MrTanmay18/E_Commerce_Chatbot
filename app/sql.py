from groq import Groq
import os
import re
import sqlite3
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GROQ_MODEL = os.getenv("GROQ_MODEL")
db_path = Path(__file__).parent / "db.sqlite"
client_sql = Groq()


# ============================================================
# PROMPTS
# ============================================================

sql_prompt = """
You are an expert in understanding a product database and generating SQL
queries for natural-language questions.

<schema>
table: product

fields:
product_link - string (product URL)
title - string (product name)
brand - string (product brand)
price - integer (price in Indian Rupees)
discount - float (discount stored as decimal between 0 and 1)
avg_rating - float (rating from 0 to 5)
total_ratings - integer (number of ratings)
</schema>

Rules:
- Use LIKE for brand searches. Never use ILIKE.
- For top N queries, use LIMIT N.
- For rating-based queries, use ORDER BY avg_rating DESC.
- For price-based queries, use ORDER BY price ASC unless specified otherwise.
- For general product searches, use LIMIT 10.
- Always use SELECT *.
- Create only one SQL query.

IMPORTANT DISCOUNT RULE:
The discount column stores percentages as decimal fractions.

10% = 0.10
20% = 0.20
30% = 0.30
40% = 0.40
50% = 0.50
60% = 0.60
70% = 0.70

Therefore:
- "50% discount" means discount >= 0.50
- "more than 50% discount" means discount > 0.50
- "at least 50% discount" means discount >= 0.50
- "below 50% discount" means discount < 0.50
- "between 20% and 50%" means discount BETWEEN 0.20 AND 0.50

NEVER compare discount with whole percentage values such as 50 or 70.

Return only the SQL query between <SQL></SQL> tags.
"""

comprehension_prompt = """
You answer product questions using only the supplied product data.

Rules:
- Do not mention SQL, database, dataframe or context.
- Do not make up information.
- Keep the answer concise.
- Mention product name, price, discount and rating when relevant.
- Do not include raw Python dictionaries.
- Do not include HTML.
"""


# ============================================================
# SQL SAFETY
# ============================================================

FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
    "ATTACH", "DETACH", "PRAGMA", "REPLACE", "CREATE",
    "TRUNCATE", "VACUUM", "REINDEX"
]


def is_safe_sql(query):
    """Allow only one read-only SELECT statement."""
    query = query.strip()

    if not query.upper().startswith("SELECT"):
        return False

    query_body = query.rstrip(";")

    if ";" in query_body:
        return False

    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", query.upper()):
            return False

    return True


# ============================================================
# DISCOUNT NORMALIZATION
# ============================================================

def normalize_discount_query(query):
    """
    Convert incorrect whole-number discount comparisons to decimals.

    Example:
    discount >= 50
    becomes:
    discount >= 0.50
    """

    pattern = r"(discount\s*(?:>=|<=|>|<|=)\s*)(\d+(?:\.\d+)?)"

    def replace(match):
        operator = match.group(1)
        value = float(match.group(2))

        if value > 1:
            value /= 100

        return f"{operator}{value:.2f}"

    return re.sub(
        pattern,
        replace,
        query,
        flags=re.IGNORECASE
    )


# ============================================================
# GENERATE SQL
# ============================================================

def generate_sql_query(question):
    response = client_sql.chat.completions.create(
        messages=[
            {"role": "system", "content": sql_prompt},
            {"role": "user", "content": question}
        ],
        model=GROQ_MODEL,
        temperature=0.2,
        max_tokens=1024
    )

    return response.choices[0].message.content


# ============================================================
# RUN SQL
# ============================================================

def run_query(query):
    """Execute validated SELECT query and return maximum 10 rows."""

    if not is_safe_sql(query):
        return None

    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(query, conn)

    return df.head(10)


# ============================================================
# NATURAL-LANGUAGE RESPONSE
# ============================================================

def data_comprehension(question, products):
    """Stream a clean natural-language answer from product results."""

    stream = client_sql.chat.completions.create(
        messages=[
            {"role": "system", "content": comprehension_prompt},
            {
                "role": "user",
                "content": f"QUESTION: {question}\nPRODUCTS: {products}"
            }
        ],
        model=GROQ_MODEL,
        temperature=0.2,
        max_tokens=500,
        stream=True
    )

    for chunk in stream:
        content = chunk.choices[0].delta.content

        if content:
            yield content


# ============================================================
# ERROR RESULT
# ============================================================

def error_result(message):
    """Return the same dictionary structure for every SQL response."""

    def error_stream():
        yield message

    return {
        "route": "sql",
        "stream": error_stream(),
        "sql_query": None,
        "products": None
    }


# ============================================================
# SQL CHAIN
# ============================================================

def sql_chain(question):
    """
    Complete SQL pipeline:

    Question
        ↓
    Groq generates SQL
        ↓
    Validate SQL
        ↓
    Normalize discount values
        ↓
    SQLite
        ↓
    Product results
        ↓
    Groq natural-language response
    """

    sql_response = generate_sql_query(question)

    matches = re.findall(
        r"<SQL>(.*?)</SQL>",
        sql_response,
        re.DOTALL | re.IGNORECASE
    )

    if not matches:
        return error_result(
            "Sorry, I couldn't generate a product search for that question."
        )

    query = matches[0].strip()

    # Convert discount values such as 50 to 0.50.
    query = normalize_discount_query(query)

    print(f"[SQL] {query}")

    # Safety validation happens after normalization.
    if not is_safe_sql(query):
        print(f"[SQL BLOCKED] {query}")

        return error_result(
            "Sorry, I can't run that because the generated search is not safe."
        )

    try:
        response_df = run_query(query)
    except Exception as e:
        print(f"[SQL ERROR] {e}")

        return error_result(
            "Sorry, there was a problem searching the products."
        )

    if response_df is None or response_df.empty:
        return error_result(
            "Sorry, I couldn't find any matching products."
        )

    # Convert DataFrame rows into JSON-friendly dictionaries.
    products = response_df.to_dict(
        orient="records"
    )

    return {
        "route": "sql",
        "stream": data_comprehension(
            question,
            products
        ),
        "sql_query": query,
        "products": products
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    question = "Which products have 50% discount?"

    result = sql_chain(question)

    for token in result["stream"]:
        print(token, end="", flush=True)

    print("\n")
    print("SQL:", result["sql_query"])