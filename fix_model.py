#!/usr/bin/env python
"""
Script to fix the ML categorizer model
"""

import os
import sys
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

# Sample data with all categories
sample_data = [
    # E-commerce samples
    ("Shop our latest products with free shipping on orders over $50. Add items to cart and checkout.", "e-commerce"),
    ("Product catalog with detailed specifications and pricing. Buy now and save 20% on your purchase.", "e-commerce"),
    ("Online store featuring electronics, clothing, and home goods. View shopping cart and payment options.", "e-commerce"),
    ("Best deals on brand name products. Add to wishlist or add to cart for immediate purchase.", "e-commerce"),
    ("Digital marketplace for buying and selling handmade items. Secure checkout and buyer protection.", "e-commerce"),
    
    # Blog samples
    ("Personal blog about travel adventures and photography tips. Read my latest post about sunset photography.", "blog"),
    ("Lifestyle blog featuring recipes, home decor, and family activities. Subscribe for weekly articles.", "blog"),
    ("Tech blog with in-depth tutorials and product reviews. Comment below and share your thoughts.", "blog"),
    ("Author's personal journal documenting creative writing process. Archive of previous blog posts available.", "blog"),
    ("Health and wellness blog with expert advice. Latest post: 10 ways to improve your morning routine.", "blog"),
    
    # News samples
    ("Breaking news: Latest developments in politics, economy, and world events. Subscribe to our newsletter.", "news"),
    ("Daily news updates covering local and international headlines. Reporter John Smith reports from Washington.", "news"),
    ("News analysis and editorial opinions on current events. Read today's top headlines and featured stories.", "news"),
    ("Sports news covering latest games, player transfers, and league standings. Match report and statistics.", "news"),
    ("Technology news featuring product launches and company announcements. Latest industry trends and insights.", "news"),
    
    # Portfolio samples
    ("Designer portfolio showcasing UI/UX projects and creative work. View my case studies and design process.", "portfolio"),
    ("Photography portfolio with galleries organized by theme. Professional headshots and landscape photography.", "portfolio"),
    ("Web developer portfolio with code samples and live project demos. Skills include React, Node, and Python.", "portfolio"),
    ("Artist portfolio featuring paintings, illustrations, and digital art. Commission information and artist CV.", "portfolio"),
    ("Architecture portfolio with 3D renderings and completed building projects. Resume and professional experience.", "portfolio"),
    
    # Corporate samples
    ("Company overview, mission statement, and corporate values. Learn about our team and business strategy.", "corporate"),
    ("Enterprise solutions for businesses of all sizes. Our services include consulting, implementation, and support.", "corporate"),
    ("Meet our executive leadership team and board of directors. Company history and achievements.", "corporate"),
    ("Business partnerships and client testimonials. Industries served and case studies of successful implementations.", "corporate"),
    ("Corporate responsibility initiatives and sustainability reports. How we give back to our community.", "corporate"),
    
    # Educational samples
    ("Online courses in programming, design, and business. Enroll now and start learning with our expert instructors.", "educational"),
    ("University homepage with information for students, faculty, and prospective applicants. Academic programs and majors.", "educational"),
    ("Educational resources for K-12 teachers and students. Lesson plans, worksheets, and interactive activities.", "educational"),
    ("Professional certification programs and continuing education. Industry-recognized credentials and skills assessment.", "educational"),
    ("Learning management system with course materials, assignments, and discussion forums. Student login and registration.", "educational"),
    
    # Social media
    ("Connect with friends, share photos and videos. Create your profile and join the conversation.", "social"),
    ("Social network for professionals. Build your network, find jobs, and share industry knowledge.", "social"),
    ("Photo and video sharing platform. Follow your favorite creators and discover trending content.", "social"),
    ("Community forums and discussion groups on various topics. Join the conversation and meet like-minded people.", "social"),
    ("Real-time updates and short posts about what's happening. Trending topics and hashtag challenges.", "social"),
    
    # Entertainment
    ("Stream your favorite movies and TV shows. New releases and classic titles available on demand.", "entertainment"),
    ("Gaming platform with latest releases and multiplayer options. Create your gamer profile and track achievements.", "entertainment"),
    ("Music streaming service with millions of songs and custom playlists. Listen on any device, anytime.", "entertainment"),
    ("Online videos, channels, and content creators. Subscribe to your favorite channels for updates.", "entertainment"),
    ("Celebrity news, interviews, and entertainment coverage. Behind the scenes and red carpet events.", "entertainment"),
    
    # Banking samples
    ("Online banking login. Access your checking, savings, and credit accounts securely. View statements and transaction history.", "banking"),
    ("Apply for a mortgage, auto loan, or personal loan. Competitive interest rates and flexible payment options.", "banking"),
    ("Banking services for individuals and businesses. Transfer funds, pay bills, and deposit checks remotely.", "banking"),
    ("Mobile banking app that lets you manage your accounts on the go. Secure authentication and instant alerts.", "banking"),
    ("ATM locator, branch hours, and banking services. Schedule an appointment with a financial advisor.", "banking"),
    
    # Financial samples
    ("Investment opportunities and wealth management solutions. Retirement planning and portfolio diversification.", "financial"),
    ("Financial planning services for individuals and families. Tax strategies, estate planning, and asset management.", "financial"),
    ("Market analysis, stock quotes, and investment research. Tools for monitoring your investment performance.", "financial"),
    ("Financial calculators for loans, mortgages, and retirement planning. Estimate your payments and savings goals.", "financial"),
    ("Insurance products including life, health, auto, and home policies. Get a quote and apply online.", "financial"),
    
    # Consulting samples
    ("Management consulting services to improve organizational performance. Strategy development and implementation.", "consulting"),
    ("IT consulting and digital transformation. Cloud migration, cybersecurity, and system integration services.", "consulting"),
    ("Business process optimization and operational excellence. Lean methodology and efficiency improvements.", "consulting"),
    ("Human resources consulting and talent management. Leadership development and organizational culture.", "consulting"),
    ("Strategic consulting for startups and established businesses. Market entry, growth strategy, and competitive analysis.", "consulting"),
    
    # Government samples
    ("Government services portal for citizens. Apply for permits, licenses, and official documents online.", "government"),
    ("Public records, tax information, and municipal regulations. Download forms and schedule appointments.", "government"),
    ("City council meetings, public announcements, and community events. Local government initiatives and programs.", "government"),
    ("Federal agency providing resources and services to the public. Compliance information and regulatory guidelines.", "government"),
    ("Voter registration, election information, and civic engagement opportunities. Government transparency and accountability.", "government"),
]

def create_and_train_model():
    """Create and train a new ML model using sample data"""
    # Extract texts and labels
    texts, labels = zip(*sample_data)
    
    # Create a pipeline with TF-IDF and Multinomial Naive Bayes
    model = Pipeline([
        ('tfidf', TfidfVectorizer(
            stop_words='english',
            min_df=2,
            max_df=0.9,
            ngram_range=(1, 2)
        )),
        ('clf', MultinomialNB())
    ])
    
    # Train the model
    model.fit(texts, labels)
    
    # Ensure the model directory exists
    os.makedirs("app/static/model", exist_ok=True)
    
    # Save the model
    model_file = "app/static/model/website_category_model.pkl"
    with open(model_file, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"New model created and saved to {model_file}")
    
    # Evaluate model with some basic tests
    test_texts = [
        "Login to your bank account and view your recent transactions. Transfer money between accounts.",
        "Our financial advisors help you plan for retirement and manage your investments.",
        "Professional consulting services for businesses looking to optimize their operations.",
        "Apply for a passport and access government services online."
    ]
    
    predictions = model.predict(test_texts)
    
    print("\nTest results:")
    for text, prediction in zip(test_texts, predictions):
        print(f"Text: {text[:50]}...\nPredicted category: {prediction}\n")

if __name__ == "__main__":
    print("Creating new ML model with updated categories...")
    create_and_train_model()
    print("Done!") 