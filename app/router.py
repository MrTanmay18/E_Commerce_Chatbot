from semantic_router import Route
from semantic_router.routers import SemanticRouter
from semantic_router.encoders import HuggingFaceEncoder


# Load embedding model
encoder = HuggingFaceEncoder(
    name="sentence-transformers/all-MiniLM-L6-v2"
)


# ============================================================
# FAQ ROUTE
# ============================================================

faq = Route(
    name="faq",
    utterances=[
        # Return policy
        "What is the return policy?",
        "What is your return policy?",
        "Can I return a product?",
        "How can I return my order?",
        "How many days do I have to return a product?",
        "Can I return an item after delivery?",
        "What are the conditions for returning a product?",
        "I want to return something I purchased.",
        "How do I get a refund for a returned product?",

        # Defective / damaged products
        "What if I receive a defective product?",
        "What should I do if my product is defective?",
        "I received a damaged product.",
        "Can I return a damaged item?",
        "My product arrived broken, what should I do?",
        "What happens if my order is damaged?",
        "I received a faulty product, can I get a replacement?",
        "Can I get a replacement for a defective product?",

        # Payment
        "What payment methods do you accept?",
        "Which payment methods are available?",
        "Can I pay using a credit card?",
        "Can I pay using UPI?",
        "Do you accept debit cards?",
        "Can I pay with cash on delivery?",
        "Is cash on delivery available?",

        # Discounts / offers
        "Do you offer discounts?",
        "Are there any discounts available?",
        "Do I get a discount with an HDFC credit card?",
        "Are there any credit card offers?",
        "What offers are available on credit cards?",
        "Are there any bank discounts?",
        "Do you have any current offers?",

        # Order tracking
        "How can I track my order?",
        "Where can I track my order?",
        "How do I check my order status?",
        "Can I track my package?",
        "Where is my order?",
        "How can I find my delivery status?",
        "I want to know where my order is.",

        # Refund
        "How long does a refund take?",
        "When will I receive my refund?",
        "How long does it take to process a refund?",
        "When will my refund be credited?",
        "How can I check my refund status?",
        "What is the refund process?",
        "How do I get my money back?",

        # General policies
        "What is your cancellation policy?",
        "Can I cancel my order?",
        "How can I cancel an order?",
        "Can I change my delivery address?",
        "What is your shipping policy?",
        "How long does delivery take?",
        "What are the delivery charges?",
    ]
)


# ============================================================
# SQL / PRODUCT ROUTE
# ============================================================

sql = Route(
    name="sql",
    utterances=[
        # Product search
        "Show me Nike shoes.",
        "I want to buy Nike shoes.",
        "Find me Puma shoes.",
        "Show me Adidas shoes.",
        "Do you have running shoes?",
        "Show me formal shoes.",
        "I am looking for sports shoes.",
        "Find shoes for men.",
        "Find shoes for women.",
        "Show me available shoes.",

        # Price
        "What is the price of Puma running shoes?",
        "How much do Nike shoes cost?",
        "Show me shoes under Rs. 3000.",
        "Are there any shoes below 3000?",
        "Find shoes between Rs. 5000 and Rs. 10000.",
        "Show me products between 2000 and 5000.",
        "I need shoes under 5000.",
        "Find cheap running shoes.",
        "What are the cheapest Nike shoes?",

        # Discount
        "I want Nike shoes with 50% discount.",
        "Show me shoes with discounts.",
        "Which shoes are on sale?",
        "Are there any Puma shoes on sale?",
        "Show me products with more than 30% discount.",
        "Find discounted Nike shoes.",
        "Which products have the highest discount?",
        "Show me shoes with at least 20% off.",

        # Size
        "Do you have formal shoes in size 9?",
        "Show me Nike shoes in size 10.",
        "Do you have Puma shoes in size 8?",
        "Find shoes available in size 9.",
        "Which shoes are available in size 7?",
        "I need running shoes in size 10.",
        "Show me products available in my size.",

        # Brand
        "Show me all Puma shoes.",
        "What Nike shoes do you have?",
        "Find Adidas products.",
        "Show me products from Puma.",
        "Do you have Nike running shoes?",
        "Show me Adidas shoes under 5000.",
        "Find Puma shoes below 3000.",

        # Product comparison / filtering
        "Which Nike shoes are cheapest?",
        "Show me the most expensive shoes.",
        "Find shoes with the highest discount.",
        "Show me running shoes under 4000.",
        "Find black Nike shoes.",
        "Show me red Puma shoes.",
        "Find formal shoes under 5000.",
        "Show me shoes with a discount between 20 and 50 percent.",
    ]
)


# ============================================================
# SMALL TALK ROUTE
# ============================================================

small_talk = Route(
    name="small-talk",
    utterances=[
        # Greetings
        "hi",
        "hii",
        "hello",
        "hey",
        "hey there",
        "hi there",
        "hello there",
        "good morning",
        "good afternoon",
        "good evening",

        # How are you?
        "how are you",
        "how are you doing",
        "how are you today",
        "how is it going",
        "how are things",
        "how have you been",

        # Responses to how are you
        "good",
        "fine",
        "great",
        "okay",
        "ok",
        "not bad",
        "I'm good",
        "I am good",
        "I'm fine",
        "I am fine",
        "doing good",
        "doing great",
        "doing well",
        "I'm doing well",
        "I am doing well",
        "pretty good",
        "I'm great",

        # Identity
        "what is your name",
        "what's your name",
        "who are you",
        "tell me your name",
        "what should I call you",

        # AI / Robot
        "are you a robot",
        "are you a bot",
        "are you an AI",
        "are you artificial intelligence",
        "are you human",
        "are you a chatbot",
        "are you a real person",

        # Capabilities
        "what are you",
        "what do you do",
        "what can you do",
        "what can you help me with",
        "how can you help me",
        "what is your purpose",

        # Casual conversation
        "nice to meet you",
        "thanks",
        "thank you",
        "thank you for your help",
        "cool",
        "awesome",
        "bye",
        "goodbye",
        "see you later",
    ]
)


# ============================================================
# CREATE ROUTER
# ============================================================

router = SemanticRouter(
    routes=[faq, sql, small_talk],
    encoder=encoder,
    auto_sync="local"
)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    test_queries = [
        "hi",
        "hii",
        "hello",
        "how are you",
        "how are you doing",
        "are you a robot",
        "what are you",
        "what do you do",
        "what is your name",
    ]

    for query in test_queries:
        result = router(query)
        print(f"{query} --> {result}")