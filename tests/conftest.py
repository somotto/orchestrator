import pytest
import requests
import time


@pytest.fixture(scope="session", autouse=True)
def wait_for_services():
    """Wait for services to be ready before running tests"""
    api_url = "http://localhost:3000/api/movies"
    max_retries = 30
    retry_delay = 2
    
    for i in range(max_retries):
        try:
            response = requests.get(api_url, timeout=5)
            if response.status_code == 200:
                print(f"\n✓ Services are ready")
                return
        except requests.exceptions.RequestException:
            pass
        
        if i < max_retries - 1:
            print(f"Waiting for services... ({i+1}/{max_retries})")
            time.sleep(retry_delay)
    
    pytest.fail("Services did not become ready in time")


@pytest.fixture(scope="function")
def clean_movies():
    """Clean up movies after each test"""
    yield
    try:
        requests.delete("http://localhost:3000/api/movies")
    except:
        pass
