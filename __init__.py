# Project initialization
import sys
import os

# 添加当前目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 定义web目录，使ComfyUI能够加载JavaScript文件
WEB_DIRECTORY = os.path.join(os.path.dirname(os.path.realpath(__file__)), "dist")

# 导入 nf4_model 中的 OPS
from .nf4_model import OPS

# 导入加密后的节点
from .runtime.api_model_protection import LmcqAuthModelEncryption, LmcqAuthModelDecryption
from .runtime.api_lora_protection import LmcqAuthLoraEncryption, LmcqAuthLoraDecryption
from .runtime.api_workflow_protection import LmcqAuthWorkflowEncryption, LmcqAuthWorkflowDecryption
from .runtime.flux_protection import LmcqAuthFluxEncryption, LmcqAuthFluxDecryption
from .runtime.code_protection import LmcqCodeEncryption, LmcqCodeDecryptionLoader
# 导入新的群组节点保护
from .runtime.group_node_protection import LmcqGroupNodes

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
    "LmcqAuthFluxEncryption": LmcqAuthFluxEncryption,
    "LmcqAuthFluxDecryption": LmcqAuthFluxDecryption,
    "LmcqCodeEncryption": LmcqCodeEncryption,
    "LmcqCodeDecryptionLoader": LmcqCodeDecryptionLoader,
    "LmcqGroupNode": LmcqGroupNodes  # 添加新的群组节点
})

NODE_DISPLAY_NAME_MAPPINGS.update({
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
    "LmcqGroupNode": "Lmcq 加密节点组" # 添加新的群组节点显示名称
})

# 导出节点映射和WEB_DIRECTORY
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']