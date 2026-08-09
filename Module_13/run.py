"""
Module 13: Flask Web App - "Will You Get In?"

This Flask app integrates the trained admissions predictor
into a web interface where users can enter applicant information
and receive a prediction.
"""

import os
import json
import torch
import pandas as pd
import numpy as np
from flask import Flask, render_template, request, jsonify
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Import inference functions
from inference import load_model, predict, create_unified_text

# Initialize Flask app
app = Flask(__name__)

# Load the model once at startup
print("Loading model...")
model, tokenizer, idx_to_label, label_map = load_model()
print(f"Model loaded! Label mapping: {label_map}")


@app.route('/')
def index():
    """Home page - redirect to the prediction page."""
    return render_template('will_you_get_in.html')


@app.route('/will-you-get-in')
def will_you_get_in():
    """Main prediction page."""
    return render_template('will_you_get_in.html')


@app.route('/predict', methods=['POST'])
def make_prediction():
    """
    Handle form submission and return a prediction.
    """
    try:
        # Collect form data
        applicant_data = {
            'program': request.form.get('program', ''),
            'comments': request.form.get('comments', ''),
            'llm_generated_program': request.form.get('llm_generated_program', ''),
            'llm_generated_university': request.form.get('llm_generated_university', ''),
            'term': request.form.get('term', ''),
            'degree': request.form.get('degree', ''),
            'us_or_international': request.form.get('us_or_international', ''),
            'gpa': float(request.form.get('gpa')) if request.form.get('gpa') else None,
            'gre': float(request.form.get('gre')) if request.form.get('gre') else None,
            'gre_v': float(request.form.get('gre_v')) if request.form.get('gre_v') else None,
            'gre_aw': float(request.form.get('gre_aw')) if request.form.get('gre_aw') else None,
        }
        
        # Validate required fields
        if not applicant_data['program']:
            return jsonify({'error': 'Program name is required.'}), 400
        
        # Make prediction
        result = predict(applicant_data, model, tokenizer, idx_to_label)
        
        # Get the prediction label and probability
        predicted_label = result['predicted_label']
        probability = result['probability']
        
        # Prepare response
        response = {
            'success': True,
            'prediction': predicted_label,
            'probability': probability,
            'confidence': 'High' if probability > 0.75 else 'Medium' if probability > 0.60 else 'Low',
            'unified_text': result['unified_text']
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/about')
def about():
    """About page with disclaimer."""
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)