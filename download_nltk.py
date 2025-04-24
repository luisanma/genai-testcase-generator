#!/usr/bin/env python
"""
Script to download the necessary NLTK resources
"""

import nltk

print("Downloading NLTK resources...")
nltk.download('punkt')
nltk.download('stopwords')
print("NLTK resources downloaded successfully.") 