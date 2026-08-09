"""
Module 13: Multimodal Admissions Prediction with PyTorch

This script fine-tunes a pretrained transformer model (DistilBERT)
on the Grad Café admissions dataset using both text and structured fields.
"""

import os
import json
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback
)
from datasets import Dataset
import matplotlib.pyplot as plt
import seaborn as sns

# Set random seed for reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
torch.manual_seed(RANDOM_SEED)

# ---------------------------------------------------------------------------
# Part 1: Load and Prepare the Dataset
# ---------------------------------------------------------------------------

def load_data(filepath):
    """Load the admissions dataset from JSON."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return pd.DataFrame(data)
    elif isinstance(data, dict) and 'results' in data:
        return pd.DataFrame(data['results'])
    else:
        raise ValueError("Unexpected JSON format. Expected list or dict with 'results' key.")


def preprocess_data(df):
    """
    Filter and prepare the dataset for modeling.
    
    - Keep only Accepted or Rejected applicants
    - Remove duplicate rows (based on URL)
    - Normalize missing values
    - Convert numeric columns to appropriate types
    - Create target column
    """
    df_clean = df.copy()
    
    # Filter by acceptance status
    status_col = 'acceptance_status' if 'acceptance_status' in df_clean.columns else 'applicant_status'
    df_clean = df_clean[df_clean[status_col].isin(['Accepted', 'Rejected'])]
    
    # Remove duplicates based on URL
    if 'result_url' in df_clean.columns:
        df_clean = df_clean.drop_duplicates(subset=['result_url'])
    
    # Create target: Accepted = 1, Rejected = 0
    df_clean['label'] = (df_clean[status_col] == 'Accepted').astype(int)
    
    # Normalize missing values for text fields to empty string
    text_fields = ['program', 'comments', 'llm_generated_program', 'llm_generated_university', 'term']
    for field in text_fields:
        if field in df_clean.columns:
            df_clean[field] = df_clean[field].fillna('').astype(str)
    
    # Normalize missing values for numeric fields to NaN
    numeric_fields = ['gpa', 'gre', 'gre_v', 'gre_aw']
    for field in numeric_fields:
        if field in df_clean.columns:
            df_clean[field] = pd.to_numeric(df_clean[field], errors='coerce')
    
    # Ensure degree and citizenship fields are strings
    if 'degree' in df_clean.columns:
        df_clean['degree'] = df_clean['degree'].fillna('Unknown').astype(str)
    if 'us_or_international' in df_clean.columns:
        df_clean['us_or_international'] = df_clean['us_or_international'].fillna('Unknown').astype(str)
    
    return df_clean


def get_metadata(df):
    """Return metadata about the dataset."""
    return {
        'original_rows': len(df),
        'filtered_rows': len(df),
        'accepted_count': df['label'].sum(),
        'rejected_count': len(df) - df['label'].sum(),
        'text_fields': ['program', 'comments', 'llm_generated_program', 'llm_generated_university', 'term'],
        'numeric_fields': ['gpa', 'gre', 'gre_v', 'gre_aw'],
        'categorical_fields': ['degree', 'us_or_international']
    }


def create_unified_text(row, metadata):
    """
    Create a single unified text input for an applicant.
    
    Combines text fields, numeric fields, and categorical fields
    into a human-readable format.
    """
    parts = []
    
    # Text fields
    if 'program' in row and row['program']:
        parts.append(f"Program: {row['program']}")
    if 'comments' in row and row['comments']:
        parts.append(f"Comments: {row['comments']}")
    if 'llm_generated_program' in row and row['llm_generated_program']:
        parts.append(f"LLM Program: {row['llm_generated_program']}")
    if 'llm_generated_university' in row and row['llm_generated_university']:
        parts.append(f"LLM University: {row['llm_generated_university']}")
    if 'term' in row and row['term']:
        parts.append(f"Term: {row['term']}")
    
    # Numeric fields
    if 'gpa' in row and pd.notna(row['gpa']):
        parts.append(f"GPA: {row['gpa']:.2f}")
    if 'gre' in row and pd.notna(row['gre']):
        parts.append(f"GRE: {row['gre']:.0f}")
    if 'gre_v' in row and pd.notna(row['gre_v']):
        parts.append(f"GRE V: {row['gre_v']:.0f}")
    if 'gre_aw' in row and pd.notna(row['gre_aw']):
        parts.append(f"GRE AW: {row['gre_aw']:.1f}")
    
    # Categorical fields
    if 'degree' in row and row['degree'] and row['degree'] != 'Unknown':
        parts.append(f"Degree: {row['degree']}")
    if 'us_or_international' in row and row['us_or_international'] and row['us_or_international'] != 'Unknown':
        parts.append(f"Citizenship: {row['us_or_international']}")
    
    # Join all parts with newlines
    return "\n".join(parts)


if __name__ == "__main__":
    print("=" * 60)
    print("Module 13: Multimodal Admissions Prediction")
    print("=" * 60)
    
    # Load data
    print("\n[1] Loading data...")
    df = load_data("applicant_data.json")
    print(f"Original rows: {len(df)}")
    
    # Preprocess
    print("\n[2] Preprocessing data...")
    df_clean = preprocess_data(df)
    metadata = get_metadata(df_clean)
    
    print(f"Rows after filtering: {metadata['filtered_rows']}")
    print(f"Accepted: {metadata['accepted_count']}")
    print(f"Rejected: {metadata['rejected_count']}")
    print(f"\nText fields: {metadata['text_fields']}")
    print(f"Numeric fields: {metadata['numeric_fields']}")
    print(f"Categorical fields: {metadata['categorical_fields']}")
    
    print("\nFirst few rows:")
    print(df_clean.head())

    print("\n[3] Creating unified text representation...")
    df_clean['unified_text'] = df_clean.apply(lambda row: create_unified_text(row, metadata), axis=1)

    # Show template and examples
    print("\nTemplate format:")
    print("Program: <value>")
    print("Comments: <value>")
    print("LLM Program: <value>")
    print("LLM University: <value>")
    print("Term: <value>")
    print("GPA: <value>")
    print("GRE: <value>")
    print("GRE V: <value>")
    print("GRE AW: <value>")
    print("Degree: <value>")
    print("Citizenship: <value>")

    print("\nThree example unified texts:")
    for i in range(min(3, len(df_clean))):
        print(f"\n--- Example {i+1} ---")
        print(df_clean.iloc[i]['unified_text'])
        print(f"Label: {'Accepted' if df_clean.iloc[i]['label'] == 1 else 'Rejected'}")

    # ---------------------------------------------------------------------------
    # Part 4: Train/Test Split and Tokenization
    # ---------------------------------------------------------------------------
    
    print("\n[4] Splitting data into train/test sets...")
    
    # Features and target
    X = df_clean['unified_text']
    y = df_clean['label']
    
    # Train/test split with stratification
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=RANDOM_SEED,
        shuffle=True,
        stratify=y
    )
    
    print(f"Training set size: {len(X_train)}")
    print(f"Test set size: {len(X_test)}")
    print(f"\nClass balance in training set:")
    print(f"  Accepted: {y_train.sum()} ({y_train.sum() / len(y_train) * 100:.1f}%)")
    print(f"  Rejected: {len(y_train) - y_train.sum()} ({(len(y_train) - y_train.sum()) / len(y_train) * 100:.1f}%)")
    print(f"\nClass balance in test set:")
    print(f"  Accepted: {y_test.sum()} ({y_test.sum() / len(y_test) * 100:.1f}%)")
    print(f"  Rejected: {len(y_test) - y_test.sum()} ({(len(y_test) - y_test.sum()) / len(y_test) * 100:.1f}%)")

    # Reduce dataset size for faster training
    # Use 10% of the training data (about 1,650 samples)
    train_subset_size = int(0.1 * len(X_train))
    X_train = X_train.sample(n=train_subset_size, random_state=RANDOM_SEED)
    y_train = y_train.loc[X_train.index]
    
    print(f"Using subset of training data: {len(X_train)} samples")
    print(f"Accepted in subset: {y_train.sum()}")
    print(f"Rejected in subset: {len(y_train) - y_train.sum()}")

    print("\nWhy train/test separation matters:")
    print("  Train/test separation prevents data leakage, ensuring the model")
    print("  is evaluated on unseen data. This gives a realistic estimate of")
    print("  how the model will perform on new applicants in the deployed system.")
    
    # ---------------------------------------------------------------------------
    # Part 5: Tokenization
    # ---------------------------------------------------------------------------
    
    print("\n[5] Tokenizing the unified text...")
    
    # Use DistilBERT tokenizer
    MODEL_NAME = "distilbert-base-uncased"
    MAX_LENGTH = 256
    
    print(f"Model: {MODEL_NAME}")
    print(f"Max sequence length: {MAX_LENGTH}")
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    
    print(f"Tokenizer: {tokenizer.__class__.__name__}")
    print(f"Vocabulary size: {tokenizer.vocab_size}")
    print(f"Model max length: {tokenizer.model_max_length}")
    
    print("\nTokenizer choice explanation:")
    print("  DistilBERT is a smaller, faster version of BERT that retains most")
    print("  of its performance. It is well-suited for this task because:")
    print("  1. It handles text inputs up to 512 tokens (we use 256)")
    print("  2. It is pretrained on a large corpus of English text")
    print("  3. It can be fine-tuned for classification tasks")
    print("  4. It is practical to train on ordinary hardware")
    
    def tokenize_function(texts):
        return tokenizer(
            texts.tolist(),
            padding='max_length',
            truncation=True,
            max_length=MAX_LENGTH,
            return_tensors=None
        )
    
    # Tokenize training and test sets
    train_encodings = tokenize_function(X_train)
    test_encodings = tokenize_function(X_test)
    
    print(f"\nTraining encodings shape: {len(train_encodings['input_ids'])} x {len(train_encodings['input_ids'][0])}")
    print(f"Test encodings shape: {len(test_encodings['input_ids'])} x {len(test_encodings['input_ids'][0])}")
    
    # Convert to PyTorch datasets
    train_dataset = Dataset.from_dict({
        'input_ids': train_encodings['input_ids'],
        'attention_mask': train_encodings['attention_mask'],
        'labels': y_train.tolist()
    })
    
    test_dataset = Dataset.from_dict({
        'input_ids': test_encodings['input_ids'],
        'attention_mask': test_encodings['attention_mask'],
        'labels': y_test.tolist()
    })
    
    print(f"\nTraining dataset size: {len(train_dataset)}")
    print(f"Test dataset size: {len(test_dataset)}")

    # ---------------------------------------------------------------------------
    # Part 6: Model Fine-Tuning
    # ---------------------------------------------------------------------------
    
    print("\n[6] Loading pretrained model for fine-tuning...")
    
    # Model configuration
    MODEL_NAME = "distilbert-base-uncased"
    NUM_LABELS = 2
    BATCH_SIZE = 32
    EPOCHS = 2
    LEARNING_RATE = 2e-5
    WEIGHT_DECAY = 0.01
    WARMUP_STEPS = 100
    
    print(f"Model: {MODEL_NAME}")
    print(f"Number of labels: {NUM_LABELS}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Epochs: {EPOCHS}")
    print(f"Learning rate: {LEARNING_RATE}")
    print(f"Weight decay: {WEIGHT_DECAY}")
    print(f"Warmup steps: {WARMUP_STEPS}")
    print(f"Device: {'cuda' if torch.cuda.is_available() else 'cpu'}")
    
    # Load the model
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=NUM_LABELS
    )
    
    # Move to device if GPU available
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    print(f"Model moved to: {device}")
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir="./results",
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=LEARNING_RATE,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        num_train_epochs=EPOCHS,
        weight_decay=WEIGHT_DECAY,
        warmup_steps=WARMUP_STEPS,
        logging_dir="./logs",
        logging_steps=50,
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        report_to="none",  # Disable wandb/other logging
    )
    
    print("\nTraining arguments:")
    print(f"  Output directory: {training_args.output_dir}")
    print(f"  Evaluation strategy: {training_args.eval_strategy}")
    print(f"  Save strategy: {training_args.save_strategy}")
    print(f"  Logging steps: {training_args.logging_steps}")
    print(f"  Load best model at end: {training_args.load_best_model_at_end}")
    
    # Define compute_metrics function
    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=-1)
        accuracy = accuracy_score(labels, predictions)
        precision = precision_score(labels, predictions, average='binary', zero_division=0)
        recall = recall_score(labels, predictions, average='binary', zero_division=0)
        f1 = f1_score(labels, predictions, average='binary', zero_division=0)
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1
        }
    
    # Create Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        compute_metrics=compute_metrics,
    )
    
    print("\n[7] Starting training...")
    print("=" * 60)
    
    # Train the model
    trainer.train()
    
    print("\n[8] Evaluating on test set...")
    eval_results = trainer.evaluate()
    print(f"Test Accuracy: {eval_results['eval_accuracy']:.4f}")
    print(f"Test Precision: {eval_results['eval_precision']:.4f}")
    print(f"Test Recall: {eval_results['eval_recall']:.4f}")
    print(f"Test F1: {eval_results['eval_f1']:.4f}")
    
    # Get predictions for confusion matrix
    predictions = trainer.predict(test_dataset)
    pred_labels = np.argmax(predictions.predictions, axis=-1)
    
    # Confusion matrix
    cm = confusion_matrix(y_test, pred_labels)
    print("\nConfusion Matrix:")
    print(cm)
    print("  (Rows: True labels, Columns: Predicted labels)")
    
    # ---------------------------------------------------------------------------
    # Part 9: Save the Model
    # ---------------------------------------------------------------------------
    
    print("\n[9] Saving the fine-tuned model...")
    
    # Create saved_model directory
    os.makedirs("./saved_model", exist_ok=True)
    
    # Save model
    model.save_pretrained("./saved_model")
    tokenizer.save_pretrained("./saved_model")
    
    # Save label mapping
    label_map = {'Accepted': 1, 'Rejected': 0}
    import json
    with open("./saved_model/label_map.json", 'w') as f:
        json.dump(label_map, f)
    
    print("Model saved to ./saved_model/")
    print("  - model files")
    print("  - tokenizer files")
    print("  - label_map.json")
    
    print("\n" + "=" * 60)
    print("Training complete!")
    print("=" * 60)