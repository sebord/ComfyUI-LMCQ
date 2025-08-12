# Project initialization
import sys
import os

# 添加当前目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

"""
为前端扩展提供 WEB_DIRECTORY，同时尽可能避免因可选依赖缺失导致整个模块导入失败，
从而使 /extensions 枚举不到本插件的前端脚本。
"""

# 定义 web 目录（前端扩展静态资源）
WEB_DIRECTORY = os.path.join(os.path.dirname(os.path.realpath(__file__)), "dist")

# 可选导入：任何失败不应阻止模块加载（否则 WEB_DIRECTORY 不会被注册）
OPS = None
LmcqAuthModelEncryption = LmcqAuthModelDecryption = None
LmcqAuthLoraEncryption = LmcqAuthLoraDecryption = None
LmcqAuthWorkflowEncryption = LmcqAuthWorkflowDecryption = None
LmcqAuthFluxEncryption = LmcqAuthFluxDecryption = None
LmcqCodeEncryption = LmcqCodeDecryptionLoader = None
LmcqGroupNodes = None

try:
    from .nf4_model import OPS  # noqa: F401
except Exception as e:
    print(f"[ComfyUI-LMCQ-ZE] Optional import nf4_model failed: {e}")

try:
    from .runtime.api_model_protection import LmcqAuthModelEncryption, LmcqAuthModelDecryption  # noqa: F401
    from .runtime.api_lora_protection import LmcqAuthLoraEncryption, LmcqAuthLoraDecryption  # noqa: F401
    from .runtime.api_workflow_protection import LmcqAuthWorkflowEncryption, LmcqAuthWorkflowDecryption  # noqa: F401
    from .runtime.flux_protection import LmcqAuthFluxEncryption, LmcqAuthFluxDecryption  # noqa: F401
    from .runtime.code_protection import LmcqCodeEncryption, LmcqCodeDecryptionLoader  # noqa: F401
    from .runtime.group_node_protection import LmcqGroupNodes  # noqa: F401
except Exception as e:
    # 仅记录，不抛出，确保 WEB_DIRECTORY 能被注册，前端 JS 正常加载
    print(f"[ComfyUI-LMCQ-ZE] Optional runtime import failed: {e}")

# 导入节点映射（总是可用）
from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

# 更新节点映射
_maybe_nodes = {
    "LmcqAuthModelEncryption": LmcqAuthModelEncryption,
    "LmcqAuthModelDecryption": LmcqAuthModelDecryption,
    "LmcqAuthLoraEncryption": LmcqAuthLoraEncryption,
    "LmcqAuthLoraDecryption": LmcqAuthLoraDecryption,
    "LmcqAuthWorkflowEncryption": LmcqAuthWorkflowEncryption,
    "LmcqAuthWorkflowDecryption": LmcqAuthWorkflowDecryption,
    "LmcqAuthFluxEncryption": LmcqAuthFluxEncryption,
    "LmcqAuthFluxDecryption": LmcqAuthFluxDecryption,
    "LmcqCodeEncryption": LmcqCodeEncryption,
    "LmcqCodeDecryptionLoader": LmcqCodeDecryptionLoader,
    "LmcqGroupNode": LmcqGroupNodes,
}

# 仅注册成功导入的类，避免 None 进入映射
for _name, _cls in list(_maybe_nodes.items()):
    if _cls is not None:
        NODE_CLASS_MAPPINGS[_name] = _cls

_display_names = {
    "LmcqAuthModelEncryption": "Lmcq Auth Model Encryption",
    "LmcqAuthModelDecryption": "Lmcq Auth Model Decryption",
    "LmcqAuthLoraEncryption": "Lmcq Auth LoRA Encryption",
    "LmcqAuthLoraDecryption": "Lmcq Auth LoRA Decryption",
    "LmcqAuthWorkflowEncryption": "Lmcq Auth Workflow Encryption",
    "LmcqAuthWorkflowDecryption": "Lmcq Auth Workflow Decryption",
    "LmcqAuthFluxEncryption": "Lmcq Auth Flux Model Encryption (API)",
    "LmcqAuthFluxDecryption": "Lmcq Auth Flux Model Decryption (API)",
    "LmcqCodeEncryption": "Lmcq 代码加密保护",
    "LmcqCodeDecryptionLoader": "Lmcq 代码解密加载测试",
    "LmcqGroupNode": "Lmcq 加密节点组",
}

for _name, _title in list(_display_names.items()):
    if _name in NODE_CLASS_MAPPINGS:
        NODE_DISPLAY_NAME_MAPPINGS[_name] = _title

# 导出节点映射和WEB_DIRECTORY
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']