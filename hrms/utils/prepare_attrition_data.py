# prepare_attrition_data.py

import frappe
import pandas as pd
from datetime import datetime

def get_employee_data():
    """
    Fetches and preprocesses data for all employees.
    """
    employees = frappe.get_all("Employee", fields=["name", "date_of_joining", "department", "designation"])
    employee_df = pd.DataFrame(employees)
    employee_df.rename(columns={"name": "employee"}, inplace=True)

    # Calculate tenure in days
    employee_df['date_of_joining'] = pd.to_datetime(employee_df['date_of_joining'])
    employee_df['tenure_days'] = (datetime.now() - employee_df['date_of_joining']).dt.days

    return employee_df

def get_separation_data():
    """
    Fetches employee separation data to create the target variable.
    """
    separations = frappe.get_all("Employee Separation", fields=["employee"])
    separation_df = pd.DataFrame(separations)
    separation_df['attrition'] = 1
    return separation_df.drop_duplicates(subset=['employee'])

def get_performance_data():
    """
    Fetches and aggregates performance data from appraisals.
    Note: This is a simplified aggregation. A real-world scenario would be more complex.
    """
    appraisals = frappe.get_all("Appraisal", fields=["employee", "total_score"])
    if not appraisals:
        return pd.DataFrame(columns=['employee', 'avg_performance_score'])

    performance_df = pd.DataFrame(appraisals)
    # Basic aggregation: average score
    performance_agg = performance_df.groupby('employee')['total_score'].mean().reset_index()
    performance_agg.rename(columns={'total_score': 'avg_performance_score'}, inplace=True)
    return performance_agg

def get_leave_data():
    """
    Fetches and aggregates leave application data.
    """
    leaves = frappe.get_all("Leave Application", fields=["employee", "total_leave_days"])
    if not leaves:
        return pd.DataFrame(columns=['employee', 'total_leave_days_taken'])

    leave_df = pd.DataFrame(leaves)
    # Basic aggregation: sum of leave days
    leave_agg = leave_df.groupby('employee')['total_leave_days'].sum().reset_index()
    leave_agg.rename(columns={'total_leave_days': 'total_leave_days_taken'}, inplace=True)
    return leave_agg

def create_dataset():
    """
    Main function to orchestrate data fetching, merging, and preprocessing.
    """
    # Fetch data from different doctypes
    emp_df = get_employee_data()
    sep_df = get_separation_data()
    perf_df = get_performance_data()
    leave_df = get_leave_data()

    # Merge datasets
    merged_df = pd.merge(emp_df, sep_df, on='employee', how='left')
    merged_df = pd.merge(merged_df, perf_df, on='employee', how='left')
    merged_df = pd.merge(merged_df, leave_df, on='employee', how='left')

    # --- Preprocessing and Feature Engineering ---

    # Fill NaN for attrition with 0 (employees who haven't left)
    merged_df['attrition'].fillna(0, inplace=True)

    # Impute missing values for features (using median for numeric)
    merged_df['avg_performance_score'].fillna(merged_df['avg_performance_score'].median(), inplace=True)
    merged_df['total_leave_days_taken'].fillna(0, inplace=True)

    # Convert categorical variables to numerical using one-hot encoding
    merged_df = pd.get_dummies(merged_df, columns=['department', 'designation'], drop_first=True)

    # Drop columns that are not needed for the model
    final_df = merged_df.drop(columns=['employee', 'date_of_joining'])

    # Ensure all data is numeric
    # This is a safeguard; proper handling would be more nuanced.
    for col in final_df.columns:
        if final_df[col].dtype == 'object':
            final_df[col] = final_df[col].astype('category').cat.codes

    print("Dataset created successfully!")
    print(final_df.head())
    print(f"\nShape of the dataset: {final_df.shape}")
    print(f"\nAttrition distribution:\n{final_df['attrition'].value_counts()}")

    # Save the processed data to a file for the next step
    final_df.to_csv('processed_attrition_data.csv', index=False)

    return final_df

if __name__ == "__main__":
    # This allows running the script from the command line for testing
    # Note: Requires a running Frappe instance and context
    # frappe.connect(site="your_site_name")
    # create_dataset()
    # frappe.db.commit()
    pass
