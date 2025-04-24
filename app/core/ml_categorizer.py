import re
import nltk
import logging
import numpy as np
import pickle
import os
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split

# Set up logger
logger = logging.getLogger("web-analysis-framework.ml-categorizer")

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    logger.info("Downloading NLTK punkt package")
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    logger.info("Downloading NLTK stopwords package")
    nltk.download('stopwords', quiet=True)

class MLCategorizer:
    """Machine Learning based website categorizer"""
    
    def __init__(self):
        self.model = None
        self.model_file = "app/static/model/website_category_model.pkl"
        self.categories = [
            'e-commerce', 'blog', 'news', 'portfolio', 
            'corporate', 'educational', 'social', 'entertainment',
            'banking', 'financial', 'consulting', 'government'
        ]
        self.stopwords = set(nltk.corpus.stopwords.words('english'))
        
        self._ensure_model_dir()
        self._load_or_create_model()
    
    def _ensure_model_dir(self):
        """Ensure model directory exists"""
        os.makedirs("app/static/model", exist_ok=True)
    
    def _load_or_create_model(self):
        """Load existing model or create a new one"""
        try:
            if os.path.exists(self.model_file):
                logger.info("Loading existing ML model")
                with open(self.model_file, 'rb') as f:
                    self.model = pickle.load(f)
            else:
                logger.info("Creating and training new ML model")
                self._create_and_train_model()
        except Exception as e:
            logger.error(f"Error loading/creating model: {str(e)}", exc_info=True)
            # Create a fresh model if loading fails
            self._create_and_train_model()
    
    def _create_and_train_model(self):
        """Create and train a new ML model using sample data"""
        # Sample training data (in a real system, this would be a large dataset)
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
        
        # Extract texts and labels
        texts, labels = zip(*sample_data)
        
        # Create a pipeline with TF-IDF and Multinomial Naive Bayes
        self.model = Pipeline([
            ('tfidf', TfidfVectorizer(
                stop_words='english',
                min_df=2,
                max_df=0.9,
                ngram_range=(1, 2)
            )),
            ('clf', MultinomialNB())
        ])
        
        # Train the model
        self.model.fit(texts, labels)
        
        # Save the model
        with open(self.model_file, 'wb') as f:
            pickle.dump(self.model, f)
        
        logger.info("ML model created and trained successfully")
    
    def preprocess_text(self, text):
        """Preprocess text for classification"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and digits
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\d+', ' ', text)
        
        # Tokenize
        tokens = nltk.word_tokenize(text)
        
        # Remove stopwords
        tokens = [word for word in tokens if word not in self.stopwords]
        
        # Join tokens back into string
        return ' '.join(tokens)
    
    def categorize(self, text_content):
        """Categorize website based on its content"""
        if not self.model:
            logger.warning("ML model not available, using fallback method")
            return self._fallback_categorization(text_content)
        
        try:
            # Preprocess the text
            processed_text = self.preprocess_text(text_content)
            
            # Make prediction
            prediction = self.model.predict([processed_text])[0]
            
            # Get probability distribution
            proba = self.model.predict_proba([processed_text])[0]
            max_proba = max(proba)
            
            # If confidence is too low, use fallback
            if max_proba < 0.4:
                logger.info(f"Low confidence prediction ({max_proba:.2f}), using hybrid approach")
                fallback_category = self._fallback_categorization(text_content)
                
                # If ML prediction is different from fallback with low confidence, use fallback
                if prediction != fallback_category:
                    logger.info(f"ML predicted {prediction} but fallback suggested {fallback_category}")
                    return fallback_category
            
            logger.info(f"Website categorized as '{prediction}' with confidence {max_proba:.2f}")
            return prediction
            
        except Exception as e:
            logger.error(f"Error in ML categorization: {str(e)}", exc_info=True)
            return self._fallback_categorization(text_content)
    
    def _fallback_categorization(self, text_content):
        """Fallback keyword-based categorization"""
        categories = {
            "e-commerce": ["shop", "cart", "product", "buy", "price", "store", "checkout", "shipping", "order", "payment"],
            "blog": ["blog", "post", "article", "comment", "author", "publish", "read more", "tags", "categories", "archive"],
            "news": ["news", "article", "headline", "reporter", "editor", "breaking", "latest", "update", "coverage", "report"],
            "portfolio": ["portfolio", "project", "work", "skill", "resume", "cv", "showcase", "gallery", "creative", "designer"],
            "corporate": ["company", "business", "service", "client", "team", "about us", "mission", "values", "industry", "solution"],
            "educational": ["course", "learn", "student", "teacher", "education", "school", "university", "training", "lesson", "quiz"],
            "social": ["profile", "friend", "follow", "share", "connect", "community", "network", "message", "post", "like"],
            "entertainment": ["entertainment", "game", "movie", "music", "play", "stream", "video", "show", "watch", "fun"],
            "banking": ["banking", "bank", "account", "transfer", "deposit", "withdraw", "atm", "branch", "checking", "savings"],
            "financial": ["financial", "investment", "portfolio", "stocks", "bonds", "market", "wealth", "advisor", "retirement", "fund"],
            "consulting": ["consulting", "consultant", "strategy", "analysis", "implementation", "optimization", "assessment", "recommendation", "expertise", "solutions"],
            "government": ["government", "public", "citizen", "official", "regulation", "compliance", "agency", "municipal", "federal", "permit"]
        }
        
        # Convert text to lowercase
        text_content = text_content.lower()
        
        # Count keywords for each category
        scores = {}
        for category, keywords in categories.items():
            score = sum([text_content.count(keyword) for keyword in keywords])
            scores[category] = score
        
        # Determine the highest scoring category
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        else:
            return "unknown"
    
    def evaluate_model(self):
        """Evaluate the model and return accuracy metrics"""
        # Sample evaluation data
        eval_data = [
            ("Shop our clearance sale with discounts up to 70%. Free shipping on orders over $100.", "e-commerce"),
            ("My personal travel journal documenting adventures across Asia. New photos posted weekly.", "blog"),
            ("Breaking news: Government announces new climate policy. Opposition responds with criticism.", "news"),
            ("Graphic design portfolio showcasing branding projects and package design work.", "portfolio"),
            ("Our company provides enterprise IT solutions for financial institutions worldwide.", "corporate"),
            ("Interactive online courses in mathematics, science, and computer programming.", "educational"),
            ("Share your moments with friends and family. Privacy controls for your personal content.", "social"),
            ("Streaming platform for movies, TV shows, and documentaries. Watch on any device.", "entertainment")
        ]
        
        texts, labels = zip(*eval_data)
        
        # Preprocess texts
        processed_texts = [self.preprocess_text(text) for text in texts]
        
        # Predict categories
        predictions = self.model.predict(processed_texts)
        
        # Calculate accuracy
        accuracy = sum(1 for i, pred in enumerate(predictions) if pred == labels[i]) / len(labels)
        
        # Return evaluation results
        return {
            "accuracy": accuracy,
            "samples": len(labels),
            "evaluation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "categories": self.categories
        }

# Create a singleton instance
categorizer = MLCategorizer() 