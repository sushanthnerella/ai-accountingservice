import os
import abc
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from backend.app.core.config import settings

class StorageService(abc.ABC):
    @abc.abstractmethod
    async def save_file(self, content: bytes, path: str) -> str:
        pass
    @abc.abstractmethod
    async def read_file(self, path: str) -> bytes:
        pass

class LocalEncryptedStorageService(StorageService):
    def __init__(self, base_path: str = settings.LOCAL_STORAGE_PATH, secret_key: str = settings.STORAGE_ENCRYPTION_KEY):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)
        self.key = hashlib.sha256(secret_key.encode()).digest()
        self.aesgcm = AESGCM(self.key)

    async def save_file(self, content: bytes, path: str) -> str:
        full_path = os.path.join(self.base_path, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        nonce = os.urandom(12)
        encrypted_data = self.aesgcm.encrypt(nonce, content, None)
        with open(full_path, "wb") as f:
            f.write(nonce + encrypted_data)
        return path

    async def read_file(self, path: str) -> bytes:
        full_path = os.path.join(self.base_path, path)
        with open(full_path, "rb") as f:
            data = f.read()
        return self.aesgcm.decrypt(data[:12], data[12:], None)

def get_storage_service() -> StorageService:
    return LocalEncryptedStorageService()
