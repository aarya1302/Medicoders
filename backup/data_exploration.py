import kagglehub
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import pyreadr
from sklearn.preprocessing import LabelEncoder

def load_dataset():
    """Download and load the hospital triage dataset"""
    # Download latest version
    path = kagglehub.dataset_download("maalona/hospital-triage-and-patient-history-data")
    print(f"Path to dataset files: {path}")
    
    # Load the R data file
    data_file = Path(path) / "5v_cleandf.rdata"
    result = pyreadr.read_r(str(data_file))
    
    # Get the first (and likely only) dataframe from the R file
    df_name = list(result.keys())[0]
    df = result[df_name]
    
    return df

def explore_dataset(df):
    """Perform basic exploratory data analysis"""
    print("\n=== DATASET OVERVIEW ===")
    print(f"Dataset shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    print("\n=== DATA TYPES ===")
    print(df.dtypes)
    
    print("\n=== MISSING VALUES ===")
    missing = df.isnull().sum()
    print(missing[missing > 0])
    
    print("\n=== FIRST 5 ROWS ===")
    print(df.head())
    
    return df

def analyze_triage_data(df):
    """Analyze hospital triage patterns"""
    print("\n=== TRIAGE ANALYSIS ===")
    
    # Look for triage-related columns
    triage_cols = [col for col in df.columns if 'triage' in col.lower() or 'priority' in col.lower() or 'urgency' in col.lower()]
    print(f"Potential triage columns: {triage_cols}")
    
    # Basic statistics for numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        print("\n=== NUMERIC COLUMNS SUMMARY ===")
        print(df[numeric_cols].describe())
    
    # Categorical columns analysis
    categorical_cols = df.select_dtypes(include=['object']).columns
    if len(categorical_cols) > 0:
        print("\n=== CATEGORICAL COLUMNS VALUE COUNTS ===")
        for col in categorical_cols[:5]:  # Show first 5 categorical columns
            print(f"\n{col}:")
            print(df[col].value_counts().head())

def visualize_data(df):
    """Create visualizations for the dataset"""
    # Set up the plotting style
    plt.style.use('default')
    sns.set_palette("husl")
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Hospital Triage Dataset Analysis', fontsize=16)
    
    # Plot 1: Missing values heatmap (if there are missing values)
    missing_data = df.isnull().sum()
    if missing_data.sum() > 0:
        sns.heatmap(df.isnull(), ax=axes[0,0], cbar=True, yticklabels=False)
        axes[0,0].set_title('Missing Values Pattern')
    else:
        axes[0,0].text(0.5, 0.5, 'No Missing Values', ha='center', va='center', fontsize=14)
        axes[0,0].set_title('Missing Values Check')
    
    # Plot 2: Distribution of numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        # Plot distribution of first numeric column
        first_numeric = numeric_cols[0]
        df[first_numeric].hist(bins=30, ax=axes[0,1])
        axes[0,1].set_title(f'Distribution of {first_numeric}')
        axes[0,1].set_xlabel(first_numeric)
        axes[0,1].set_ylabel('Frequency')
    
    # Plot 3: Categorical column distribution
    categorical_cols = df.select_dtypes(include=['object']).columns
    if len(categorical_cols) > 0:
        first_categorical = categorical_cols[0]
        value_counts = df[first_categorical].value_counts().head(10)
        value_counts.plot(kind='bar', ax=axes[1,0])
        axes[1,0].set_title(f'Top 10 Values in {first_categorical}')
        axes[1,0].tick_params(axis='x', rotation=45)
    
    # Plot 4: Correlation heatmap (if enough numeric columns)
    if len(numeric_cols) > 1:
        correlation_matrix = df[numeric_cols].corr()
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, ax=axes[1,1])
        axes[1,1].set_title('Correlation Matrix')
    else:
        axes[1,1].text(0.5, 0.5, 'Insufficient numeric\ncolumns for correlation', ha='center', va='center')
        axes[1,1].set_title('Correlation Analysis')
    
    plt.tight_layout()
    plt.savefig('triage_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    print("\nVisualization saved as 'triage_analysis.png'")


def main():
    """Main function to run the hospital triage analysis"""
    try:
        # Load the dataset
        df = load_dataset()
        
        # Explore the dataset
        df = explore_dataset(df)
        
        # Analyze triage patterns
        analyze_triage_data(df)
        
        # Create visualizations
        visualize_data(df)
        
        print("\n=== ANALYSIS COMPLETE ===")
        print("Dataset has been loaded, analyzed, and visualized successfully!")
        
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()