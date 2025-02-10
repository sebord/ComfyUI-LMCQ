
import os
import sys
import importlib
import types
from pathlib import Path

# 尝试导入加密库
try:
    from Crypto.Cipher import AES
except ImportError:
    try:
        from crypto.Cipher import AES
    except ImportError:
        try:
            from Cryptodome.Cipher import AES
        except ImportError:
            raise ImportError(
                "未找到加密库。请安装 pycryptodome：\n"
                "pip install pycryptodome\n"
                "或\n"
                "pip install pycrypto"
            )

# 导出节点映射
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

class EncryptedLoader:
    # 加密密钥
    KEY = b'\x10\t\x90%\x17"\x9b\xdb\xb0!\x0e\x0fXc\xe3\xbc\x9bT\x01o\x03\xe4\xdek\x83K1\x98^\xde6w'
    
    def __init__(self, spec):
        self.spec = spec
    
    def create_module(self, spec):
        """创建一个新的模块对象"""
        return None  # 使用默认的模块创建
        
    def exec_module(self, module):
        """执行模块的代码"""
        try:
            # 读取加密文件
            with open(self.spec.origin, 'rb') as f:
                encrypted_data = f.read()
                
            # 验证格式
            if not encrypted_data.startswith(b'PYE1'):
                raise ImportError("无效的加密文件格式")
                
            # 提取加密数据
            nonce = encrypted_data[4:20]
            tag = encrypted_data[20:36]
            ciphertext = encrypted_data[36:]
            
            # 解密
            cipher = AES.new(self.KEY, AES.MODE_GCM, nonce)
            try:
                source_bytes = cipher.decrypt_and_verify(ciphertext, tag)
                source_code = source_bytes.decode('utf-8')
                
                # 编译源代码
                try:
                    code = compile(
                        source_code,
                        self.spec.origin,
                        'exec',
                        dont_inherit=True,
                        optimize=0
                    )
                except Exception as compile_error:
                    raise ImportError(f"编译代码失败: {str(compile_error)}")
                
                # 设置模块属性
                module.__file__ = self.spec.origin
                module.__package__ = '.'.join(self.spec.name.split('.')[:-1])
                module.__loader__ = self
                module.__spec__ = self.spec
                
                # 执行代码
                try:
                    exec(code, module.__dict__)
                except Exception as exec_error:
                    raise ImportError(f"执行代码失败: {str(exec_error)}")
                
            except Exception as decrypt_error:
                python_version = sys.version_info
                raise ImportError(
                    f"解密失败 (Python {python_version.major}.{python_version.minor}.{python_version.micro}): "
                    f"{str(decrypt_error)}"
                )
                
        except Exception as load_error:
            raise ImportError(f"加载失败: {str(load_error)}")

def install_loader():
    """安装加密文件加载器"""
    class EncryptedFinder:
        def find_spec(self, fullname, path, target=None):
            if fullname.startswith(__package__ + '.runtime.'):
                modname = fullname.split('.')[-1]
                location = str(Path(__file__).parent / 'runtime' / (modname + '.pye'))
                if os.path.exists(location):
                    # 创建模块规范
                    loader = EncryptedLoader(None)  # 临时创建加载器
                    spec = importlib.machinery.ModuleSpec(
                        fullname,
                        loader,
                        origin=location,
                        is_package=False
                    )
                    loader.spec = spec  # 更新加载器的spec
                    return spec
            return None
    
    # 注册加载器
    sys.meta_path.insert(0, EncryptedFinder())

# 安装加载器
install_loader()

# 导入所有节点
def init_nodes():
    from .nodes import NODE_CLASS_MAPPINGS as ncm
    from .nodes import NODE_DISPLAY_NAME_MAPPINGS as ndm
    globals()['NODE_CLASS_MAPPINGS'].update(ncm)
    globals()['NODE_DISPLAY_NAME_MAPPINGS'].update(ndm)

init_nodes()
