from app.core.security import hash_password
import sys

def test_hashing():
    test_pwd = "@RoziBerutu123"
    print(f"Testing hashing for: {test_pwd}")
    print(f"Password length: {len(test_pwd)}")
    
    try:
        hashed = hash_password(test_pwd)
        print(f"SUCCESS! Hash: {hashed}")
    except Exception as e:
        print(f"FAILED! Error: {str(e)}")
        print(f"Error type: {type(e)}")

if __name__ == "__main__":
    test_hashing()
