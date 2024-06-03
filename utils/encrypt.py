from Crypto.Cipher import AES
import struct
import base64
import execjs

def parse_word_array(word_array):
    byte_array = b''
    for word in word_array["words"]:
        byte_array += struct.pack('>I', word)
    return byte_array

def zero_pad(data, block_size):
    padding_len = block_size - (len(data) % block_size)
    return data + b'\x00' * padding_len
key = {
    "words": [
        808530483,
        875902519,
        943276354,
        1128547654
    ],
    "sigBytes": 16
}
iv = {
    "words": [
        808530483,
        875902519,
        943276354,
        1128547654
    ],
    "sigBytes": 16
}    

key_bytes = parse_word_array(key)
iv_bytes = parse_word_array(iv)


def word_array_to_string(word_array):
    return ''.join(f'{word:08x}' for word in word_array['words'])

def eta_AES_encrypt(text):
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
    padded_text = zero_pad(text.encode('utf-8'), AES.block_size)
    encrypted = cipher.encrypt(padded_text)
    return base64.b64encode(encrypted).decode('utf-8')
import os
with open(os.path.join(os.path.dirname(__file__), "security.js"), "r") as f:
    js_code = f.read()
    ctx = execjs.compile(js_code)

def tc_rsa_encrypt(exponent: str, modulus: str, password: str):
    return ctx.call("encryptPassword", exponent, modulus, password)