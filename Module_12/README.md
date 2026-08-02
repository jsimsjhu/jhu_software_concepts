# Module 12: Two-Layer Neural Network for Graduate Admissions Prediction

## Overview

This project implements a two-layer neural network from scratch using NumPy to predict graduate admissions outcomes based on applicant features.

## Files

| File | Description |
|------|-------------|
| `neural_network.py` | Main script implementing the neural network |
| `training.log` | Complete training output log |
| `mse_curve.png` | Plot of training and test MSE over time |
| `writeup.pdf` | Written analysis and reflection |
| `README.md` | This file |

## Features

The model uses six input features:
- GPA
- GRE Quant
- GRE Verbal
- GRE AW
- PhD vs Masters (binary)
- International vs Local (binary)

## Network Architecture

- Input layer: 6 features
- Hidden layer: 6 units (sigmoid activation)
- Output layer: 1 unit (sigmoid activation)
- Loss function: Mean Squared Error (MSE)
- Training: Full-batch gradient descent

## How to Run

### 1. Install dependencies

```bash
pip install numpy pandas matplotlib scikit-learn

### 2. Run the Script
bash
python neural_network.py
### 3. View outputs
Training progress is printed to the console

MSE curve is saved as mse_curve.png

Full training log is saved in training.log

Results
Metric	Value
Best test MSE	0.2478
Final training accuracy	55.1%
Final test accuracy	54.1%
Requirements
Python 3.10+

NumPy

Pandas

Matplotlib

scikit-learn

Author
Justen Sims
JHU Software Concepts