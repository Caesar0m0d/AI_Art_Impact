# -*- coding: utf-8 -*-
"""241022_추천시스템_v1.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1w0HbVeASIEfunzXx1JY6cjBUOjj0hUxf
"""

import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.neighbors import NearestNeighbors
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module='sklearn')

def get_wine_recmd(file_path, user_input, n_neighbors=3):

    # Load data
    df = pd.read_excel(file_path)
    df['type'] = df['type'].str.lower()
    df['country'] = df['country'].str.lower()

    # Encode categorical variables
    le_type = LabelEncoder()
    le_country = LabelEncoder()
    df['type_encoded'] = le_type.fit_transform(df['type'])
    df['country_encoded'] = le_country.fit_transform(df['country'])

    # Encode ordinal variables
    ordinal_features = ['density', 'smoothness', 'tannin']
    mapping = {'low': 1, 'medium': 2, 'high': 3}
    for feature in ordinal_features:
        if df[feature].dtype == 'object':
            df[feature] = df[feature].map(mapping)
    
    # Fill missing values
    df[ordinal_features] = df[ordinal_features].fillna(df[ordinal_features].median())

    # Scale data
    scaler = StandardScaler()
    df[ordinal_features] = scaler.fit_transform(df[ordinal_features])

    # Encode and scale user input
    user_input_encoded = [
        le_type.transform([user_input['type']])[0] if user_input['type'] in le_type.classes_ else -1,
        mapping[user_input['density']],
        mapping[user_input['smoothness']],
        mapping[user_input['tannin']],
        le_country.transform([user_input['country']])[0] if user_input['country'] in le_country.classes_ else -1
    ]
    user_input_encoded[1:4] = scaler.transform([user_input_encoded[1:4]])[0]

    # Build and fit the model
    features = ['type_encoded', 'density', 'smoothness', 'tannin', 'country_encoded']
    X = df[features]
    model = NearestNeighbors(n_neighbors=n_neighbors, metric='euclidean')
    model.fit(X)

    # Recommend wines
    distances, indices = model.kneighbors([user_input_encoded])
    recommended_wines = df.iloc[indices[0]]['wine'].tolist()

    return recommended_wines

