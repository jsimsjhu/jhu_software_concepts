# Module 13: Multimodal Admissions Prediction

## Overview

This project fine-tunes a pretrained DistilBERT model to predict graduate admissions outcomes using both text and structured applicant data. The model is deployed as a Flask web application called "Will You Get In?"

## Files

| File | Description |
|------|-------------|
| `train_model.py` | Fine-tunes the DistilBERT model on admissions data |
| `inference.py` | Loads the saved model and makes predictions |
| `run.py` | Flask web app with the prediction form |
| `templates/` | HTML templates for the web pages |
| `saved_model/` | Trained model, tokenizer, and label mapping |
| `requirements.txt` | Python dependencies |
| `README.md` | This file |
| `writeup.pdf` | Full report with results and reflection |

## How to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Train the model (optional — model is already saved)

```bash
python train_model.py
```

### 3. Run inference test

```bash
python inference.py
```

### 4. Start the Flask app

```bash
python run.py
```

### 5. Open in browser

```
http://127.0.0.1:8080
```

## Model Architecture

- Base model: DistilBERT-base-uncased
- Task: Binary classification (Accepted/Rejected)
- Input: Unified text combining program, comments, GPA, GRE, degree, citizenship
- Max sequence length: 256
- Batch size: 32
- Epochs: 2
- Learning rate: 2e-5

## Results

| Metric | Value |
|--------|-------|
| Test Accuracy | 61.96% |
| Test Precision | 61.69% |
| Test Recall | 68.49% |
| Test F1 | 64.91% |

## Disclaimer

This is a course project model trained on scraped self-reported GradCafe data. It is not a real admissions decision tool.

## Author

Justen Sims
JHU Software Concepts

