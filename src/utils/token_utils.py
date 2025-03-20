from fastapi import HTTPException


def check_token(token: str):
    # Example: Decode the token and check validity.
    # For simplicity, we're assuming token is just a dictionary with user_id.
    # Replace this logic with actual token decoding and validation.

    if not token:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Example token decoding (replace with your actual decoding logic)
    decoded_token = {"user_id": "some-uuid-value"}  # Replace this with actual token decoding logic
    return decoded_token
