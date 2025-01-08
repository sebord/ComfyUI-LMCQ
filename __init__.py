# Project initialization
import sys
import os

def setup_runtime():
    """设置运行时环境"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 添加项目根目录
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # 检查是否是加密版本
    runtime_dir = os.path.join(current_dir, 'pyarmor_runtime_000000')
    is_encrypted = os.path.exists(runtime_dir)
    
    if is_encrypted:
        # 将运行时目录添加到 sys.path 的最前面
        if runtime_dir not in sys.path:
            sys.path.insert(0, runtime_dir)
            
    return current_dir, runtime_dir, is_encrypted

# 设置运行时环境
current_dir, runtime_dir, is_encrypted = setup_runtime()

# 导入 nf4_model 中的 OPS
from .nf4_model import OPS

try:
    if is_encrypted:
        # 如果是加密版本，先导入运行时
        import pyarmor_runtime_000000
        
        # 然后导入加密后的节点
        from .runtime.api_model_protection import LmcqAuthModelEncryption, LmcqAuthModelDecryption
        from .runtime.api_lora_protection import LmcqAuthLoraEncryption, LmcqAuthLoraDecryption
        from .runtime.api_workflow_protection import LmcqAuthWorkflowEncryption, LmcqAuthWorkflowDecryption
    else:
        # 非加密版本直接导入
        from .runtime.api_model_protection import LmcqAuthModelEncryption, LmcqAuthModelDecryption
        from .runtime.api_lora_protection import LmcqAuthLoraEncryption, LmcqAuthLoraDecryption
        from .runtime.api_workflow_protection import LmcqAuthWorkflowEncryption, LmcqAuthWorkflowDecryption
except ImportError as e:
    print(f"Error: Failed to import required modules")
    print(f"Current directory: {current_dir}")
    print(f"Runtime directory: {runtime_dir}")
    print(f"Is encrypted: {is_encrypted}")
    print(f"Python path: {sys.path}")
    print(f"Error details: {e}")
    raise

# 导入节点映射
from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

# 更新节点映射
NODE_CLASS_MAPPINGS.update({
    "LmcqAuthModelEncryption": LmcqAuthModelEncryption,
    "LmcqAuthModelDecryption": LmcqAuthModelDecryption,
    "LmcqAuthLoraEncryption": LmcqAuthLoraEncryption,
    "LmcqAuthLoraDecryption": LmcqAuthLoraDecryption,
    "LmcqAuthWorkflowEncryption": LmcqAuthWorkflowEncryption,
    "LmcqAuthWorkflowDecryption": LmcqAuthWorkflowDecryption,
})

NODE_DISPLAY_NAME_MAPPINGS.update({
    "LmcqAuthModelEncryption": "Lmcq Auth Model Encryption",
    "LmcqAuthModelDecryption": "Lmcq Auth Model Decryption",
    "LmcqAuthLoraEncryption": "Lmcq Auth LoRA Encryption",
    "LmcqAuthLoraDecryption": "Lmcq Auth LoRA Decryption",
    "LmcqAuthWorkflowEncryption": "Lmcq Auth Workflow Encryption",
    "LmcqAuthWorkflowDecryption": "Lmcq Auth Workflow Decryption",
})

# 导出节点映射
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']