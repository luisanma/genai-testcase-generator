#!/usr/bin/env python
"""
Script to regenerate the ML categorizer model
"""

import os
import sys

# Add the project root to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.ml_categorizer import categorizer

# Force model regeneration by creating a new instance
print("Regenerating ML categorization model...")
print(f"Available categories: {categorizer.categories}")

# Evaluate the model
eval_results = categorizer.evaluate_model()
print(f"Model evaluation results: {eval_results}")
print("Model regeneration complete!") 