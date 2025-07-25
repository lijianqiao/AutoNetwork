"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: encryption.py
@DateTime: 2025/07/23
@Docs: 加密工具类 - AES加密解密
"""

import base64
import secrets

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
except ImportError as e:
    raise ImportError("加密依赖未安装。请运行: pip install cryptography") from e

from app.core.config import settings
from app.utils.logger import logger


class EncryptionManager:
    """加密管理器 - 提供AES加密解密功能"""

    def __init__(self):
        self.encryption_key = self._get_encryption_key()
        self.fernet = Fernet(self.encryption_key)

    def _get_encryption_key(self) -> bytes:
        """获取加密密钥

        Returns:
            加密密钥
        """
        # 使用配置中的密钥或生成新密钥
        if hasattr(settings, "ENCRYPTION_KEY") and settings.ENCRYPTION_KEY:
            # 从配置的密钥派生Fernet密钥
            password = settings.ENCRYPTION_KEY.encode()
            salt = b"autonetwork_salt"  # 固定盐值，确保密钥一致性
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
            return key
        else:
            # 如果没有配置密钥，使用SECRET_KEY派生
            password = settings.SECRET_KEY.encode()
            salt = b"autonetwork_salt"
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
            return key

    def encrypt(self, plaintext: str) -> str:
        """加密字符串

        Args:
            plaintext: 明文字符串

        Returns:
            加密后的字符串（Base64编码）
        """
        if not plaintext:
            return ""

        try:
            return self.fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")
        except Exception as e:
            logger.error(f"加密失败: {e}")
            raise ValueError(f"加密失败: {e}") from e

    def decrypt(self, encrypted_text: str) -> str:
        """解密字符串

        Args:
            encrypted_text: 加密的字符串（Base64编码）

        Returns:
            解密后的明文字符串
        """
        if not encrypted_text:
            return ""

        try:
            decrypted_bytes = self.fernet.decrypt(encrypted_text.encode("utf-8"))
            return decrypted_bytes.decode("utf-8")
        except Exception as e:
            # 不记录错误日志，因为可能是明文密码导致的正常解密失败
            raise ValueError(f"解密失败: {e}") from e

    def encrypt_if_not_empty(self, plaintext: str | None) -> str | None:
        """如果不为空则加密

        Args:
            plaintext: 明文字符串或None

        Returns:
            加密后的字符串或None
        """
        if plaintext is None or plaintext.strip() == "":
            return None
        return self.encrypt(plaintext)

    def decrypt_if_not_empty(self, encrypted_text: str | None) -> str | None:
        """如果不为空则解密

        Args:
            encrypted_text: 加密的字符串或None

        Returns:
            解密后的明文字符串或None
        """
        if encrypted_text is None or encrypted_text.strip() == "":
            return None
        return self.decrypt(encrypted_text)

    @staticmethod
    def generate_key() -> str:
        """生成新的Fernet密钥

        Returns:
            Base64编码的密钥字符串
        """
        key = Fernet.generate_key()
        return base64.urlsafe_b64encode(key).decode("utf-8")

    @staticmethod
    def generate_random_password(length: int = 16) -> str:
        """生成随机密码

        Args:
            length: 密码长度

        Returns:
            随机密码
        """
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return "".join(secrets.choice(alphabet) for _ in range(length))


# 全局加密管理器实例
encryption_manager = EncryptionManager()


# 便捷函数
def encrypt_text(plaintext: str) -> str:
    """加密文本便捷函数"""
    return encryption_manager.encrypt(plaintext)


def decrypt_text(encrypted_text: str) -> str:
    """解密文本便捷函数"""
    return encryption_manager.decrypt(encrypted_text)


def encrypt_if_not_empty(plaintext: str | None) -> str | None:
    """如果不为空则加密便捷函数"""
    return encryption_manager.encrypt_if_not_empty(plaintext)


def decrypt_if_not_empty(encrypted_text: str | None) -> str | None:
    """如果不为空则解密便捷函数"""
    return encryption_manager.decrypt_if_not_empty(encrypted_text)
