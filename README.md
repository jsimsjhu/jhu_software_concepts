# JHU Software Concepts — Modern Software Concepts in Python

**Student:** Justen Sims  
**Course:** EN.605.256 — Modern Software Concepts in Python  
**Term:** Summer 2026  

## Repository Overview

This repository contains all coursework, projects, and assignments completed during the Summer 2026 semester of Modern Software Concepts in Python at Johns Hopkins University. The work spans web scraping, data cleaning, SQL, Flask web development, cloud computing, data visualization, machine learning, MLOps, and neural network deployment.

## Projects Portfolio

The complete portfolio of semester projects is displayed on the personal website hosted at [your-website-url] (or localhost for development). The Projects page organizes each module with:
- Project title and overview
- Link to the GitHub folder
- Personal learning statement

Visit the portfolio at: `http://127.0.0.1:5000/projects` (when running locally)

## Corrections Log

This section documents all grader feedback implemented across the semester.

| Module | Grader Comment | Revision Made |
|--------|----------------|---------------|
| Module 6 | Dockerfiles had portability issues; forced amd64 architecture | Removed architecture-specific dependencies; made Dockerfiles portable |
| Module 7 | Used Studio instead of Notebook Instance | Used proper Notebook Instance for future modules |
| Module 8 | Missing files in submission; cleaned dataset not included | Created systematic file verification before zipping |
| Module 9 | Elbow justification missing; dataset not included | Added clear justification for cluster selection; included dataset |
| Module 10 | README incomplete; debug mode left on | Completed README; set debug=False |
| Module 11 | Pylint issues; venv in submission | Fixed Pylint issues; removed venv before zipping |
| Module 12 | Column name mismatches | Corrected column names to match dataset schema |
| Module 13 | Large model file exceeded GitHub limit | Used Git LFS for model file storage |

## Repository Structure
jhu_software_concepts/
├── Module_1/ # Personal website (updated for portfolio)
├── Module_2/ # Python foundations
├── Module_3/ # SQL and database queries
├── Module_4/ # Pytest and Sphinx documentation
├── Module_5/ # Flask web application
├── Module_6/ # Docker + RabbitMQ + PostgreSQL microservices
├── Module_7/ # AWS S3 + SageMaker + EC2 deployment
├── Module_8/ # Data cleaning and EDA
├── Module_9/ # K-Means clustering
├── Module_10/ # Data dashboard with Dash + Plotly
├── Module_11/ # MLOps tracking with MLflow + wandb
├── Module_12/ # Two-layer neural network from scratch
├── Module_13/ # Multimodal admissions prediction with PyTorch
└── README.md # This file

## Reflection

**Most Challenging Module:** Module 13 — Fine-tuning a transformer model and deploying it in a Flask app required integrating many concepts from throughout the semester.

**Strongest Work:** Module 12 — Implementing a neural network from scratch in NumPy demonstrated deep understanding of gradient descent and backpropagation.

**Most Improved Skills:** Python packaging, code quality (Pylint), and submission workflow.

**Understanding of Python:** Over the semester, I progressed from writing scripts to building complete, deployable systems with proper documentation, testing, and version control.