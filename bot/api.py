import requests
import os

API_URL = os.getenv("API_URL")

def create_property(data):
    return requests.post(f"{API_URL}/property", json=data).json()

def search_property(params):
    return requests.get(f"{API_URL}/properties", params=params).json()

def create_lead(data):
    return requests.post(f"{API_URL}/lead", json=data).json()
