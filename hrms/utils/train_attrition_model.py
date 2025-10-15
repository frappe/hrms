# train_attrition_model.py

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

def train_model():
    """
    Loads the processed data, trains a RandomForestClassifier, evaluates it,
    and saves the trained model.
    """
    # Define file paths
    data_path = 'processed_attrition_data.csv'
    model_dir = 'hrms/ml_models'
    model_path = os.path.join(model_dir, 'attrition_model.joblib')

    # Ensure the directory for saving the model exists
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)

    # --- 1. Load Data ---
    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        print(f"Error: The data file '{data_path}' was not found.")
        print("Please run the 'prepare_attrition_data.py' script first.")
        return

    # --- 2. Prepare Data for Training ---
    X = df.drop('attrition', axis=1)
    y = df['attrition']

    # Get feature names to save them with the model
    feature_names = X.columns.tolist()

    # --- 3a. Calculate and store the median for imputation ---
    median_performance_score = X['avg_performance_score'].median()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # --- 3. Train the Model ---
    print("Training the RandomForestClassifier...")
    # Using class_weight='balanced' is a good practice for imbalanced datasets
    model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    model.fit(X_train, y_train)
    print("Model training complete.")

    # --- 4. Evaluate the Model ---
    print("\n--- Model Evaluation ---")
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Accuracy on the test set: {accuracy:.2f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    # --- 5. Save the Model and Feature Names ---
    print(f"\nSaving model to '{model_path}'...")
    model_payload = {
        'model': model,
        'feature_names': feature_names,
        'median_performance_score': median_performance_score
    }
    joblib.dump(model_payload, model_path)
    print("Model saved successfully.")

if __name__ == '__main__':
    # This part allows the script to be run directly.
    # It assumes the 'processed_attrition_data.csv' is in the root directory.
    # In a real Frappe app, you'd call this function from a hook or a custom script.

    # For standalone execution, we need to simulate some data if the CSV doesn't exist.
    if not os.path.exists('processed_attrition_data.csv'):
        print("Simulating data for standalone run...")
        # Create a dummy CSV for testing purposes
        dummy_data = {
            'tenure_days': [100, 200, 500, 1000, 1500, 2000, 300, 400, 600, 800],
            'avg_performance_score': [3, 4, 3, 5, 2, 4, 3, 4, 5, 2],
            'total_leave_days_taken': [10, 5, 12, 2, 20, 8, 9, 3, 4, 15],
            'department_HR': [1, 0, 0, 0, 1, 0, 1, 0, 0, 0],
            'designation_Manager': [0, 1, 0, 1, 0, 1, 0, 0, 1, 0],
            'attrition': [1, 0, 1, 0, 1, 0, 0, 0, 0, 1]
        }
        pd.DataFrame(dummy_data).to_csv('processed_attrition_data.csv', index=False)

    train_model()
