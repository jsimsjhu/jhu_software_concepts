# Module 8 – Data Cleaning and Exploratory Data Analysis

## Overview
This module performs data cleaning, feature engineering, statistical analysis, and visualization on the Grad Café applicant dataset using Pandas, NumPy, SciPy, and Matplotlib within an Amazon SageMaker Jupyter notebook.

## Prerequisites

- AWS Account with SageMaker access
- S3 bucket containing `applicant_data.json`
- IAM user `dailyWork-JS` with S3 and SageMaker permissions

## Setup

1. Launch SageMaker Notebook Instance:
   - Name: `module-8`
   - Instance type: `ml.t2.medium`
   - IAM role: Use existing role with S3 access

2. Upload `s3_fetch.py` to the notebook instance

3. Create a new Python 3 notebook named `module_8.ipynb`

4. Install required packages (if needed):
   ```bash
   !pip install pandas numpy scipy matplotlib boto3