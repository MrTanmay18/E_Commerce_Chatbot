# 🛍️ E-Commerce AI Chatbot

An AI-powered e-commerce chatbot that combines **Semantic Routing, RAG,
Text-to-SQL, SQLite, ChromaDB, Groq and Streamlit** to answer
product-search, FAQ and small-talk queries through a single
conversational interface.

The project is designed around a simple principle:

> **Use the most appropriate technique for each type of user query
> instead of sending every query directly to an LLM.**

------------------------------------------------------------------------

## 1. Problem Statement

An e-commerce assistant needs to handle different categories of
questions:

-   **Product queries** require exact filtering, sorting and numerical
    comparisons.
-   **FAQ queries** require answers grounded in predefined business
    information.
-   **Small-talk** requires natural conversational responses and
    context.

Examples:

  User Query                          Route        Solution
  ----------------------------------- ------------ -----------------------------
  Show Nike shoes under ₹3000         SQL          Groq + SQLite
  Which products have 50% discount?   SQL          Groq + SQLite
  Show top 5 shoes by rating          SQL          Groq + SQLite
  What is the return policy?          FAQ          RAG + ChromaDB
  How long does a refund take?        FAQ          RAG + ChromaDB
  How are you?                        small-talk   Groq + conversation history

------------------------------------------------------------------------

## 2. Solution Architecture

``` text
                         USER
                           │
                           ▼
                    ┌─────────────┐
                    │  Streamlit  │
                    │     UI      │
                    └──────┬──────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Semantic Router │
                  └────────┬────────┘
                           │
             ┌─────────────┼─────────────┐
             │             │             │
             ▼             ▼             ▼
           FAQ            SQL        small-talk
             │             │             │
             ▼             ▼             ▼
        ChromaDB         Groq          Groq
          + RAG       Text-to-SQL      + History
             │             │             │
             ▼             ▼             │
          Retrieved     SQL Safety       │
            Data        Validation       │
                           │             │
                           ▼             │
                         SQLite          │
                           │             │
                           ▼             │
                    Product Results      │
                           │             │
                           ▼             │
                         Groq             │
                           │             │
                           └──────┬──────┘
                                  ▼
                             Final Answer
                                  │
                                  ▼
                            Streamlit UI
```

------------------------------------------------------------------------

## 3. Main Components

### Semantic Router

The router classifies the user query into three routes:

``` text
faq
sql
small-talk
```

This makes the application modular and avoids unnecessary LLM calls.

### FAQ Route

``` text
User Question
      ↓
Semantic Router
      ↓
FAQ Route
      ↓
ChromaDB
      ↓
Relevant FAQ Documents
      ↓
Groq
      ↓
Grounded Answer
```

The FAQ route is suitable for questions such as:

``` text
What is the return policy?
How can I track my order?
What payment methods are accepted?
How long does a refund take?
```

### SQL Route

``` text
User Question
      ↓
Semantic Router
      ↓
SQL Route
      ↓
Groq Text-to-SQL
      ↓
Extract SQL
      ↓
Validate SQL
      ↓
SQLite
      ↓
Product Rows
      ├──────────────→ Groq → Natural-language response
      └──────────────→ Streamlit → Product cards
```

### Small-talk Route

``` text
User Message
      ↓
Semantic Router
      ↓
small-talk
      ↓
Groq + Conversation History
      ↓
Conversational Response
```

------------------------------------------------------------------------

# 4. Product Data Pipeline

The project contains a separate web-scraping and database-update
pipeline.

``` text
E-commerce Website
        ↓
Selenium Scraper
        ↓
CSV Files
        ↓
Staging Area
        ↓
Validation / Duplicate Handling
        ↓
Product Change Report
        ↓
Human Review
        ↓
SQLite Database
        ↓
SQL Chatbot
```

This separation is important because the chatbot should query **approved
structured data**, not depend directly on the scraping process during
every user request.

### Human-in-the-loop update flow

``` text
New scraped data
      ↓
staging/flipkart_product_data_new.csv
      ↓
Validate
      ↓
Review product_changes.csv
      ↓
Human approval
      ↓
Backup existing database
      ↓
Update SQLite
```

------------------------------------------------------------------------

# 5. Database Schema

The product database uses the following schema:

``` sql
CREATE TABLE product (
    product_link TEXT,
    title TEXT,
    brand TEXT,
    price INTEGER,
    discount FLOAT,
    avg_rating FLOAT,
    total_ratings INTEGER
);
```

  Column            Type      Description
  ----------------- --------- ---------------------------------
  `product_link`    TEXT      Product URL
  `title`           TEXT      Product name/title
  `brand`           TEXT      Brand name
  `price`           INTEGER   Price in INR
  `discount`        FLOAT     Discount represented as decimal
  `avg_rating`      FLOAT     Average rating
  `total_ratings`   INTEGER   Total number of ratings

### Discount representation

The database stores discounts as fractions:

``` text
10% → 0.10
20% → 0.20
30% → 0.30
50% → 0.50
```

Therefore a query such as:

``` text
Which products have 50% discount?
```

should translate to a condition such as:

``` sql
WHERE discount >= 0.50
```

------------------------------------------------------------------------

# 6. Text-to-SQL Design

The SQL route uses Groq to convert natural language into SQL.

For example:

### User

``` text
Show top 3 Nike shoes by rating
```

### Generated SQL

``` sql
SELECT *
FROM product
WHERE brand LIKE '%Nike%'
ORDER BY avg_rating DESC
LIMIT 3;
```

The application then:

1.  Extracts the SQL from `<SQL>...</SQL>`.
2.  Checks that it is a read-only `SELECT`.
3.  Rejects multiple SQL statements.
4.  Blocks destructive SQL keywords.
5.  Applies project-specific normalization where required.
6.  Executes the query against SQLite.
7.  Limits the returned rows.
8.  Sends structured results to the response layer.

------------------------------------------------------------------------

# 7. SQL Safety

LLM-generated SQL is treated as untrusted input.

The project includes application-level validation to reject operations
such as:

``` text
INSERT
UPDATE
DELETE
DROP
ALTER
ATTACH
DETACH
PRAGMA
CREATE
TRUNCATE
VACUUM
REINDEX
```

The application also rejects stacked statements.

### Important production improvement

Keyword filtering alone is not a complete security mechanism. A
production implementation should additionally use:

-   Read-only database credentials
-   SQL parser / AST validation
-   Table and column allowlists
-   Query timeouts
-   Resource limits

------------------------------------------------------------------------

# 8. FAQ RAG

FAQ information is stored in:

``` text
app/resources/faq_data.csv
```

The FAQ route converts FAQ content into embeddings and stores them in a
vector database.

When a user asks a semantically similar question, the most relevant FAQ
information is retrieved and supplied to the LLM.

This allows queries such as:

``` text
Can I get my money back?
```

to retrieve information related to:

``` text
What is the return policy of the products?
```

even though the wording is different.

------------------------------------------------------------------------

# 9. Project Structure

The following structure reflects the project organization:

``` text
E_Commerce_Chatbot/
│
├── app/
│   ├── resources/
│   │   ├── architecture-diagram.png
│   │   ├── ecommerce_data_final.csv
│   │   ├── faq_data.csv
│   │   └── product-ss.png
│   │
│   ├── .env
│   ├── db.sqlite
│   ├── faq.py
│   ├── main.py
│   ├── router.py
│   ├── smalltalk.py
│   └── sql.py
│
├── web-scrapping/
│   ├── archive/
│   │
│   ├── staging/
│   │   ├── failed_products_new.csv
│   │   ├── flipkart_product_data_new.csv
│   │   ├── flipkart_product_links_new.csv
│   │   ├── product_changes.csv
│   │   └── unavailable_products_new.csv
│   │
│   ├── csv_to_sqlite.py
│   ├── db.sqlite
│   ├── duplicate_products.csv
│   ├── failed_products.csv
│   ├── flipkart_data_extraction.py
│   ├── flipkart_product_data.csv
│   ├── flipkart_product_links.csv
│   └── unavailable_products.csv
│
├── README.md
└── requirements.txt
```

> **Security note:** `.env` contains API credentials and should not be
> committed to GitHub. Add it to `.gitignore`.

------------------------------------------------------------------------

# 10. Important Files

  ---------------------------------------------------------------------------------
  File                                          Responsibility
  --------------------------------------------- -----------------------------------
  `app/main.py`                                 Streamlit application and route
                                                orchestration

  `app/router.py`                               Semantic query classification

  `app/sql.py`                                  Text-to-SQL, validation, SQLite
                                                execution and response generation

  `app/faq.py`                                  FAQ ingestion and RAG pipeline

  `app/smalltalk.py`                            Small-talk response generation

  `app/db.sqlite`                               Product database used by the
                                                chatbot

  `app/resources/faq_data.csv`                  FAQ knowledge base

  `app/resources/ecommerce_data_final.csv`      Product data resource

  `web-scrapping/flipkart_data_extraction.py`   Product data extraction

  `web-scrapping/csv_to_sqlite.py`              CSV validation and SQLite update

  `web-scrapping/staging/`                      Temporary/staged data awaiting
                                                approval

  `web-scrapping/archive/`                      Archived scraping data

  `requirements.txt`                            Python dependencies
  ---------------------------------------------------------------------------------

------------------------------------------------------------------------

# 11. Technology Stack

  Technology              Purpose
  ----------------------- ----------------------------------
  Python                  Core application
  Streamlit               Interactive chatbot UI
  Groq                    LLM inference
  Semantic Router         Query routing
  ChromaDB                Vector storage for FAQ retrieval
  Sentence Transformers   Embeddings
  SQLite                  Structured product database
  Pandas                  Data processing
  Selenium                Product data extraction
  python-dotenv           Environment configuration
  pandasql                SQL-related data operations

------------------------------------------------------------------------

# 12. Installation

### Clone the project

``` bash
git clone <YOUR_REPOSITORY_URL>
cd E_Commerce_Chatbot
```

### Create virtual environment

Windows:

``` bash
python -m venv venv
venv\Scripts\activate
```

### Install dependencies

``` bash
pip install -r requirements.txt
```

Example `requirements.txt`:

``` text
streamlit
pandas
pandasql
python-dotenv
groq
semantic-router[local]
chromadb
sentence_transformers
```

If your final implementation imports additional packages, add them to
`requirements.txt` before deployment.

------------------------------------------------------------------------

# 13. Environment Configuration

Create a `.env` file inside the `app` directory if that is where the
application loads environment variables from:

``` env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=your_groq_model
```

Never expose the API key in source code.

Recommended `.gitignore`:

``` text
.env
venv/
__pycache__/
*.pyc
```

------------------------------------------------------------------------

# 14. Running the Chatbot

From the project root:

``` bash
streamlit run app/main.py
```

The application will open in the browser.

------------------------------------------------------------------------

# 15. Running the Data Pipeline

The data extraction and database update process is separate from the
chatbot.

### Step 1 --- Extract product data

``` bash
cd web-scrapping
python flipkart_data_extraction.py
```

The new dataset is written into the staging area.

### Step 2 --- Review staged data

Check:

``` text
staging/flipkart_product_data_new.csv
staging/product_changes.csv
```

Also review failure/unavailable-product reports where applicable.

### Step 3 --- Update SQLite

``` bash
python csv_to_sqlite.py
```

The update process validates the dataset and updates the SQLite
database.

### Step 4 --- Run chatbot

``` bash
cd ..
streamlit run app/main.py
```

------------------------------------------------------------------------

# 16. Example Queries

### SQL / Product

``` text
Show top 5 Nike shoes
```

``` text
Show shoes under ₹3000
```

``` text
Which products have 50% discount?
```

``` text
Show products with rating above 4
```

``` text
Show Puma shoes between ₹2000 and ₹5000
```

``` text
Show the top 3 products by rating
```

### FAQ

``` text
What is the return policy?
```

``` text
How long does a refund take?
```

``` text
What payment methods are accepted?
```

``` text
How can I track my order?
```

### Small-talk

``` text
Hi
```

``` text
How are you?
```

``` text
What is your name?
```

``` text
Are you a robot?
```

------------------------------------------------------------------------

# 17. Evaluation Strategy

A good evaluation should test each component independently and then
evaluate the complete system.

## Router Evaluation

Use a labeled dataset containing expected routes.

Metrics:

``` text
Accuracy
Precision
Recall
F1-score
No-route rate
```

Example:

``` text
Question: Show Nike shoes under ₹3000
Expected: sql
Predicted: sql
Result: Correct
```

## Text-to-SQL Evaluation

The most important metric is **execution/result accuracy** rather than
only exact SQL string matching.

``` text
Question
   ↓
Generated SQL
   ↓
SQLite execution
   ↓
Compare returned result with expected result
```

Two different SQL queries can be logically equivalent, so execution
accuracy is more meaningful than exact string matching.

## RAG Evaluation

Useful metrics:

``` text
Recall@K
Precision@K
Answer correctness
Groundedness
Hallucination rate
```

## End-to-End Evaluation

Measure:

``` text
Route accuracy
SQL execution accuracy
FAQ retrieval quality
Final answer correctness
Hallucination rate
Latency
Failure rate
```

------------------------------------------------------------------------

# 18. Reliability Considerations

The architecture intentionally combines deterministic and generative
components.

``` text
LLM
 │
 ├── Generates SQL
 │       ↓
 │   Code validation
 │       ↓
 │   SQLite
 │
 ├── Generates FAQ answer
 │       ↑
 │   Retrieved documents
 │
 └── Generates small-talk
         ↑
     Conversation history
```

This reduces the amount of responsibility placed on the LLM.

The LLM is used for:

-   Natural-language understanding
-   SQL generation
-   Answer generation
-   Conversational responses

Deterministic code is used for:

-   Routing
-   SQL validation
-   Database execution
-   Data validation
-   Product rendering
-   Database update workflow

------------------------------------------------------------------------

# 19. Design Decisions

### Why Semantic Router?

The project has a small number of well-defined routes. Semantic
similarity is lightweight and easier to control than using an additional
LLM call for classification.

### Why SQL for products?

Product questions frequently involve exact numerical and categorical
operations:

``` text
price < 3000
discount >= 0.50
rating > 4
ORDER BY avg_rating DESC
LIMIT 5
```

SQL is more appropriate than semantic similarity for these operations.

### Why RAG for FAQs?

FAQ questions are answered from a controlled knowledge base. RAG
provides semantic retrieval while keeping the answer grounded in
project-specific information.

### Why SQLite?

The project is designed around a compact structured product catalog.
SQLite is simple, lightweight and sufficient for project-scale
workloads.

### Why Groq?

Fast inference is useful for an interactive chatbot where response
latency affects user experience.

### Why human approval?

Scraped data can contain missing, duplicate, unavailable or incorrectly
extracted records. Human review provides a quality gate before replacing
the approved dataset.

------------------------------------------------------------------------

# 20. Limitations

-   Product freshness depends on the scraping/update process.
-   Semantic Router performance depends on representative utterances and
    thresholds.
-   LLM-generated SQL can still be incorrect.
-   Basic SQL keyword filtering is not a complete production security
    solution.
-   SQLite is suitable for project-scale data but is not ideal for
    high-concurrency production workloads.
-   FAQ answer quality depends on the coverage and correctness of the
    FAQ dataset.
-   Scraping-based data collection can be affected by website structure
    changes and access restrictions.

------------------------------------------------------------------------

# 21. Future Improvements

### Data

-   Use an official product API where available.
-   Add scheduled data refresh.
-   Add timestamps such as `last_updated`.
-   Add stronger change detection.
-   Automate data-quality reports.

### Database

-   Move to PostgreSQL for production.
-   Add indexes for frequently queried fields.
-   Add a unique product identifier.
-   Store historical product-price changes if required.

### RAG

-   Add better chunking.
-   Add metadata filtering.
-   Add reranking.
-   Add retrieval evaluation.
-   Persist and version the vector database.

### SQL Agent

-   Use an SQL parser/AST validator.
-   Add read-only DB credentials.
-   Add table/column allowlists.
-   Add query timeout and resource limits.
-   Add automated Text-to-SQL regression tests.

### Application

-   Add authentication.
-   Add logging and monitoring.
-   Add caching.
-   Add feedback buttons.
-   Add API/backend separation for production deployment.

------------------------------------------------------------------------

# 22. Testing Checklist

### Routing

-   [ ] FAQ query routes to `faq`
-   [ ] Product query routes to `sql`
-   [ ] Greeting routes to `small-talk`
-   [ ] Unknown query produces a controlled fallback
-   [ ] `None` router result is handled safely

### SQL

-   [ ] Brand filter
-   [ ] Price filter
-   [ ] Discount filter
-   [ ] Rating filter
-   [ ] Top-N query
-   [ ] Multiple filters
-   [ ] No-result query
-   [ ] Invalid SQL
-   [ ] Unsafe SQL
-   [ ] Empty database

### FAQ

-   [ ] Exact question
-   [ ] Paraphrased question
-   [ ] Unrelated question
-   [ ] Missing retrieval

### Small-talk

-   [ ] Greeting
-   [ ] Identity question
-   [ ] Casual conversation
-   [ ] Contextual follow-up

### Data Pipeline

-   [ ] Missing CSV
-   [ ] Missing columns
-   [ ] Duplicate products
-   [ ] Invalid numeric values
-   [ ] Human rejection
-   [ ] Database backup
-   [ ] Successful database update

------------------------------------------------------------------------

# 23. Interview Summary

> **I built a multi-route AI-powered e-commerce chatbot using Streamlit,
> Groq, Semantic Router, ChromaDB and SQLite. The Semantic Router
> classifies incoming queries into FAQ, SQL and small-talk. FAQ queries
> use RAG to retrieve grounded information from the FAQ knowledge base.
> Product queries use Groq to convert natural language into SQL,
> followed by code-level SQL validation and SQLite execution. Small-talk
> uses Groq with conversation history. Product data is maintained
> through a separate scraping-to-CSV-to-SQLite pipeline with validation
> and human approval. The system combines generative AI with
> deterministic database operations to improve reliability, control and
> explainability.**

------------------------------------------------------------------------

# 24. Project Highlights

-   Multi-route GenAI architecture
-   Semantic query routing
-   Retrieval-Augmented Generation
-   Natural-language-to-SQL
-   SQLite structured retrieval
-   ChromaDB semantic retrieval
-   LLM-generated SQL validation
-   Discount normalization
-   Human-in-the-loop data pipeline
-   Interactive Streamlit product cards
-   Component-level evaluation strategy
-   Production scalability considerations

------------------------------------------------------------------------

## 👨‍💻 Author

**Tanmay Pakori**

MSc Mathematics & Data Science

GitHub: [MrTanmay18](https://github.com/MrTanmay18)

------------------------------------------------------------------------

⭐ If you find this project useful, consider starring the repository.
