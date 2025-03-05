import os
import json
import base64
import hashlib
import ctypes
import time
import psutil
import numpy as np
import torch
from threading import Thread, Lock
import datetime

class SecurityCheck:
    """安全检查类，提供反调试和内存保护功能"""
    _instance = None
    _lock = Lock()
    _security_checks_enabled = True
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SecurityCheck, cls).__new__(cls)
            return cls._instance
    
    @classmethod
    def check_security(cls, silent=True):
        """执行安全检查"""
        if not cls._security_checks_enabled:
            return True
            
        try:
            # 基础调试检测
            if ctypes.windll.kernel32.IsDebuggerPresent():
                if not silent:
                    raise RuntimeError("检测到调试器")
                return False
                
            # 时间检测
            start = time.time()
            for _ in range(1000): pass
            if (time.time() - start) > 0.1:
                if not silent:
                    raise RuntimeError("检测到执行时间异常")
                return False
                
            # 进程检测
            try:
                current = psutil.Process()
                parent = current.parent()
                suspicious = ['ida', 'x64dbg', 'ollydbg', 'windbg']
                if any(s in parent.name().lower() for s in suspicious):
                    if not silent:
                        raise RuntimeError("检测到可疑进程")
                    return False
            except:
                pass
                
            return True
            
        except Exception:
            return True  # 出错时不影响正常功能
    
    @classmethod
    def protect_memory(cls, data):
        """保护内存数据，但不改变数据结构"""
        try:
            if isinstance(data, dict):
                return {k: v for k, v in data.items()}  # 简单复制
            elif isinstance(data, (str, bytes)):
                return data  # 不再分片存储
            elif isinstance(data, torch.Tensor):
                return data.clone().detach()
            return data
        except Exception:
            return data
    
    @classmethod
    def enable_security_checks(cls):
        """启用安全检查"""
        cls._security_checks_enabled = True
    
    @classmethod
    def disable_security_checks(cls):
        """禁用安全检查"""
        cls._security_checks_enabled = False

class ProtectionBase:
    """保护基类"""
    _security = SecurityCheck()
    
    @classmethod
    def save_metadata(cls, meta_path, meta_data):
        """保存元数据到文件
        Args:
            meta_path: 元数据文件路径
            meta_data: 元数据字典
        """
        try:
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta_data, f, indent=2)
        except Exception as e:
            raise ValueError(f"保存元数据失败: {str(e)}")
    
    @classmethod
    def load_metadata(cls, meta_path):
        """从文件加载元数据
        Args:
            meta_path: 元数据文件路径
        Returns:
            dict: 元数据字典
        """
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta_encoded = f.read()
            # 解码 base64 并解析 JSON
            meta_json = base64.b64decode(meta_encoded).decode()
            return json.loads(meta_json)
        except Exception as e:
            raise ValueError(f"加载元数据失败: {str(e)}")
    
    @classmethod
    def verify_metadata_type(cls, meta_data, expected_type):
        """验证元数据类型
        Args:
            meta_data: 元数据字典
            expected_type: 期望的类型
        """
        actual_type = meta_data.get('type')
        if actual_type != expected_type:
            raise ValueError(f"元数据类型不匹配: 期望 {expected_type}, 实际 {actual_type}")
    
    @classmethod
    def verify_key(cls, meta_data, key):
        """验证密钥
        Args:
            meta_data: 元数据字典
            key: 待验证的密钥
        Returns:
            bool: 验证结果
        """
        stored_hash = meta_data.get('key_hash')
        if not stored_hash:
            return False
        return cls._hash_key(key) == stored_hash
    
    @classmethod
    def verify_machine_code(cls, meta_data, machine_code, key):
        """验证机器码
        Args:
            meta_data: 元数据字典
            machine_code: 待验证的机器码
            key: 密钥
        Returns:
            bool: 验证结果
        """
        if not cls.verify_key(meta_data, key):
            return False
            
        authorized_codes = meta_data.get('machine_codes', [])
        # 如果授权机器码列表为空，则跳过机器码验证，直接返回True
        if not authorized_codes:
            return True
            
        return machine_code in authorized_codes
    
    @classmethod
    def _generate_key_params(cls, key, tensor_name=None):
        """根据密钥和张量名生成加密参数
        Args:
            key: 加密密钥
            tensor_name: 张量名称（可选）
        Returns:
            dict: 包含 scale 和 bias 的参数字典
        """
        if not key:
            raise ValueError("密钥不能为空")
            
        # 组合密钥和张量名
        combined = key
        if tensor_name:
            combined = key + tensor_name
            
        # 使用密钥生成哈希
        key_hash = hashlib.sha256(combined.encode()).digest()
        
        # 使用哈希值生成浮点数参数
        import struct
        float_values = [
            struct.unpack('f', key_hash[i:i+4])[0] 
            for i in range(0, min(len(key_hash), 16), 4)
        ]
        
        # 生成缩放和偏移参数 - 使用更明显的范围
        scale = abs(float_values[0] % 0.5) + 1.5  # 1.5-2.0 范围
        bias = (float_values[1] % 1.0) - 0.5  # -0.5 到 0.5 范围
        
        return {
            'scale': scale,
            'bias': bias
        }
    
    @classmethod
    def encrypt_data(cls, data_path, key):
        """加密数据
        Args:
            data_path: 数据文件路径
            key: 加密密钥
        Returns:
            dict: 加密后的数据字典
        """
        cls._security.check_security()
        if not os.path.exists(data_path):
            raise ValueError(f"文件不存在: {data_path}")
            
        try:
            # 读取数据
            if data_path.endswith('.safetensors'):
                from safetensors.torch import load_file
                data_dict = load_file(data_path)
            else:
                data_dict = torch.load(data_path)
            
            # 生成基础加密参数
            base_params = cls._generate_key_params(key)
            scale = base_params['scale'] * 1.5  # 使用更明显的缩放
            bias = base_params['bias'] * 3.0    # 使用更明显的偏移
            
            print(f"使用加密参数: scale={scale}, bias={bias}")
            
            # 加密张量数据 - 使用简单但有效的线性变换
            encrypted_dict = {}
            for k, tensor in data_dict.items():
                if torch.is_tensor(tensor):
                    # 保存原始数据类型
                    original_dtype = tensor.dtype
                    
                    # 转换为float32进行操作以避免精度问题
                    tensor_f32 = tensor.to(torch.float32)
                    
                    # 应用线性变换加密
                    encrypted = tensor_f32 * scale + bias
                    
                    # 转回原始数据类型
                    encrypted_dict[k] = encrypted.to(original_dtype)
                else:
                    encrypted_dict[k] = tensor
            
            # 添加加密标记
            encrypted_dict["_encryption_version"] = torch.tensor([1.0])
            
            return encrypted_dict
            
        except Exception as e:
            import traceback
            print(f"加密失败详细信息: {traceback.format_exc()}")
            raise ValueError(f"加密失败: {str(e)}")
    
    @classmethod
    def decrypt_data(cls, encrypted_dict, key):
        """解密数据
        Args:
            encrypted_dict: 加密后的数据字典
            key: 解密密钥
        Returns:
            dict: 解密后的数据字典
        """
        cls._security.check_security()
        
        try:
            # 生成基础解密参数
            base_params = cls._generate_key_params(key)
            scale = base_params['scale'] * 1.5  # 与加密时相同
            bias = base_params['bias'] * 3.0    # 与加密时相同
            
            print(f"使用解密参数: scale={scale}, bias={bias}")
            
            # 解密每个张量
            decrypted_dict = {}
            for k, tensor in encrypted_dict.items():
                if k == "_encryption_version":
                    continue
                    
                if torch.is_tensor(tensor):
                    # 保存原始数据类型
                    original_dtype = tensor.dtype
                    
                    # 转换为float32进行操作以避免精度问题
                    tensor_f32 = tensor.to(torch.float32)
                    
                    # 应用线性变换解密
                    decrypted = (tensor_f32 - bias) / scale
                    
                    # 转回原始数据类型
                    decrypted_dict[k] = decrypted.to(original_dtype)
                else:
                    decrypted_dict[k] = tensor
            
            return decrypted_dict
            
        except Exception as e:
            import traceback
            print(f"解密失败详细信息: {traceback.format_exc()}")
            raise ValueError(f"解密失败: {str(e)}")
    
    @classmethod
    def create_metadata(cls, **kwargs):
        """创建元数据
        Args:
            key: 加密密钥
            machine_codes: 授权机器码列表
            type_name: 加密类型
        Returns:
            str: base64编码的元数据
        """
        # 使用统一的哈希方法
        key_hash = cls._hash_key(kwargs.get('key', ''))
        
        # 构建元数据
        metadata = {
            'key_hash': key_hash,
            'machine_codes': kwargs.get('machine_codes', []),
            'type': kwargs.get('type_name', 'unknown'),
            'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 将元数据转换为 JSON 字符串并进行 base64 编码
        meta_json = json.dumps(metadata)
        meta_encoded = base64.b64encode(meta_json.encode()).decode()
        
        return meta_encoded
    
    @classmethod
    def process_machine_codes(cls, machine_codes_text):
        """处理机器码文本，转换为列表
        Args:
            machine_codes_text: 机器码文本，每行一个
        Returns:
            list: 机器码列表
        """
        if not machine_codes_text.strip():
            return []
            
        # 按行分割，并移除空行
        codes = [line.strip() for line in machine_codes_text.split('\n') if line.strip()]
        return codes
    
    @classmethod
    def _hash_key(cls, key):
        """生成密钥的哈希值
        Args:
            key: 加密密钥
        Returns:
            str: 密钥的哈希值
        """
        if not key:
            raise ValueError("密钥不能为空")
        return hashlib.sha256(key.encode()).hexdigest()
    
    # 其他方法保持不变...