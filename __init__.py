# Project initialization
import sys
import os

# 添加当前目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    import pyarmor_runtime_000000
except ImportError:
    print("Warning: pyarmor runtime not found, please install pyarmor")

# 导入 nf4_model 中的 OPS
from .nf4_model import OPS

# 导入加密后的节点
from .runtime.model_protection import LmcqRuntimeModelEncryption, LmcqRuntimeModelDecryption
from .runtime.lora_protection import LmcqRuntimeLoraEncryption, LmcqRuntimeLoraDecryption
from .runtime.workflow_protection import LmcqRuntimeWorkflowEncryption, LmcqRuntimeWorkflowDecryption, LmcqGetMachineCode
from .runtime.api_model_protection import LmcqAuthModelEncryption, LmcqAuthModelDecryption
from .runtime.api_lora_protection import LmcqAuthLoraEncryption, LmcqAuthLoraDecryption
from .runtime.api_workflow_protection import LmcqAuthWorkflowEncryption, LmcqAuthWorkflowDecryption

# 导入其他节点
from .nodes import (
    LmcqImageSaver,
    LmcqImageSaverTransit,
    LmcqImageSaverWeb,
    LmcqLoadFluxNF4Checkpoint,
    LmcqInputValidator
)

# 定义节点映射
NODE_CLASS_MAPPINGS = {
    "LmcqImageSaver": LmcqImageSaver,
    "LmcqImageSaverTransit": LmcqImageSaverTransit,
    "LmcqImageSaverWeb": LmcqImageSaverWeb,
    "LmcqLoadFluxNF4Checkpoint": LmcqLoadFluxNF4Checkpoint,
    "LmcqInputValidator": LmcqInputValidator,
    "LmcqRuntimeModelEncryption": LmcqRuntimeModelEncryption,
    "LmcqRuntimeModelDecryption": LmcqRuntimeModelDecryption,
    "LmcqRuntimeLoraEncryption": LmcqRuntimeLoraEncryption,
    "LmcqRuntimeLoraDecryption": LmcqRuntimeLoraDecryption,
    "LmcqRuntimeWorkflowEncryption": LmcqRuntimeWorkflowEncryption,
    "LmcqRuntimeWorkflowDecryption": LmcqRuntimeWorkflowDecryption,
    "LmcqGetMachineCode": LmcqGetMachineCode,
    "LmcqAuthModelEncryption": LmcqAuthModelEncryption,
    "LmcqAuthModelDecryption": LmcqAuthModelDecryption,
    "LmcqAuthLoraEncryption": LmcqAuthLoraEncryption,
    "LmcqAuthLoraDecryption": LmcqAuthLoraDecryption,
    "LmcqAuthWorkflowEncryption": LmcqAuthWorkflowEncryption,
    "LmcqAuthWorkflowDecryption": LmcqAuthWorkflowDecryption,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LmcqImageSaver": "Lmcq Image Saver",
    "LmcqImageSaverTransit": "Lmcq Image Saver Transit",
    "LmcqImageSaverWeb": "Lmcq Image Saver Web",
    "LmcqLoadFluxNF4Checkpoint": "Lmcq Load Flux NF4 Checkpoint",
    "LmcqInputValidator": "Lmcq Input Validator",
    "LmcqRuntimeModelEncryption": "Lmcq Runtime Model Encryption",
    "LmcqRuntimeModelDecryption": "Lmcq Runtime Model Decryption",
    "LmcqRuntimeLoraEncryption": "Lmcq Runtime Lora Encryption",
    "LmcqRuntimeLoraDecryption": "Lmcq Runtime Lora Decryption",
    "LmcqRuntimeWorkflowEncryption": "Lmcq Runtime Workflow Encryption",
    "LmcqRuntimeWorkflowDecryption": "Lmcq Runtime Workflow Decryption",
    "LmcqGetMachineCode": "Lmcq Get Machine Code",
    "LmcqAuthModelEncryption": "Lmcq Auth Model Encryption",
    "LmcqAuthModelDecryption": "Lmcq Auth Model Decryption",
    "LmcqAuthLoraEncryption": "Lmcq Auth LoRA Encryption",
    "LmcqAuthLoraDecryption": "Lmcq Auth LoRA Decryption",
    "LmcqAuthWorkflowEncryption": "Lmcq Auth Workflow Encryption",
    "LmcqAuthWorkflowDecryption": "Lmcq Auth Workflow Decryption",
}

# 导出节点映射
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
