import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.neural_network import MLPRegressor
import warnings
warnings.filterwarnings('ignore')

class ImprovedQueueNeuralNetwork:
    """
    Improved Neural Network for predicting Wq from lambda and Lq
    Learns the actual relationship in the data without assuming Little's Law
    """
    
    def __init__(self, hidden_layers=(256, 128, 64), learning_rate=0.001, max_iter=1000):
        self.hidden_layers = hidden_layers
        self.learning_rate = learning_rate
        self.max_iter = max_iter
        self.model = None
        self.scaler_X = MinMaxScaler()  # Use MinMaxScaler for better performance
        self.scaler_y = MinMaxScaler()
        
    def build_model(self):
        """Build the neural network using MLPRegressor"""
        self.model = MLPRegressor(
            hidden_layer_sizes=self.hidden_layers,
            learning_rate_init=self.learning_rate,
            max_iter=self.max_iter,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.2,
            n_iter_no_change=50,
            verbose=True,
            alpha=0.001,  # L2 regularization
            activation='relu'
        )
        return self.model
    
    def prepare_data(self, X, y):
        """Prepare and scale the data"""
        # Scale features to [0, 1] range
        X_scaled = self.scaler_X.fit_transform(X)
        
        # Scale target to [0, 1] range
        y_scaled = self.scaler_y.fit_transform(y.reshape(-1, 1)).flatten()
        
        return X_scaled, y_scaled
    
    def train(self, X, y, validation_split=0.2, verbose=True):
        """Train the neural network"""
        if self.model is None:
            self.build_model()
        
        # Prepare data
        X_scaled, y_scaled = self.prepare_data(X, y)
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X_scaled, y_scaled, test_size=validation_split, random_state=42
        )
        
        if verbose:
            print(f"Training with {len(X_train)} samples, validating with {len(X_val)} samples")
            print(f"Input features range: X_min={X.min(axis=0)}, X_max={X.max(axis=0)}")
            print(f"Target range: y_min={y.min():.4f}, y_max={y.max():.4f}")
        
        # Train the model
        self.model.fit(X_train, y_train)
        
        # Calculate training metrics
        y_train_pred = self.model.predict(X_train)
        y_val_pred = self.model.predict(X_val)
        
        # Convert back to original scale for metrics
        y_train_orig = self.scaler_y.inverse_transform(y_train_pred.reshape(-1, 1)).flatten()
        y_val_orig = self.scaler_y.inverse_transform(y_val_pred.reshape(-1, 1)).flatten()
        y_train_true = self.scaler_y.inverse_transform(y_train.reshape(-1, 1)).flatten()
        y_val_true = self.scaler_y.inverse_transform(y_val.reshape(-1, 1)).flatten()
        
        train_mse = mean_squared_error(y_train_true, y_train_orig)
        val_mse = mean_squared_error(y_val_true, y_val_orig)
        train_mae = mean_absolute_error(y_train_true, y_train_orig)
        val_mae = mean_absolute_error(y_val_true, y_val_orig)
        train_rmse = np.sqrt(train_mse)
        val_rmse = np.sqrt(val_mse)
        
        if verbose:
            print(f"Training MSE: {train_mse:.6f}")
            print(f"Validation MSE: {val_mse:.6f}")
            print(f"Training MAE: {train_mae:.6f}")
            print(f"Validation MAE: {val_mae:.6f}")
            print(f"Training RMSE: {train_rmse:.6f}")
            print(f"Validation RMSE: {val_rmse:.6f}")
            print(f"Training completed in {self.model.n_iter_} iterations")
        
        return {
            'train_mse': train_mse,
            'val_mse': val_mse,
            'train_mae': train_mae,
            'val_mae': val_mae,
            'train_rmse': train_rmse,
            'val_rmse': val_rmse,
            'n_iterations': self.model.n_iter_
        }
    
    def predict(self, X):
        """Make predictions"""
        if self.model is None:
            raise ValueError("Model not trained yet. Call train() first.")
        
        X_scaled = self.scaler_X.transform(X)
        y_pred_scaled = self.model.predict(X_scaled)
        y_pred = self.scaler_y.inverse_transform(y_pred_scaled.reshape(-1, 1))
        
        return y_pred.flatten()
    
    def evaluate(self, X, y_true):
        """Evaluate model performance"""
        y_pred = self.predict(X)
        
        mse = mean_squared_error(y_true, y_pred)
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        
        return {
            'MSE': mse,
            'MAE': mae,
            'RMSE': rmse
        }
    
    def plot_predictions(self, X, y_true, sample_size=1000):
        """Plot actual vs predicted values"""
        if len(X) > sample_size:
            indices = np.random.choice(len(X), sample_size, replace=False)
            X_sample = X[indices]
            y_true_sample = y_true[indices]
        else:
            X_sample = X
            y_true_sample = y_true
        
        y_pred = self.predict(X_sample)
        
        plt.figure(figsize=(10, 6))
        plt.scatter(y_true_sample, y_pred, alpha=0.5)
        plt.plot([y_true_sample.min(), y_true_sample.max()], 
                [y_true_sample.min(), y_true_sample.max()], 'r--', lw=2)
        plt.xlabel('Actual Wq')
        plt.ylabel('Predicted Wq')
        plt.title('Actual vs Predicted Wq Values')
        plt.grid(True)
        plt.show()
        
        # Print correlation
        correlation = np.corrcoef(y_true_sample, y_pred)[0, 1]
        print(f"Correlation between actual and predicted: {correlation:.4f}")
    
    def save_model(self, filename='improved_queue_nn_model.pkl'):
        """Save the trained model"""
        import pickle
        model_data = {
            'model': self.model,
            'scaler_X': self.scaler_X,
            'scaler_y': self.scaler_y
        }
        with open(filename, 'wb') as f:
            pickle.dump(model_data, f)
        print(f"Model saved to {filename}")
    
    def load_model(self, filename='improved_queue_nn_model.pkl'):
        """Load a trained model"""
        import pickle
        with open(filename, 'rb') as f:
            model_data = pickle.load(f)
        self.model = model_data['model']
        self.scaler_X = model_data['scaler_X']
        self.scaler_y = model_data['scaler_y']
        print(f"Model loaded from '{filename}'")

def train_improved_model():
    """Train the improved neural network"""
    
    # Load data
    df = pd.read_csv('dataset.csv')
    
    # Extract columns
    lambda_col = df.columns[0]  # First column
    lq_col = df.columns[6]      # 7th column (Lq)
    wq_col = df.columns[4]      # 5th column (Wq)
    
    # Prepare data
    X = df[[lambda_col, lq_col]].values
    y = df[wq_col].values
    
    # Remove NaNs and infinite values
    mask = ~(np.isnan(X).any(axis=1) | np.isnan(y) | np.isinf(X).any(axis=1) | np.isinf(y))
    X = X[mask]
    y = y[mask]
    
    print(f"Training improved neural network with {len(X)} samples")
    print(f"Data ranges: lambda=[{X[:, 0].min():.4f}, {X[:, 0].max():.4f}], Lq=[{X[:, 1].min():.4f}, {X[:, 1].max():.4f}], Wq=[{y.min():.4f}, {y.max():.4f}]")
    
    # Train model
    nn = ImprovedQueueNeuralNetwork()
    results = nn.train(X, y, verbose=True)

    # Save model
    nn.save_model('improved_queue_nn_model.pkl')

    # --- PLOTTING SECTION ---
    # Reload data for plotting
    lambda_vals = df[lambda_col].values[mask]
    lq_vals = df[lq_col].values[mask]
    rho_vals = df[df.columns[3]].values[mask]  # 4th column is rho
    wq_real = y
    X_full = np.column_stack([lambda_vals, lq_vals])
    wq_pred = nn.predict(X_full)

    # Plot Wq vs lambda
    plt.figure(figsize=(8,5))
    plt.scatter(lambda_vals, wq_real, color='red', label='Real Wq', alpha=0.6)
    plt.scatter(lambda_vals, wq_pred, color='blue', label='Predicted Wq', alpha=0.6)
    plt.xlabel('Lambda (λ)')
    plt.ylabel('Wq')
    plt.title('Wq vs Lambda')
    plt.legend()
    plt.grid(True)
    plt.show()

    # Plot Wq vs Lq
    plt.figure(figsize=(8,5))
    plt.scatter(lq_vals, wq_real, color='red', label='Real Wq', alpha=0.6)
    plt.scatter(lq_vals, wq_pred, color='blue', label='Predicted Wq', alpha=0.6)
    plt.xlabel('Lq')
    plt.ylabel('Wq')
    plt.title('Wq vs Lq')
    plt.legend()
    plt.grid(True)
    plt.show()

    # Plot Wq vs Rho
    plt.figure(figsize=(8,5))
    plt.scatter(rho_vals, wq_real, color='red', label='Real Wq', alpha=0.6)
    plt.scatter(rho_vals, wq_pred, color='blue', label='Predicted Wq', alpha=0.6)
    plt.xlabel('Rho (ρ)')
    plt.ylabel('Wq')
    plt.title('Wq vs Rho')
    plt.legend()
    plt.grid(True)
    plt.show()
    # --- END PLOTTING SECTION ---
    
    # Test predictions
    test_cases = [
        (0.5, 10),
        (1.0, 5),
        (2.0, 8),
        (0.1, 2),
        (0.8, 16)
    ]
    
    print("\nTest Predictions:")
    for lambda_val, lq_val in test_cases:
        X_test = np.array([[lambda_val, lq_val]])
        pred = nn.predict(X_test)[0]
        print(f"  lambda={lambda_val}, Lq={lq_val} → Predicted Wq = {pred:.4f}")
    
    return nn

if __name__ == "__main__":
    train_improved_model() 