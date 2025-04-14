import hashlib

def hash256(input_string):
    encoded_string = input_string.encode('utf-8')
    hash_object = hashlib.sha256(encoded_string)
    hash_hex = hash_object.hexdigest()
    return hash_hex 