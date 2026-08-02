"""
Module 12: Two-Layer Neural Network for Graduate Admissions Prediction

This script implements a two-layer neural network from scratch using NumPy.
It predicts whether a graduate applicant will be accepted or rejected based on
GPA, GRE scores, degree type, and citizenship status.

Features:
- 6 input features: gpa, gre_quant, gre_verbal, gre_aw, ms_vs_phd, international_vs_local
- 6 hidden units
- 1 output unit
- Sigmoid activation
- MSE loss
- Early stopping with patience = 100
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split

# Set random seed for reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# ---------------------------------------------------------------------------
# Activation and Loss Functions
# ---------------------------------------------------------------------------

def sigmoid(x):
    """Sigmoid activation function with clipping for numerical stability."""
    x = np.clip(x, -50, 50)
    return 1.0 / (1.0 + np.exp(-x))


def mse(y_true, y_pred):
    """Mean Squared Error loss function."""
    return np.mean((y_true - y_pred) ** 2)


# ---------------------------------------------------------------------------
# Two-Layer Neural Network Class
# ---------------------------------------------------------------------------

class TwoLayerNet:
    """
    Rudimentary 2-layer neural net:
    input -> hidden(sigmoid) -> output(sigmoid)
    """

    def __init__(self, input_dim, hidden_dim, seed=42):
        """
        Args:
            input_dim: int, number of input features
            hidden_dim: int, number of hidden units
            seed: int, random seed for reproducibility
        """
        np.random.seed(seed)
        # Initialize weights with normal distribution (mean=0, std=0.1)
        self.W1 = np.random.randn(input_dim, hidden_dim) * 0.1
        self.b1 = np.zeros((1, hidden_dim))
        self.W2 = np.random.randn(hidden_dim, 1) * 0.1
        self.b2 = np.zeros((1, 1))

        # Store dimensions for reference
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim

    def forward(self, X):
        """
        Forward pass through the network.

        Args:
            X: np.array, input data of shape (n_samples, input_dim)

        Returns:
            y_hat: np.array, predictions of shape (n_samples, 1)
        """
        self.z1 = X @ self.W1 + self.b1           # (n_samples, hidden_dim)
        self.a1 = sigmoid(self.z1)                # (n_samples, hidden_dim)
        self.z2 = self.a1 @ self.W2 + self.b2     # (n_samples, 1)
        self.y_hat = sigmoid(self.z2)             # (n_samples, 1)
        return self.y_hat

    def backward(self, X, y, learning_rate):
        """
        Backward pass: compute gradients and update weights and biases.

        Args:
            X: np.array, input data of shape (n_samples, input_dim)
            y: np.array, target values of shape (n_samples, 1)
            learning_rate: float, step size for gradient descent
        """
        n_samples = X.shape[0]

        # MSE derivative through sigmoid output
        # dL/dz2 = (y_hat - y) * sigmoid'(z2) = (y_hat - y) * y_hat * (1 - y_hat)
        dZ2 = (self.y_hat - y) * self.y_hat * (1 - self.y_hat)  # (n_samples, 1)

        # Gradients for W2 and b2
        dW2 = self.a1.T @ dZ2 / n_samples           # (hidden_dim, 1)
        db2 = dZ2.sum(axis=0, keepdims=True) / n_samples  # (1, 1)

        # Backpropagate to hidden layer
        da1 = dZ2 @ self.W2.T                       # (n_samples, hidden_dim)
        dz1 = da1 * self.a1 * (1 - self.a1)         # (n_samples, hidden_dim)

        # Gradients for W1 and b1
        dW1 = X.T @ dz1 / n_samples                 # (input_dim, hidden_dim)
        db1 = dz1.sum(axis=0, keepdims=True) / n_samples  # (1, hidden_dim)

        # Update weights and biases using gradient descent
        self.W2 -= learning_rate * dW2
        self.b2 -= learning_rate * db2
        self.W1 -= learning_rate * dW1
        self.b1 -= learning_rate * db1

    def predict_proba(self, X):
        """
        Predict probabilities for input data.

        Args:
            X: np.array, input data of shape (n_samples, input_dim)

        Returns:
            np.array: predicted probabilities of shape (n_samples, 1)
        """
        return self.forward(X)

    def predict(self, X, threshold=0.5):
        """
        Predict binary labels for input data.

        Args:
            X: np.array, input data of shape (n_samples, input_dim)
            threshold: float, classification threshold

        Returns:
            np.array: predicted labels of shape (n_samples, 1)
        """
        return (self.predict_proba(X) >= threshold).astype(int)


# ---------------------------------------------------------------------------
# Data Loading and Preprocessing
# ---------------------------------------------------------------------------

def load_data(filepath):
    """Load JSON data into a pandas DataFrame."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Check if data is a list or has a 'results' key
    if isinstance(data, list):
        return pd.DataFrame(data)
    elif isinstance(data, dict) and 'results' in data:
        return pd.DataFrame(data['results'])
    else:
        raise ValueError("Unexpected JSON format. Expected list or dict with 'results' key.")


def preprocess_data(df):
    """
    Preprocess the raw dataset for binary classification.

    Filters:
    - Keep only Accepted or Rejected applicants
    - Keep only Masters or PhD applicants

    Feature engineering:
    - Convert gpa, gre_quant, gre_verbal, gre_aw to float
    - Create ms_vs_phd: PhD=1, Masters=0
    - Create international_vs_local: International=1, Local=0
    - Create target: Accepted=1, Rejected=0

    Returns:
        X: DataFrame with 6 features
        y: Series with target values
        metadata: dict with counts and info
    """
    df_clean = df.copy()

    # Filter acceptance_status
    df_clean = df_clean[df_clean['acceptance_status'].isin(['Accepted', 'Rejected'])]

    # Filter degree
    df_clean = df_clean[df_clean['degree'].isin(['Masters', 'PhD'])]

    # Convert numeric columns to float
    numeric_cols = ['gpa', 'gre_quant', 'gre_verbal', 'gre_aw']
    for col in numeric_cols:
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

    # Create binary features
    df_clean['ms_vs_phd'] = (df_clean['degree'] == 'PhD').astype(int)
    df_clean['international_vs_local'] = (df_clean['applicant_type'] == 'International').astype(int)

    # Create target
    df_clean['target'] = (df_clean['acceptance_status'] == 'Accepted').astype(int)

    # Select final features
    features = ['gpa', 'gre_quant', 'gre_verbal', 'gre_aw', 'ms_vs_phd', 'international_vs_local']
    X = df_clean[features].copy()
    y = df_clean['target'].copy()

    metadata = {
        'filtered_rows': len(df_clean),
        'accepted_count': df_clean['target'].sum(),
        'rejected_count': len(df_clean) - df_clean['target'].sum(),
        'features': features
    }

    return X, y, metadata


def preprocess_features(X_train, X_test):
    """
    Preprocess features using training set statistics.
    - Fill missing values with training medians
    - Standardize using training means and stds
    """
    # Compute medians from training set
    medians = X_train.median()

    # Fill missing values with medians
    X_train_filled = X_train.fillna(medians)
    X_test_filled = X_test.fillna(medians)

    # Compute means and stds from training set
    means = X_train_filled.mean()
    stds = X_train_filled.std()

    # Replace zero std with 1
    stds = stds.replace(0, 1)

    # Standardize
    X_train_scaled = (X_train_filled - means) / stds
    X_test_scaled = (X_test_filled - means) / stds

    stats = {
        'medians': medians,
        'means': means,
        'stds': stds
    }

    return X_train_scaled, X_test_scaled, stats


# ---------------------------------------------------------------------------
# Training Function
# ---------------------------------------------------------------------------

def train_model(X_train, y_train, X_test, y_test, hidden_units=6,
                learning_rate=0.05, max_epochs=10000, patience=100):
    """
    Train the two-layer neural network with early stopping.
    """
    # Convert to numpy arrays and reshape y
    X_train_np = X_train.values
    y_train_np = y_train.values.reshape(-1, 1)
    X_test_np = X_test.values
    y_test_np = y_test.values.reshape(-1, 1)

    # Initialize network
    input_dim = X_train_np.shape[1]
    net = TwoLayerNet(input_dim, hidden_units, seed=RANDOM_SEED)

    # History storage
    history = {
        'epoch': [],
        'train_mse': [],
        'test_mse': [],
        'test_accuracy': []
    }

    # Early stopping variables
    best_test_mse = float('inf')
    best_params = None
    patience_counter = 0

    for epoch in range(max_epochs):
        # Forward pass
        y_train_pred = net.forward(X_train_np)
        train_mse = mse(y_train_np, y_train_pred)

        # Backward pass
        net.backward(X_train_np, y_train_np, learning_rate)

        # Test set evaluation
        y_test_pred = net.forward(X_test_np)
        test_mse = mse(y_test_np, y_test_pred)
        test_accuracy = np.mean((y_test_pred >= 0.5).astype(int) == y_test_np)

        # Store history
        history['epoch'].append(epoch)
        history['train_mse'].append(train_mse)
        history['test_mse'].append(test_mse)
        history['test_accuracy'].append(test_accuracy)

        # Print progress every 100 epochs
        if epoch % 100 == 0:
            print(f"Epoch {epoch:5d} | Train MSE: {train_mse:.6f} | "
                  f"Test MSE: {test_mse:.6f} | Test Acc: {test_accuracy:.4f}")

        # Early stopping check
        if test_mse < best_test_mse:
            best_test_mse = test_mse
            best_params = (net.W1.copy(), net.b1.copy(), net.W2.copy(), net.b2.copy())
            patience_counter = 0
        else:
            patience_counter += 1

        if patience_counter >= patience:
            print(f"\nEarly stopping at epoch {epoch} (no improvement for {patience} epochs)")
            break

    # Restore best parameters
    if best_params is not None:
        net.W1, net.b1, net.W2, net.b2 = best_params
        best_epoch = history['epoch'][np.argmin(history['test_mse'])]
        print(f"\nBest test MSE: {best_test_mse:.6f} at epoch {best_epoch}")
    else:
        best_epoch = len(history['epoch']) - 1

    return net, history, best_epoch, best_test_mse


# ---------------------------------------------------------------------------
# Main Execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Module 12: Two-Layer Neural Network for Graduate Admissions")
    print("=" * 60)

    # 1. Load and preprocess data
    print("\n[1] Loading and preprocessing data...")
    df = load_data("applicant_data.json")
    print(f"Original rows: {len(df)}")

    X, y, metadata = preprocess_data(df)

    print(f"Rows after filtering: {metadata['filtered_rows']}")
    print(f"Accepted: {metadata['accepted_count']}")
    print(f"Rejected: {metadata['rejected_count']}")
    print(f"Features: {metadata['features']}")
    print("\nFirst few rows of cleaned data:")
    print(X.head())

    # 2. Train/Test split
    print("\n[2] Splitting data...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED, shuffle=True
    )
    print(f"Training set size: {len(X_train)}")
    print(f"Test set size: {len(X_test)}")

    # 3. Preprocess features
    print("\n[3] Preprocessing features...")
    X_train_scaled, X_test_scaled, stats = preprocess_features(X_train, X_test)
    print("Training-set medians:")
    print(stats['medians'])
    print("\nTraining-set means:")
    print(stats['means'])
    print("\nTraining-set standard deviations:")
    print(stats['stds'])
    print("\nWhy medians, means, and stds must be computed from training set only:")
    print("  To avoid data leakage — test set information must not influence training.")

    # 4. Train the model
    print("\n[4] Training the neural network...")
    net, history, best_epoch, best_test_mse = train_model(
        X_train_scaled, y_train, X_test_scaled, y_test,
        hidden_units=6, learning_rate=0.05, max_epochs=10000, patience=100
    )

    # 5. Final evaluation
    print("\n[5] Final evaluation...")
    X_train_np = X_train_scaled.values
    y_train_np = y_train.values.reshape(-1, 1)
    X_test_np = X_test_scaled.values
    y_test_np = y_test.values.reshape(-1, 1)

    y_train_pred = net.predict(X_train_np)
    y_test_pred = net.predict(X_test_np)

    train_accuracy = np.mean(y_train_pred == y_train_np)
    test_accuracy = np.mean(y_test_pred == y_test_np)

    print(f"Best epoch: {best_epoch}")
    print(f"Best test MSE: {best_test_mse:.6f}")
    print(f"Final training accuracy: {train_accuracy:.4f}")
    print(f"Final test accuracy: {test_accuracy:.4f}")
    print(f"Rows after filtering: {metadata['filtered_rows']}")
    print(f"Train/Test split: {len(X_train)} / {len(X_test)}")

    # Discuss overfitting
    print("\n[6] Overfitting discussion:")
    if train_accuracy > test_accuracy + 0.05:
        print("  The model appears to overfit (training accuracy > test accuracy + 0.05).")
    elif test_accuracy > 0.7:
        print("  The model appears reasonably strong.")
    else:
        print("  The model appears weak or unstable.")

    # 7. Plot MSE curve
    print("\n[7] Generating MSE curve...")
    plt.figure(figsize=(10, 6))
    plt.plot(history['epoch'], history['train_mse'], label='Training MSE', linewidth=2)
    plt.plot(history['epoch'], history['test_mse'], label='Test MSE', linewidth=2)
    plt.xlabel('Epoch')
    plt.ylabel('Mean Squared Error')
    plt.title('Training and Test MSE Over Time')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('mse_curve.png', dpi=300, bbox_inches='tight')
    print("Saved mse_curve.png")
    plt.close()

    # 8. Artificial applicants
    print("\n[8] Artificial applicant predictions...")
    artificial_applicants = pd.DataFrame([
        {
            'gpa': 3.9,
            'gre_quant': 165,
            'gre_verbal': 160,
            'gre_aw': 5.0,
            'ms_vs_phd': 1,  # PhD
            'international_vs_local': 0  # Local
        },
        {
            'gpa': 3.2,
            'gre_quant': 145,
            'gre_verbal': 140,
            'gre_aw': 3.0,
            'ms_vs_phd': 0,  # Masters
            'international_vs_local': 1  # International
        }
    ])
    print("Artificial applicants:")
    print(artificial_applicants)

    # Preprocess artificial applicants
    X_art = artificial_applicants.copy()
    X_art_filled = X_art.fillna(stats['medians'])
    X_art_scaled = (X_art_filled - stats['means']) / stats['stds']

    # Make predictions
    X_art_np = X_art_scaled.values
    art_probs = net.predict_proba(X_art_np)
    art_preds = (art_probs >= 0.5).astype(int)

    print("\nPredictions:")
    for i, (prob, pred) in enumerate(zip(art_probs, art_preds)):
        status = "Accepted" if pred[0] == 1 else "Rejected"
        print(f"  Applicant {i+1}: Probability = {prob[0]:.4f}, Predicted = {status}")

    print("\n" + "=" * 60)
    print("Training complete!")
    print("=" * 60)