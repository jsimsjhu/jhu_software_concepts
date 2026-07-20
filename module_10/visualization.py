"""
Module 10: Data Visualization for Diamond Price Analysis

This module generates three informative visualizations exploring the relationship
between diamond features and their market prices. It uses Seaborn for static
plots and Plotly for interactive visualizations.
"""

import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
from plotly.io import write_html

# Create necessary directories
os.makedirs('plots', exist_ok=True)
os.makedirs('data', exist_ok=True)

def load_and_clean_data():
    """
    Load the diamonds dataset and perform data cleaning.
    Removes outliers and validates data ranges.

    Returns:
        pd.DataFrame: Cleaned diamonds dataset
    """
    # Load dataset (automatically downloads if needed)
    try:
        df = sns.load_dataset('diamonds')
    except FileNotFoundError:
        # Fallback: try to load from data folder
        df = pd.read_csv('data/diamonds.csv')

    # Initial data quality checks
    print(f"Initial data shape: {df.shape}")
    print(f"Missing values: {df.isnull().sum().sum()}")

    # Remove obvious outliers
    # Diamond prices > $20,000 are rare and can skew visualizations
    # Carat > 3.0 is extremely rare
    df_clean = df[
        (df['price'] <= 20000) &
        (df['carat'] <= 3.0) &
        (df['x'] > 0) & (df['y'] > 0) & (df['z'] > 0)  # Valid dimensions
    ].copy()

    print(f"Cleaned data shape: {df_clean.shape}")
    print(f"Price range: ${df_clean['price'].min():,.0f} - ${df_clean['price'].max():,.0f}")

    return df_clean

def create_seaborn_correlation_heatmap(df):
    """
    Create a Seaborn correlation heatmap showing relationships
    between all numeric diamond features.

    Args:
        df (pd.DataFrame): Cleaned diamonds dataset
    """
    plt.figure(figsize=(10, 8))

    # Select numeric columns for correlation
    numeric_cols = ['carat', 'depth', 'table', 'price', 'x', 'y', 'z']
    corr_matrix = df[numeric_cols].corr()

    # Create heatmap with consistent color palette
    sns.heatmap(
        corr_matrix,
        annot=True,
        cmap='coolwarm',  # Consistent color palette
        fmt='.2f',
        square=True,
        linewidths=0.5,
        cbar_kws={'label': 'Correlation Coefficient'}
    )

    plt.title('Correlation Between Diamond Features and Price', fontsize=14, pad=20)
    plt.tight_layout()
    plt.savefig('plots/correlation_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Saved: correlation_heatmap.png")

def create_seaborn_scatter_plot(df):
    """
    Create a Seaborn scatter plot showing how carat and clarity
    affect diamond price, with a regression line.

    Args:
        df (pd.DataFrame): Cleaned diamonds dataset
    """
    plt.figure(figsize=(12, 8))

    # Sample 1000 points for readability (keep all for regression)
    sample = df.sample(n=1000, random_state=42)

    # Create scatter plot with color by clarity
    sns.scatterplot(
        data=sample,
        x='carat',
        y='price',
        hue='clarity',
        palette='viridis',  # Consistent color palette
        alpha=0.6,
        size='depth',  # Show third variable
        sizes=(20, 100),
        legend='full'
    )

    # Add regression line
    sns.regplot(
        data=df,
        x='carat',
        y='price',
        scatter=False,
        color='red',
        line_kws={'linestyle': '--', 'alpha': 0.7}
    )

    plt.title('Diamond Price vs Carat Weight by Clarity Grade', fontsize=14, pad=20)
    plt.xlabel('Carat Weight (carats)')
    plt.ylabel('Price (USD)')
    plt.legend(title='Clarity', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('plots/diamond_scatter.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Saved: diamond_scatter.png")

def create_plotly_3d_scatter(df):
    """
    Create an interactive 3D Plotly visualization showing
    diamond price, carat, and table size by cut quality.

    Args:
        df (pd.DataFrame): Cleaned diamonds dataset
    """
    # Sample for performance
    sample = df.sample(n=500, random_state=42)

    # Create 3D scatter plot
    fig = px.scatter_3d(
        sample,
        x='carat',
        y='price',
        z='table',
        color='cut',
        size='depth',
        hover_data=['clarity', 'color'],
        title='3D Interactive: Diamond Price, Carat, and Table Size by Cut Quality',
        labels={
            'carat': 'Carat Weight (carats)',
            'price': 'Price (USD)',
            'table': 'Table Size (%)',
            'cut': 'Cut Quality'
        },
        color_discrete_sequence=px.colors.qualitative.Set2  # Consistent palette
    )

    # Update layout for better appearance
    fig.update_layout(
        scene={
            'xaxis_title': 'Carat Weight (carats)',
            'yaxis_title': 'Price (USD)',
            'zaxis_title': 'Table Size (%)'
        },
        width=1200,
        height=800,
        title_font_size=16
    )

    # Save as HTML for interactivity
    write_html(fig, 'plots/diamond_3d_interactive.html')
    print("✓ Saved: diamond_3d_interactive.html")

    # Also save as JSON for dashboard loading
    fig.write_json('plots/diamond_3d_interactive.json')
    print("✓ Saved: diamond_3d_interactive.json")

def create_plotly_box_plot(df):
    """
    Create an interactive Plotly box plot showing price distribution
    across different cut qualities and colors.

    Args:
        df (pd.DataFrame): Cleaned diamonds dataset
    """
    fig = px.box(
        df,
        x='cut',
        y='price',
        color='color',
        title='Diamond Price Distribution by Cut Quality and Color Grade',
        labels={
            'cut': 'Cut Quality',
            'price': 'Price (USD)',
            'color': 'Color Grade'
        },
        color_discrete_sequence=px.colors.qualitative.Set3  # Consistent palette
    )

    fig.update_layout(
        width=1000,
        height=600,
        boxmode='group',
        title_font_size=16
    )

    # Save as HTML for interactivity
    write_html(fig, 'plots/diamond_box_interactive.html')
    print("✓ Saved: diamond_box_interactive.html")

    # Also save as JSON for dashboard loading
    fig.write_json('plots/diamond_box_interactive.json')
    print("✓ Saved: diamond_box_interactive.json")

def main():
    """
    Main execution function that coordinates all visualization creation.
    """
    print("=" * 60)
    print("Module 10 Visualization Generator")
    print("=" * 60)

    # Load and clean data
    print("\nLoading and cleaning data...")
    df = load_and_clean_data()
    print(f"Working with {len(df):,} diamonds")

    # Generate visualizations
    print("\nGenerating Seaborn visualizations...")
    create_seaborn_correlation_heatmap(df)
    create_seaborn_scatter_plot(df)

    print("\nGenerating Plotly visualizations...")
    create_plotly_3d_scatter(df)
    create_plotly_box_plot(df)

    print("\n" + "=" * 60)
    print("✅ All visualizations generated successfully!")
    print("Check the 'plots' folder for output files.")
    print("=" * 60)

if __name__ == "__main__":
    main()
