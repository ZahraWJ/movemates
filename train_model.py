import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

def load_and_prepare_data(filepath="ruttdata.csv"):
    """Load and prepare the route data for training."""
    df = pd.read_csv(filepath)
    
    # Convert categorical labels to numerical
    label_map = {"lätt": 0, "medel": 1, "svår": 2}
    df['label_numeric'] = df['label'].map(label_map)
    
    # Prepare features
    X = df[["max_lutning", "risk_percent", "total_length_m"]]
    y = df['label_numeric']
    
    return X, y, label_map

def train_model(X, y):
    """Train a Random Forest model with cross-validation."""
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Initialize and train model
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42
    )
    
    # Perform cross-validation with fewer folds for small datasets
    n_samples = len(X_train)
    # Find the minimum number of samples in any class
    min_class_count = y_train.value_counts().min()
    n_folds = min(3, n_samples, min_class_count)
    if n_folds > 1:
        cv_scores = cross_val_score(model, X_train, y_train, cv=n_folds)
        print(f"Cross-validation scores: {cv_scores}")
        print(f"Average CV score: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
    else:
        print("Not enough samples per class for cross-validation.")
    
    # Train final model
    model.fit(X_train, y_train)
    
    # Evaluate on test set
    y_pred = model.predict(X_test)
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # Create confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.savefig('confusion_matrix.png')
    
    return model, X_test, y_test

def save_model(model, label_map):
    """Save the trained model and label mapping."""
    model_data = {
        'model': model,
        'label_map': label_map
    }
    joblib.dump(model_data, "ml_modell.pkl")
    print("Model saved as ml_modell.pkl")

def main():
    print("Loading and preparing data...")
    X, y, label_map = load_and_prepare_data()
    
    print("\nTraining model...")
    model, X_test, y_test = train_model(X, y)
    
    print("\nSaving model...")
    save_model(model, label_map)
    
    print("\nTraining complete! Model saved as ml_modell.pkl")

if __name__ == "__main__":
    main()


