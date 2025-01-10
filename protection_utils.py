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
        return machine_code in authorized_codes
    
    @classmethod
    def _generate_key_params(cls, key):
        """根据密钥生成加密参数
        Args:
            key: 加密密钥
        Returns:
            dict: 包含 scale 和 bias 的参数字典
        """
        if not key:
            raise ValueError("密钥不能为空")
            
        # 使用密钥生成哈希
        key_hash = hashlib.sha256(key.encode()).digest()
        
        # 使用哈希值生成浮点数参数
        import struct
        float_values = [
            struct.unpack('f', key_hash[i:i+4])[0] 
            for i in range(0, 8, 4)
        ]
        
        # 生成缩放和偏移参数
        scale = abs(float_values[0]) % 0.5 + 1.0  # 1.0-1.5 范围
        bias = float_values[1] % 0.1  # 小偏移量
        
        return {
            'scale': scale,
            'bias': bias
        }
    
    @classmethod
    def encrypt_data(cls, data_path, key):
        """加密数据"""
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
            
            # 生成加密参数
            params = cls._generate_key_params(key)
            
            # 加密张量数据
            def encrypt_tensor(tensor):
                if torch.is_tensor(tensor):
                    return tensor * params['scale'] + params['bias']
                return tensor
            
            def process_dict(d):
                result = {}
                if isinstance(d, dict):
                    # 处理字典
                    for k, v in d.items():
                        if isinstance(v, dict):
                            # 递归处理嵌套字典
                            processed = process_dict(v)
                            # 如果处理后的字典包含张量，则展平
                            if any(torch.is_tensor(tv) for tv in processed.values()):
                                for sub_k, sub_v in processed.items():
                                    if torch.is_tensor(sub_v):
                                        result[f"{k}.{sub_k}"] = encrypt_tensor(sub_v)
                            else:
                                result[k] = processed
                        elif torch.is_tensor(v):
                            result[k] = encrypt_tensor(v)
                        else:
                            # 忽略非张量数据
                            continue
                elif torch.is_tensor(d):
                    return encrypt_tensor(d)
                return result
            
            # 处理整个字典
            encrypted_dict = process_dict(data_dict)
            
            # 验证结果
            if not encrypted_dict:
                raise ValueError("没有找到可加密的张量数据")
            
            # 确保所有值都是张量
            for k, v in list(encrypted_dict.items()):
                if not torch.is_tensor(v):
                    del encrypted_dict[k]
            
            print(f"已处理 {len(encrypted_dict)} 个张量")
            return encrypted_dict
            
        except Exception as e:
            raise ValueError(f"加密失败: {str(e)}")
    
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
    def process_machine_codes(cls, machine_codes_str):
        """处理机器码列表
        Args:
            machine_codes_str: 多行机器码字符串
        Returns:
            list: 处理后的机器码列表
        """
        if not machine_codes_str.strip():
            raise ValueError("机器码不能为空")
            
        # 分割并清理机器码
        codes = [
            code.strip() 
            for code in machine_codes_str.split('\n')
            if code.strip()
        ]
        
        # 验证每个机器码
        valid_codes = []
        for code in codes:
            if len(code) == 32 and all(c in '0123456789abcdef' for c in code.lower()):
                valid_codes.append(code)
            else:
                print(f"警告: 忽略无效的机器码 {code}")
                
        if not valid_codes:
            raise ValueError("没有有效的机器码")
            
        return valid_codes
    
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