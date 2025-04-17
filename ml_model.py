import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta
from models import Incident

def prepare_data():
    """Prepare incident data for ML model"""
    all_incidents = Incident.get_all_incidents()
    
    if not all_incidents:
        return None, None
    
    # Convert to DataFrame
    data = []
    for incident in all_incidents:
        data.append({
            'created_at': incident.created_at,
            'severity': incident.severity,
            'status': incident.status
        })
    
    df = pd.DataFrame(data)
    
    # If no incidents, return None
    if df.empty:
        return None, None
    
    # Convert created_at to date
    df['date'] = df['created_at'].dt.date
    
    # Create time series with count of incidents per day
    daily_incidents = df.groupby('date').size().reset_index(name='count')
    
    # Sort by date
    daily_incidents = daily_incidents.sort_values('date')
    
    # Add features: day of week, day of month, month
    daily_incidents['day_of_week'] = daily_incidents['date'].apply(lambda x: x.weekday())
    daily_incidents['day_of_month'] = daily_incidents['date'].apply(lambda x: x.day)
    daily_incidents['month'] = daily_incidents['date'].apply(lambda x: x.month)
    
    # Create X (features) and y (target)
    X = daily_incidents[['day_of_week', 'day_of_month', 'month']].values
    y = daily_incidents['count'].values
    
    return X, y

def train_model():
    """Train a simple ML model to predict incident counts"""
    X, y = prepare_data()
    
    if X is None or y is None:
        # Not enough data, return dummy model
        return DummyModel()
    
    # Train linear regression model
    model = LinearRegression()
    model.fit(X, y)
    
    return model

class DummyModel:
    """Dummy model that returns random predictions when there's not enough data"""
    def predict(self, X):
        return np.random.randint(1, 5, size=X.shape[0])

def predict_incidents():
    """Predict incident counts for the next 7 days"""
    model = train_model()
    
    # Generate features for the next 7 days
    future_dates = []
    future_features = []
    
    for i in range(1, 8):
        future_date = datetime.now().date() + timedelta(days=i)
        future_dates.append(future_date)
        
        # Extract features
        day_of_week = future_date.weekday()
        day_of_month = future_date.day
        month = future_date.month
        
        future_features.append([day_of_week, day_of_month, month])
    
    # Make predictions
    future_features = np.array(future_features)
    predictions = model.predict(future_features)
    
    # Ensure predictions are positive integers
    predictions = np.round(np.maximum(predictions, 0)).astype(int)
    
    # Format results
    result = []
    for i, date in enumerate(future_dates):
        result.append({
            'date': date.strftime('%Y-%m-%d'),
            'predicted_incidents': int(predictions[i])
        })
    
    return {
        'prediction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'predictions': result
    }
