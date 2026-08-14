import streamlit as st
from pathlib import Path

from faq import ingest_faq_data, faq_chain
from sql import sql_chain
from router import router
from smalltalk import talk


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="E-commerce ChatBot",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>
.block-container {
    max-width: 1100px;
    padding-top: 1.5rem;
}

.chat-header {
    padding: 1.4rem 1.6rem;
    border-radius: 18px;
    margin-bottom: 1.5rem;
    background: linear-gradient(135deg,#1f2937,#111827);
    color: white;
}

.chat-header h1 {
    margin: 0;
    font-size: 2rem;
}

.chat-header p {
    margin: .4rem 0 0;
    color: #d1d5db;
}

.status {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin-top: .8rem;
    padding: 5px 10px;
    border-radius: 20px;
    background: rgba(255,255,255,.12);
    color: #e5e7eb;
    font-size: .8rem;
}

.status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #22c55e;
}

.product-card {
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 1rem;
    margin: .7rem 0;
    background: white;
}

.product-card:hover {
    border-color: #c7d2fe;
    box-shadow: 0 6px 20px rgba(0,0,0,.06);
}

.product-number {
    color: #6b7280;
    font-size: .75rem;
    font-weight: 600;
}

.product-title {
    font-size: 1rem;
    font-weight: 650;
    color: #111827;
    margin: .3rem 0 .7rem;
}

.product-price {
    font-size: 1.15rem;
    font-weight: 700;
    color: #111827;
}

.product-discount {
    display: inline-block;
    margin-left: 7px;
    padding: 3px 8px;
    border-radius: 8px;
    background: #dcfce7;
    color: #15803d;
    font-size: .78rem;
    font-weight: 600;
}

.product-meta {
    color: #6b7280;
    font-size: .83rem;
    margin-top: .45rem;
}

.product-link {
    display: inline-block;
    margin-top: .75rem;
    padding: 7px 12px;
    border-radius: 9px;
    background: #111827;
    color: white !important;
    text-decoration: none !important;
    font-size: .82rem;
    font-weight: 600;
}

.product-link:hover {
    background: #374151;
}

.sidebar-title {
    font-size: 1.25rem;
    font-weight: 700;
}

.sidebar-text {
    color: #6b7280;
    font-size: .85rem;
}

.feature-box {
    padding: .8rem;
    margin: .6rem 0;
    border-radius: 12px;
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    font-size: .85rem;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# FAQ DATA
# ============================================================

faqs_path = Path(__file__).parent / "resources" / "faq_data.csv"
ingest_faq_data(faqs_path)


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown(
        '<div class="sidebar-title">🛍️ E-commerce Assistant</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p class="sidebar-text">'
        'AI shopping assistant for products, FAQs and casual conversation.'
        '</p>',
        unsafe_allow_html=True
    )

    st.divider()

    st.markdown("### 💡 What can I ask?")

    st.markdown(
        '<div class="feature-box">🔎 Find products by brand, price or rating</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="feature-box">🏷️ Find products with discounts</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="feature-box">❓ Ask store FAQs</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="feature-box">💬 Have a casual conversation</div>',
        unsafe_allow_html=True
    )

    st.divider()

    st.markdown("### ⚡ Quick questions")

    quick_questions = [
        "Show top 5 Nike shoes",
        "Products under ₹3000",
        "Which products have 50% discount?",
        "What is the return policy?"
    ]

    for question in quick_questions:
        if st.button(
            question,
            use_container_width=True,
            key=f"quick_{question}"
        ):
            st.session_state.pending_query = question

    st.divider()

    if st.button(
        "🗑️ Clear conversation",
        use_container_width=True
    ):
        st.session_state.messages = []
        st.rerun()


# ============================================================
# HEADER
# ============================================================

st.markdown("""
<div class="chat-header">
<h1>🛍️ E-commerce ChatBot</h1>
<p>Find products, compare prices, check FAQs and chat naturally.</p>
<div class="status">
<span class="status-dot"></span>
AI Assistant Online
</div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# CHAT HISTORY
# ============================================================

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ============================================================
# ROUTER
# ============================================================

def ask(query, conversation_history):
    """Send the query to the correct route."""

    route_result = router(query)

    # Prevent None.name error when no route matches.
    if route_result is None:
        return {
            "route": "unknown",
            "response": "I couldn't understand that. Try asking about products, prices, discounts or store policies."
        }

    route = route_result.name

    print(f"[ROUTER] {query} -> {route}")

    if route == "faq":
        return {
            "route": "faq",
            "response": faq_chain(query)
        }

    if route == "sql":
        return sql_chain(query)

    if route == "small-talk":
        return {
            "route": "small-talk",
            "response": talk(
                query,
                conversation_history
            )
        }

    return {
        "route": "unknown",
        "response": "I couldn't understand that."
    }


# ============================================================
# USER INPUT
# ============================================================

query = st.chat_input(
    "Ask about products, prices, discounts or anything else..."
)

# Process sidebar quick question.
if "pending_query" in st.session_state:
    query = st.session_state.pop("pending_query")


# ============================================================
# PROCESS QUERY
# ============================================================

if query:

    # Display user message.
    with st.chat_message("user"):
        st.markdown(query)

    # Copy history before adding current message.
    # This gives small-talk access to previous conversation only.
    conversation_history = st.session_state.messages.copy()

    st.session_state.messages.append({
        "role": "user",
        "content": query
    })

    result = ask(
        query,
        conversation_history
    )

    route = result["route"]


    # ========================================================
    # FAQ / SMALL-TALK / UNKNOWN
    # ========================================================

    if route in ("faq", "small-talk", "unknown"):

        response = result["response"]

        with st.chat_message("assistant"):
            st.markdown(response)

        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })


    # ========================================================
    # SQL / PRODUCT ROUTE
    # ========================================================

    elif route == "sql":

        with st.chat_message("assistant"):

            # Stream the natural-language answer.
            stream = result.get("stream")
            full_response = ""

            if stream:
                response_placeholder = st.empty()

                for token in stream:
                    full_response += token
                    response_placeholder.markdown(full_response)

            # Display product cards.
            products = result.get("products")

            if products:
                st.markdown("### 🛍️ Matching Products")

                for i, product in enumerate(products, 1):

                    title = product.get(
                        "title",
                        "Unknown Product"
                    )

                    price = product.get("price")
                    discount = product.get("discount")
                    rating = product.get("avg_rating")
                    total_ratings = product.get("total_ratings")
                    link = product.get("product_link")

                    # Format price.
                    price_text = (
                        f"₹{int(price):,}"
                        if price is not None
                        else "Price unavailable"
                    )

                    # Format discount.
                    if discount is not None:
                        discount_value = float(discount)

                        if discount_value <= 1:
                            discount_text = (
                                f"{discount_value * 100:.0f}% off"
                            )
                        else:
                            discount_text = (
                                f"{discount_value:.0f}% off"
                            )
                    else:
                        discount_text = "No discount"

                    # Format rating.
                    rating_text = (
                        f"{float(rating):.1f}"
                        if rating is not None
                        else "N/A"
                    )

                    # Format rating count.
                    ratings_text = (
                        f"{int(total_ratings):,} ratings"
                        if total_ratings is not None
                        else ""
                    )

                    # Product URL.
                    link_html = ""

                    if link:
                        link_html = (
                            f'<a class="product-link" '
                            f'href="{link}" '
                            f'target="_blank">'
                            f'🛒 View Product'
                            f'</a>'
                        )

                    # IMPORTANT:
                    # HTML starts at column 1 inside the string.
                    # This prevents Streamlit from treating it as code.
                    card_html = f"""<div class="product-card">
<div class="product-number">PRODUCT {i}</div>
<div class="product-title">{title}</div>
<div>
<span class="product-price">{price_text}</span>
<span class="product-discount">{discount_text}</span>
</div>
<div class="product-meta">⭐ {rating_text}/5 &nbsp; • &nbsp; {ratings_text}</div>
{link_html}
</div>"""

                    st.markdown(
                        card_html,
                        unsafe_allow_html=True
                    )

        # Store only the natural-language answer.
        st.session_state.messages.append({
            "role": "assistant",
            "content": full_response
        })