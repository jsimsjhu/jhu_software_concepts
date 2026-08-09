"""
Module 13: Inference Pipeline for Admissions Prediction

This script loads the fine-tuned model and makes predictions
on new applicant data.
"""

import json
import torch
import pandas as pd
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# ---------------------------------------------------------------------------
# Model Loading
# ---------------------------------------------------------------------------

def load_model(model_dir="./saved_model"):
    """
    Load the fine-tuned model, tokenizer, and label mapping.
    """
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    
    # Load model
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)
    
    # Set to evaluation mode
    model.eval()
    
    # Load label mapping
    with open(f"{model_dir}/label_map.json", 'r') as f:
        label_map = json.load(f)
    
    # Reverse mapping for predictions
    idx_to_label = {v: k for k, v in label_map.items()}
    
    return model, tokenizer, idx_to_label, label_map


def create_unified_text(applicant_data):
    """
    Create a unified text input from applicant data.
    Same format as used during training.
    """
    parts = []
    
    # Text fields
    if applicant_data.get('program'):
        parts.append(f"Program: {applicant_data['program']}")
    if applicant_data.get('comments'):
        parts.append(f"Comments: {applicant_data['comments']}")
    if applicant_data.get('llm_generated_program'):
        parts.append(f"LLM Program: {applicant_data['llm_generated_program']}")
    if applicant_data.get('llm_generated_university'):
        parts.append(f"LLM University: {applicant_data['llm_generated_university']}")
    if applicant_data.get('term'):
        parts.append(f"Term: {applicant_data['term']}")
    
    # Numeric fields
    if applicant_data.get('gpa') is not None:
        parts.append(f"GPA: {applicant_data['gpa']:.2f}")
    if applicant_data.get('gre') is not None:
        parts.append(f"GRE: {applicant_data['gre']:.0f}")
    if applicant_data.get('gre_v') is not None:
        parts.append(f"GRE V: {applicant_data['gre_v']:.0f}")
    if applicant_data.get('gre_aw') is not None:
        parts.append(f"GRE AW: {applicant_data['gre_aw']:.1f}")
    
    # Categorical fields
    if applicant_data.get('degree') and applicant_data['degree'] != 'Unknown':
        parts.append(f"Degree: {applicant_data['degree']}")
    if applicant_data.get('us_or_international') and applicant_data['us_or_international'] != 'Unknown':
        parts.append(f"Citizenship: {applicant_data['us_or_international']}")
    
    return "\n".join(parts)


def predict(applicant_data, model, tokenizer, idx_to_label, max_length=256):
    """
    Make a prediction for a single applicant.
    
    Args:
        applicant_data: dict with applicant fields
        model: loaded PyTorch model
        tokenizer: loaded tokenizer
        idx_to_label: dict mapping index to label
        max_length: maximum sequence length
    
    Returns:
        dict with prediction, probability, and unified text
    """
    # Create unified text
    unified_text = create_unified_text(applicant_data)
    
    # Tokenize
    inputs = tokenizer(
        unified_text,
        padding='max_length',
        truncation=True,
        max_length=max_length,
        return_tensors='pt'
    )
    
    # Run inference
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probabilities = torch.softmax(logits, dim=1)
        predicted_class = torch.argmax(logits, dim=1).item()
    
    # Get label and probability
    label = idx_to_label[predicted_class]
    probability = probabilities[0][predicted_class].item()
    
    return {
        'unified_text': unified_text,
        'predicted_label': label,
        'probability': probability,
        'probabilities': probabilities[0].tolist()
    }


# ---------------------------------------------------------------------------
# Example Usage
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Module 13: Inference Test")
    print("=" * 60)
    
    # Load the model
    print("\n[1] Loading model...")
    model, tokenizer, idx_to_label, label_map = load_model()
    print(f"Model loaded from ./saved_model/")
    print(f"Label mapping: {label_map}")
    
    # Test applicants
    test_applicants = [
        {
            'program': 'Computer Science',
            'comments': 'Strong research background with 2 publications',
            'term': 'Fall 2026',
            'degree': 'PhD',
            'us_or_international': 'International',
            'gpa': 3.9,
            'gre': 168,
            'gre_v': 160,
            'gre_aw': 4.5
        },
        {
            'program': 'Physics',
            'comments': 'Average GRE scores, no research experience',
            'term': 'Fall 2026',
            'degree': 'Masters',
            'us_or_international': 'American',
            'gpa': 3.2,
            'gre': 148,
            'gre_v': 142,
            'gre_aw': 3.0
        }
    ]
    
    print("\n[2] Making predictions...")
    print("-" * 60)
    
    for i, applicant in enumerate(test_applicants, 1):
        result = predict(applicant, model, tokenizer, idx_to_label)
        
        print(f"\nApplicant {i}:")
        print(f"  Program: {applicant.get('program', 'N/A')}")
        print(f"  GPA: {applicant.get('gpa', 'N/A')}")
        print(f"  GRE: {applicant.get('gre', 'N/A')}")
        print(f"  Prediction: {result['predicted_label']}")
        print(f"  Probability: {result['probability']:.4f}")
        print(f"  Unified text: {result['unified_text'][:100]}...")
    
    print("\n" + "=" * 60)
    print("Inference test complete!")
    print("=" * 60)