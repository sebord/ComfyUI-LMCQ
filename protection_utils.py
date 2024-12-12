import torch
import hashlib
import numpy as np
from typing import Dict, Any
import os
import json
from safetensors.torch import save_file, load_file
import time


class ModelProtector:
    def __init__(self):
        self.ENCRYPTION_VERSION = "1.0"
        self.SIGNATURE_KEY = "model_protection_signature"
        self.META_FILE_SUFFIX = ".meta"

    def _generate_key_params(self, key: str) -> Dict[str, float]:
        """根据密钥生成确定性的变换参数"""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        np.random.seed(int(key_hash[:8], 16))

        return {
            'scale': np.random.uniform(0.8, 1.2),
            'bias': np.random.uniform(-0.1, 0.1)
        }

    def _save_metadata(self, model_path: str, metadata: Dict) -> None:
        """保存模型元数据"""
        meta_path = model_path + self.META_FILE_SUFFIX
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)

    def _load_metadata(self, model_path: str) -> Dict:
        """加载模型元数据"""
        meta_path = model_path + self.META_FILE_SUFFIX
        if not os.path.exists(meta_path):
            raise ValueError(f"Metadata file not found: {meta_path}")

        with open(meta_path, 'r') as f:
            return json.load(f)

    def _verify_key(self, model_path: str, key: str) -> bool:
        """验证密钥
        Args:
            model_path: 模型路径
            key: 密钥
        Returns:
            bool: 密钥是否有效
        """
        try:
            metadata = self._load_metadata(model_path)
            key_hash = hashlib.sha256(key.encode()).hexdigest()
            stored_hash = metadata.get(self.SIGNATURE_KEY)

            print(f"Verifying key for model: {model_path}")
            print(f"Stored hash: {stored_hash}")
            print(f"Current key hash: {key_hash}")

            return stored_hash == key_hash
        except Exception as e:
            print(f"Key verification error: {str(e)}")
            return False

    def encrypt(self, model_path: str, save_path: str, key: str) -> None:
        """加密模型
        Args:
            model_path: 原始模型路径
            save_path: 加密后保存路径
            key: 加密密钥
        """
        if not key:
            raise ValueError("Encryption key cannot be empty")

        try:
            # 加载原始模型
            state_dict = load_file(model_path)
            print(f"Loaded model from: {model_path}")

            # 生成加密参数
            params = self._generate_key_params(key)
            print(f"Generated encryption parameters")

            # 加密模型权重
            encrypted_dict = {}
            for k, tensor in state_dict.items():
                if torch.is_tensor(tensor):
                    encrypted_dict[k] = tensor * params['scale'] + params['bias']
                else:
                    encrypted_dict[k] = tensor
            print(f"Encrypted model weights")

            # 准备元数据
            metadata = {
                'encryption_version': self.ENCRYPTION_VERSION,
                'encryption_time': time.time(),
                self.SIGNATURE_KEY: hashlib.sha256(key.encode()).hexdigest()
            }

            # 保存加密模型和元数据
            save_file(encrypted_dict, save_path)
            self._save_metadata(save_path, metadata)
            print(f"Saved encrypted model to: {save_path}")
            print(f"Saved metadata with key hash: {metadata[self.SIGNATURE_KEY]}")

        except Exception as e:
            print(f"Encryption error: {str(e)}")
            raise ValueError(f"Failed to encrypt model: {str(e)}")

    def decrypt(self, model_path: str, save_path: str, key: str) -> None:
        """解密模型
        Args:
            model_path: 加密模型路径
            save_path: 解密后保存路径
            key: 解密密钥
        """
        if not key:
            raise ValueError("Decryption key cannot be empty")

        # 验证密钥
        if not self._verify_key(model_path, key):
            raise ValueError(f"Invalid encryption key for model: {model_path}")

        try:
            # 加载加密模型
            encrypted_dict = load_file(model_path)
            print(f"Loaded encrypted model from: {model_path}")

            # 生成解密参数
            params = self._generate_key_params(key)
            print(f"Generated decryption parameters")

            # 解密模型权重
            decrypted_dict = {}
            for k, tensor in encrypted_dict.items():
                if torch.is_tensor(tensor):
                    decrypted_dict[k] = (tensor - params['bias']) / params['scale']
                else:
                    decrypted_dict[k] = tensor
            print(f"Decrypted model weights")

            # 保存解密后的模型
            save_file(decrypted_dict, save_path)
            print(f"Saved decrypted model to: {save_path}")

        except Exception as e:
            print(f"Decryption error: {str(e)}")
            raise ValueError(f"Failed to decrypt model: {str(e)}")

    def is_encrypted(self, model_path: str) -> bool:
        """检查模型是否已加密"""
        try:
            self._load_metadata(model_path)
            return True
        except:
            return False