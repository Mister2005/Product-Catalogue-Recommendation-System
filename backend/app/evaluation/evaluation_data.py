"""
Evaluation data loader for SHL Assignment
Loads train and test data from Gen_AI Dataset.xlsx
"""
import pandas as pd
from typing import Dict, List
import os
from pathlib import Path


def get_dataset_path() -> str:
    """Get path to Gen_AI Dataset.xlsx"""
    # Look for the file in the project root
    current_dir = Path(__file__).parent.parent.parent.parent
    dataset_path = current_dir / "Gen_AI Dataset.xlsx"
    
    if not dataset_path.exists():
        raise FileNotFoundError(f"Gen_AI Dataset.xlsx not found at {dataset_path}")
    
    return str(dataset_path)


def load_train_data() -> Dict[str, List[str]]:
    """
    Load labeled train set from Excel
    
    Returns:
        Dictionary mapping query to list of relevant assessment URLs
        Format: {query: [url1, url2, ...]}
    """
    dataset_path = get_dataset_path()
    
    # Read Train-Set sheet
    df = pd.read_excel(dataset_path, sheet_name='Train-Set')
    
    # Group by Query to get all relevant URLs per query
    train_data = {}
    for query in df['Query'].unique():
        query_rows = df[df['Query'] == query]
        urls = query_rows['Assessment_url'].tolist()
        train_data[query] = urls
    
    return train_data


def load_test_data() -> List[str]:
    """
    Load unlabeled test set from Excel
    
    Returns:
        List of test queries
    """
    dataset_path = get_dataset_path()
    
    # Read Test-Set sheet
    df = pd.read_excel(dataset_path, sheet_name='Test-Set')
    
    # Get unique queries
    queries = df['Query'].unique().tolist()
    
    return queries


def get_train_queries() -> List[str]:
    """Get list of train queries"""
    train_data = load_train_data()
    return list(train_data.keys())


def get_ground_truth(query: str) -> List[str]:
    """
    Get ground truth URLs for a specific query
    
    Args:
        query: Query string
        
    Returns:
        List of relevant assessment URLs
    """
    train_data = load_train_data()
    return train_data.get(query, [])
