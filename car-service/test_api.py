"""Quick API test script for car-service."""

import requests
import json
from uuid import uuid4

BASE_URL = "http://localhost:8002/api"

def test_health():
    """Test health endpoint."""
    response = requests.get("http://localhost:8002/health")
    print(f"Health check: {response.status_code} - {response.json()}")

def test_add_car():
    """Test adding a new car."""
    car_data = {
        "owner_id": str(uuid4()),
        "license_plate": "ABC123",
        "vin": "1HGBH41JXMN109186",
        "make": "Toyota",
        "model": "Camry",
        "year": 2022
    }
    
    response = requests.post(f"{BASE_URL}/cars", json=car_data)
    print(f"\nAdd car: {response.status_code}")
    if response.status_code == 201:
        car = response.json()
        print(f"Car created: {json.dumps(car, indent=2)}")
        return car['car_id']
    else:
        print(f"Error: {response.json()}")
    return None

def test_get_car(car_id):
    """Test getting car information."""
    response = requests.get(f"{BASE_URL}/cars/{car_id}")
    print(f"\nGet car: {response.status_code}")
    if response.status_code == 200:
        print(f"Car info: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Error: {response.json()}")

def test_add_document(car_id):
    """Test adding a document to a car."""
    doc_data = {
        "document_type": "registration",
        "file": "registration_doc.pdf"
    }
    
    response = requests.post(f"{BASE_URL}/cars/{car_id}/documents", json=doc_data)
    print(f"\nAdd document: {response.status_code}")
    if response.status_code == 200:
        print(f"Document created: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Error: {response.json()}")

def test_duplicate_vin():
    """Test duplicate VIN validation."""
    car_data = {
        "owner_id": str(uuid4()),
        "license_plate": "XYZ789",
        "vin": "1HGBH41JXMN109186",  # Same VIN
        "make": "Honda",
        "model": "Accord",
        "year": 2023
    }
    
    response = requests.post(f"{BASE_URL}/cars", json=car_data)
    print(f"\nDuplicate VIN test: {response.status_code}")
    if response.status_code == 409:
        print("Correctly rejected duplicate VIN")
        print(f"Error: {response.json()}")
    else:
        print("Unexpected response")

def test_not_found():
    """Test 404 for non-existent car."""
    fake_id = str(uuid4())
    response = requests.get(f"{BASE_URL}/cars/{fake_id}")
    print(f"\nNot found test: {response.status_code}")
    if response.status_code == 404:
        print("Correctly returned 404 for non-existent car")
    else:
        print(f"Unexpected response: {response.json()}")

if __name__ == "__main__":
    print("=== Car Service API Tests ===")
    
    # Test health
    test_health()
    
    # Test adding car
    car_id = test_add_car()
    
    if car_id:
        # Test getting car
        test_get_car(car_id)
        
        # Test adding document
        test_add_document(car_id)
    
    # Test duplicate VIN
    test_duplicate_vin()
    
    # Test not found
    test_not_found()
    
    print("\n=== Tests completed ===")
