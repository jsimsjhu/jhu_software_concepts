# Module 9 – K-Means Clustering of Grad Café Programs

This module performs K-Means clustering on Grad Café program names using scikit-learn.

## What `kmeans.py` Does

1. **Vectorizes** program names using TF-IDF
2. **Reduces dimensionality** with PCA (2D for visualization, 50D for elbow)
3. **Clusters** programs using K-Means (50 clusters initial, 85 final)
4. **Finds optimal** cluster count using the Elbow Method
5. **Analyzes** GRE scores for Computer Science and Philosophy clusters

## Files

- `kmeans.py` – Main Python script
- `requirements.txt` – Dependencies
- Visualizations: `initial_cluster.png`, `clustered_dataFrame.png`, `elbow.png`, `computer_science.png`, `philosophy.png`

## Dependencies

- pandas
- numpy
- matplotlib
- scikit-learn

## How to Run

```bash
python kmeans.py
```

## Expected Outputs

| File | Description |
|------|-------------|
| `initial_cluster.png` | Scatter plot of 50 clusters |
| `clustered_dataFrame.png` | First 100 rows with cluster labels |
| `elbow.png` | Inertia vs cluster count (optimal ~85) |
| `computer_science.png` | GRE box plot for CS cluster |
| `philosophy.png` | GRE box plot for Philosophy cluster |