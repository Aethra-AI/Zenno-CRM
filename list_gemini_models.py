import requests
import os

API_KEY = "AIzaSyAJ7fim0NamF26frknzop_n3uzlR-WQKA4"
URL = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"

try:
    response = requests.get(URL)
    if response.status_code == 200:
        models = response.json().get('models', [])
        print(f"Found {len(models)} models:")
        for model in models:
            if 'generateContent' in model.get('supportedGenerationMethods', []):
                print(f"- {model['name']} ({model['displayName']})")
    else:
        print(f"Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"Error: {e}")
