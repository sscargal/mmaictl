import requests
import logging

class APIClient:
    def __init__(self, base_url, token=None):
        self.base_url = base_url.rstrip('/')
        self.headers = {'Authorization': f'Bearer {token}'} if token else {}

    def get(self, endpoint, params=None):
        try:
            response = requests.get(f"{self.base_url}/{endpoint}", headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"GET request failed: {str(e)}")
            raise e

    def post(self, endpoint, data=None):
        try:
            response = requests.post(f"{self.base_url}/{endpoint}", headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"POST request failed: {str(e)}")
            raise e

    def put(self, endpoint, data=None):
        try:
            response = requests.put(f"{self.base_url}/{endpoint}", headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"PUT request failed: {str(e)}")
            raise e

    def delete(self, endpoint):
        try:
            response = requests.delete(f"{self.base_url}/{endpoint}", headers=self.headers)
            response.raise_for_status()
            return response.status_code == 204
        except requests.exceptions.RequestException as e:
            logging.error(f"DELETE request failed: {str(e)}")
            raise e
