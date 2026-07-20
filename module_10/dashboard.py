"""
Module 10 Data Dashboard: Diamond Price Analysis

This dashboard presents visualizations exploring the relationship
between diamond features and their market prices. It combines
static Seaborn plots with interactive Plotly visualizations.
"""

import os
# Enable serving static files
import dash
from dash import html, dcc
import plotly.io as pio

# Initialize the app
app = dash.Dash(__name__)

# Load saved Plotly figures
try:
    fig3d = pio.read_json('plots/diamond_3d_interactive.json')
    figbox = pio.read_json('plots/diamond_box_interactive.json')
except FileNotFoundError:
    # Fallback: Load HTML files if JSON not available
    fig3d = None
    figbox = None
    print("Warning: Could not load Plotly JSON files. Run visualization.py first.")

# Dashboard layout
app.layout = html.Div([
    # Title - states the overarching research question
    html.H1(
        "Can Diamond Price Be Determined by Its Features?",
        style={
            'textAlign': 'center',
            'color': '#2c3e50',
            'marginBottom': 20,
            'fontSize': 32
        }
    ),
    
    # Explanatory text - fewer than 4 sentences
    html.Div([
        html.P(
            "This dashboard explores how diamond characteristics—carat weight, "
            "cut quality, color grade, and clarity—influence market price. "
            "The visualizations reveal that carat weight is the strongest predictor, "
            "while cut quality and clarity also significantly impact value.",
            style={
                'textAlign': 'center',
                'fontSize': 18,
                'color': '#34495e',
                'padding': '0 50px',
                'marginBottom': 30,
                'lineHeight': 1.6
            }
        )
    ]),
    
    # Row 1: Seaborn visualizations (as images)
    html.Div([
        html.Div([
            html.H3(
                "Correlation Heatmap",
                style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': 15}
            ),
            html.Img(
                src='/assets/correlation_heatmap.png',
                style={'width': '100%', 'height': 'auto'}
            )
        ], className='six columns', style={'padding': '10px'}),
        
        html.Div([
            html.H3(
                "Price vs Carat by Clarity",
                style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': 15}
            ),
            html.Img(
                src='/assets/diamond_scatter.png',
                style={'width': '100%', 'height': 'auto'}
            )
        ], className='six columns', style={'padding': '10px'})
    ], className='row', style={'padding': '20px'}),
    
    # Row 2: Interactive Plotly 3D Scatter
    html.Div([
        html.H3(
            "3D Interactive View: Price, Carat, and Table Size",
            style={'textAlign': 'center', 'color': '#2c3e50', 'marginTop': 30}
        ),
        dcc.Graph(figure=fig3d) if fig3d else html.Div(
            "Please run visualization.py first to generate interactive plots."
        )
    ], style={'padding': '20px'}),
    
    # Row 3: Interactive Plotly Box Plot
    html.Div([
        html.H3(
            "Price Distribution by Cut and Color",
            style={'textAlign': 'center', 'color': '#2c3e50', 'marginTop': 30}
        ),
        dcc.Graph(figure=figbox) if figbox else html.Div(
            "Please run visualization.py first to generate interactive plots."
        )
    ], style={'padding': '20px'})
    
], className='container', style={'maxWidth': '1400px', 'margin': '0 auto'})

if __name__ == '__main__':
    print("=" * 60)
    print("Starting Diamond Price Dashboard")
    print("=" * 60)
    print("Open your browser to: http://127.0.0.1:8050")
    print("Press Ctrl+C to stop the server")
    print(" =" * 60)
    app.run(debug=True, port=8050)