import os
import json
import base64
import datetime
import mimetypes
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont
from PIL.PngImagePlugin import PngInfo
import folder_paths
import requests
from server import PromptServer
import comfy.sd
from .nf4_model import OPS
import re

#------------Deepseek相关------------------
from .deepseek_util  import *
cpp=print
import torch
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoProcessor
from folder_paths import models_dir
from comfy import model_management, model_patcher
deep_model_folder_path = Path(models_dir) / 'deepseek'
deep_model_folder_path.mkdir(parents=True, exist_ok=True)

# 导入运行时保护节点
from .runtime.model_protection import (
    LmcqRuntimeModelEncryption,
    LmcqRuntimeModelDecryption
)
from .runtime.lora_protection import (
    LmcqRuntimeLoraEncryption,
    LmcqRuntimeLoraDecryption
)
from .runtime.workflow_protection import (
    LmcqRuntimeWorkflowEncryption,
    LmcqRuntimeWorkflowDecryption,
    LmcqGetMachineCode
)
from .runtime.code_protection import (
    LmcqCodeEncryption,
    LmcqCodeDecryptionLoader
)

# 基础节点类定义
class LmcqImageSaver:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"

    @classmethod
    def INPUT_TYPES(s):
        return {"required":
                    {"images": ("IMAGE",),
                     "filename_prefix": ("STRING", {"default": "LMCQ"}),
                     "format": (["png", "jpg", "webp"],),
                     "quality": ("INT", {"default": 95, "min": 1, "max": 100, "step": 1}),
                     "apply_watermark": ("BOOLEAN", {"default": False}),
                     "watermark_type": (["text", "image"],),
                     "watermark_text": ("STRING", {"default": ""}),
                     "watermark_size": ("INT", {"default": 15, "min": 0, "max": 80, "step": 1}),
                     "watermark_position": (
                         ["Bottom Right", "Bottom Left", "Top Right", "Top Left", "Center", "Left", "Right", "Top",
                          "Bottom"],),
                     "watermark_opacity": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.1}),
                     "enhance_brightness": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 2.0, "step": 0.1}),
                     "enhance_contrast": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 2.0, "step": 0.1}),
                     "save_metadata": ("BOOLEAN", {"default": True}),
                     },
                "optional":
                    {"watermark_image": ("IMAGE",)},
                "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
                }

    RETURN_TYPES = ()
    FUNCTION = "save_enhanced_image"
    OUTPUT_NODE = True
    CATEGORY = "Lmcq/Image"

    def save_enhanced_image(self, images, filename_prefix, format, quality, apply_watermark, watermark_type,
                            watermark_text, watermark_size, watermark_position, watermark_opacity,
                            enhance_brightness, enhance_contrast, save_metadata, prompt=None, extra_pnginfo=None,
                            watermark_image=None):
        results = []
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        for i, image in enumerate(images):
            img = Image.fromarray((image.squeeze().cpu().numpy() * 255).astype(np.uint8))

            if enhance_brightness != 1.0:
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(enhance_brightness)
            if enhance_contrast != 1.0:
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(enhance_contrast)

            if apply_watermark:
                if watermark_type == "text" and watermark_text:
                    self.add_text_watermark(img, watermark_text, watermark_size, watermark_position, watermark_opacity)
                elif watermark_type == "image" and watermark_image is not None:
                    self.add_image_watermark(img, watermark_image, watermark_size, watermark_position,
                                             watermark_opacity)

            metadata = None
            if save_metadata and format == "png":
                metadata = PngInfo()
                if prompt:
                    metadata.add_text("prompt", json.dumps(prompt))
                if extra_pnginfo:
                    for key, value in extra_pnginfo.items():
                        metadata.add_text(key, json.dumps(value))

            filename = f"{filename_prefix}_{timestamp}_{i}.{format}"
            filepath = os.path.join(self.output_dir, filename)

            if format == "png":
                img.save(filepath, format="PNG", pnginfo=metadata, compress_level=(100 - quality) // 10)
            elif format == "jpg":
                img.save(filepath, format="JPEG", quality=quality)
            elif format == "webp":
                img.save(filepath, format="WEBP", quality=quality)

            results.append({
                "filename": filename,
                "subfolder": "",
                "type": self.type
            })

        return {"ui": {"images": results}}

    def add_text_watermark(self, img, text, size, position, opacity):
        draw = ImageDraw.Draw(img)
        font = self.get_chinese_font(size)
        bbox = draw.textbbox((0, 0), text, font=font)
        textwidth, textheight = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y = self.get_watermark_position(img.size, (textwidth, textheight), position)
        watermark = Image.new('RGBA', img.size, (0, 0, 0, 0))
        watermark_draw = ImageDraw.Draw(watermark)
        watermark_draw.text((x, y), text, font=font, fill=(255, 255, 255, int(255 * opacity)))
        img.paste(watermark, (0, 0), watermark)

    def add_image_watermark(self, img, watermark_image, size, position, opacity):
        watermark = Image.fromarray((watermark_image.squeeze().cpu().numpy() * 255).astype(np.uint8))
        aspect_ratio = watermark.width / watermark.height
        new_width = int(img.width * size / 100)
        new_height = int(new_width / aspect_ratio)
        watermark = watermark.resize((new_width, new_height), Image.LANCZOS)
        x, y = self.get_watermark_position(img.size, watermark.size, position)
        watermark = watermark.convert('RGBA')
        watermark.putalpha(int(255 * opacity))
        img.paste(watermark, (x, y), watermark)

    def get_watermark_position(self, img_size, watermark_size, position):
        width, height = img_size
        w_width, w_height = watermark_size
        padding = 10
        if position == "Bottom Right":
            return width - w_width - padding, height - w_height - padding
        elif position == "Bottom Left":
            return padding, height - w_height - padding
        elif position == "Top Right":
            return width - w_width - padding, padding
        elif position == "Top Left":
            return padding, padding
        elif position == "Center":
            return (width - w_width) // 2, (height - w_height) // 2
        elif position == "Left":
            return padding, (height - w_height) // 2
        elif position == "Right":
            return width - w_width - padding, (height - w_height) // 2
        elif position == "Top":
            return (width - w_width) // 2, padding
        elif position == "Bottom":
            return (width - w_width) // 2, height - w_height - padding
        else:
            return width - w_width - padding, height - w_height - padding

    def get_chinese_font(self, size):
        chinese_fonts = [
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",  # Ubuntu
            "/System/Library/Fonts/PingFang.ttc",  # macOS
            "C:\\Windows\\Fonts\\msyh.ttc",  # Windows
            "/usr/share/fonts/truetype/arphic/uming.ttc",  # 其他 Linux
        ]

        for font_path in chinese_fonts:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except IOError:
                    continue

        print("警告：未找到支持中文的字体，将使用默认字体")
        return ImageFont.load_default()


class LmcqImageSaverTransit:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()  # 假设输出目录
        self.type = "output"

    @classmethod
    def INPUT_TYPES(s):
        return {"required":
                    {"images": ("IMAGE",),
                     "filename_prefix": ("STRING", {"default": "LMCQ"}),
                     "format": (["png", "jpg", "webp"],),
                     "quality": ("INT", {"default": 95, "min": 1, "max": 100, "step": 1}),
                     "apply_watermark": ("BOOLEAN", {"default": False}),
                     "watermark_type": (["text", "image"],),
                     "watermark_text": ("STRING", {"default": ""}),
                     "watermark_size": ("INT", {"default": 15, "min": 0, "max": 80, "step": 1}),
                     "watermark_position": (
                         ["Bottom Right", "Bottom Left", "Top Right", "Top Left", "Center", "Left", "Right", "Top",
                          "Bottom"],),
                     "watermark_opacity": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.1}),
                     "enhance_brightness": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 2.0, "step": 0.1}),
                     "enhance_contrast": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 2.0, "step": 0.1}),
                     "save_metadata": ("BOOLEAN", {"default": True}),
                     },
                "optional":
                    {"watermark_image": ("IMAGE",)},
                "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
                }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "save_enhanced_image"
    OUTPUT_NODE = True
    CATEGORY = "Lmcq/Image"

    def save_enhanced_image(self, images, filename_prefix, format, quality, apply_watermark, watermark_type,
                            watermark_text, watermark_size, watermark_position, watermark_opacity,
                            enhance_brightness, enhance_contrast, save_metadata, prompt=None, extra_pnginfo=None,
                            watermark_image=None):
        results = []
        output_images = []  # 存储处理后的图像
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        for i, image in enumerate(images):
            img = Image.fromarray((image.squeeze().cpu().numpy() * 255).astype(np.uint8))

            if enhance_brightness != 1.0:
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(enhance_brightness)
            if enhance_contrast != 1.0:
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(enhance_contrast)

            if apply_watermark:
                if watermark_type == "text" and watermark_text:
                    self.add_text_watermark(img, watermark_text, watermark_size, watermark_position, watermark_opacity)
                elif watermark_type == "image" and watermark_image is not None:
                    self.add_image_watermark(img, watermark_image, watermark_size, watermark_position,
                                             watermark_opacity)

            metadata = None
            if save_metadata and format == "png":
                metadata = PngInfo()
                if prompt:
                    metadata.add_text("prompt", json.dumps(prompt))
                if extra_pnginfo:
                    for key, value in extra_pnginfo.items():
                        metadata.add_text(key, json.dumps(value))

            filename = f"{filename_prefix}_{timestamp}_{i}.{format}"
            filepath = os.path.join(self.output_dir, filename)

            if format == "png":
                img.save(filepath, format="PNG", pnginfo=metadata, compress_level=(100 - quality) // 10)
            elif format == "jpg":
                img.save(filepath, format="JPEG", quality=quality)
            elif format == "webp":
                img.save(filepath, format="WEBP", quality=quality)

            results.append({
                "filename": filename,
                "subfolder": "",
                "type": self.type
            })
            # 添加到输出图像列表
            output_images.append(torch.from_numpy(np.array(img)).float() / 255.0)

        new_images = torch.stack(output_images)
        return (new_images,)

    def add_text_watermark(self, img, text, size, position, opacity):
        draw = ImageDraw.Draw(img)
        font = self.get_chinese_font(size)
        bbox = draw.textbbox((0, 0), text, font=font)
        textwidth, textheight = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y = self.get_watermark_position(img.size, (textwidth, textheight), position)
        watermark = Image.new('RGBA', img.size, (0, 0, 0, 0))
        watermark_draw = ImageDraw.Draw(watermark)
        watermark_draw.text((x, y), text, font=font, fill=(255, 255, 255, int(255 * opacity)))
        img.paste(watermark, (0, 0), watermark)

    def add_image_watermark(self, img, watermark_image, size, position, opacity):
        watermark = Image.fromarray((watermark_image.squeeze().cpu().numpy() * 255).astype(np.uint8))
        aspect_ratio = watermark.width / watermark.height
        new_width = int(img.width * size / 100)
        new_height = int(new_width / aspect_ratio)
        watermark = watermark.resize((new_width, new_height), Image.LANCZOS)
        x, y = self.get_watermark_position(img.size, watermark.size, position)
        watermark = watermark.convert('RGBA')
        watermark.putalpha(int(255 * opacity))
        img.paste(watermark, (x, y), watermark)

    def get_watermark_position(self, img_size, watermark_size, position):
        width, height = img_size
        w_width, w_height = watermark_size
        padding = 10
        if position == "Bottom Right":
            return width - w_width - padding, height - w_height - padding
        elif position == "Bottom Left":
            return padding, height - w_height - padding
        elif position == "Top Right":
            return width - w_width - padding, padding
        elif position == "Top Left":
            return padding, padding
        elif position == "Center":
            return (width - w_width) // 2, (height - w_height) // 2
        elif position == "Left":
            return padding, (height - w_height) // 2
        elif position == "Right":
            return width - w_width - padding, (height - w_height) // 2
        elif position == "Top":
            return (width - w_width) // 2, padding
        elif position == "Bottom":
            return (width - w_width) // 2, height - w_height - padding
        else:
            return width - w_width - padding, height - w_height - padding

    def get_chinese_font(self, size):
        chinese_fonts = [
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",  # Ubuntu
            "/System/Library/Fonts/PingFang.ttc",  # macOS
            "C:\\Windows\\Fonts\\msyh.ttc",  # Windows
            "/usr/share/fonts/truetype/arphic/uming.ttc",  # 其他 Linux
        ]

        for font_path in chinese_fonts:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except IOError:
                    continue

        print("警告：未找到支持中文的字体，将使用默认字体")
        return ImageFont.load_default()


class LmcqImageSaverWeb:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()  # 假设输出目录
        self.type = "output"
        self.enable_api_call = False  # 默认不开启接口调用
        self.api_url = ""  # 接口调用的地址
        self.server = PromptServer.instance  # Get the PromptServer instance

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "filename_prefix": ("STRING", {"default": "LMCQ"}),
                "format": (["png", "jpg", "webp"],),
                "quality": ("INT", {"default": 95, "min": 1, "max": 100, "step": 1}),
                "apply_watermark": ("BOOLEAN", {"default": False}),
                "watermark_type": (["text", "image"],),
                "watermark_text": ("STRING", {"default": ""}),
                "watermark_size": ("INT", {"default": 15, "min": 0, "max": 70, "step": 1}),
                "watermark_position": (
                    ["Bottom Right", "Bottom Left", "Top Right", "Top Left", "Center", "Left", "Right", "Top",
                     "Bottom"],),  # 新添加的选项
                "watermark_opacity": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.1}),
                "enhance_brightness": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 2.0, "step": 0.1}),
                "enhance_contrast": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 2.0, "step": 0.1}),
                "save_metadata": ("BOOLEAN", {"default": True}),
                "enable_api_call": ("BOOLEAN", {"default": False}),  # 是否开启接口调用
                "api_url": ("STRING", {"default": ""}),  # 接口调用的地址
            },
            "optional":
                {"watermark_image": ("IMAGE",)},
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ()
    FUNCTION = "save_enhanced_image"
    OUTPUT_NODE = True
    CATEGORY = "Lmcq/Image"

    def save_enhanced_image(self, images, filename_prefix, format, quality, apply_watermark, watermark_text,
                            watermark_type, watermark_opacity,
                            watermark_size, watermark_position, enhance_brightness, enhance_contrast, save_metadata,
                            enable_api_call, api_url,
                            prompt=None, extra_pnginfo=None, watermark_image=None):
        results = []
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        self.enable_api_call = enable_api_call  # 更新是否开启接口调用的状态
        self.api_url = api_url  # 更新接口调用的地址

        # Get the current prompt_id
        current_prompt_id = self.server.last_prompt_id

        for i, image in enumerate(images):
            img = Image.fromarray((image.squeeze().cpu().numpy() * 255).astype(np.uint8))

            # 应用图像增强
            if enhance_brightness != 1.0:
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(enhance_brightness)
            if enhance_contrast != 1.0:
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(enhance_contrast)

            # 加印
            if apply_watermark:
                if watermark_type == "text" and watermark_text:
                    self.add_text_watermark(img, watermark_text, watermark_size, watermark_position, watermark_opacity)
                elif watermark_type == "image" and watermark_image is not None:
                    self.add_image_watermark(img, watermark_image, watermark_size, watermark_position,
                                             watermark_opacity)

            # 准备元数据
            metadata = None
            if save_metadata and format == "png":
                metadata = PngInfo()
                if prompt:
                    metadata.add_text("prompt", json.dumps(prompt))
                if extra_pnginfo:
                    for key, value in extra_pnginfo.items():
                        metadata.add_text(key, json.dumps(value))

            # 保存图像
            filename = f"{filename_prefix}_{timestamp}_{i}.{format}"
            filepath = os.path.join(self.output_dir, filename)

            if format == "png":
                img.save(filepath, format="PNG", pnginfo=metadata, compress_level=(100 - quality) // 10)
            elif format == "jpg":
                img.save(filepath, format="JPEG", quality=quality)
            elif format == "webp":
                img.save(filepath, format="WEBP", quality=quality)

            results.append({
                "filename": filename,
                "subfolder": "",
                "type": self.type
            })

            # 果开启了口调用，则发送数据到接口
            if self.enable_api_call:
                self.send_to_api(filename, current_prompt_id)

        return {"ui": {"images": results}}

    def send_to_api(self, filename, prompt):
        filepath = os.path.join(self.output_dir, filename)

        # 获取文件的MIME类型
        content_type, _ = mimetypes.guess_type(filepath)
        if content_type is None:
            content_type = 'application/octet-stream'  # 默认二进制

        # 构建要发送的数据
        data = {
            "imageFilename": filename,
            "promptId": prompt
        }

        # 准备文件
        files = {
            'file': (filename, open(filepath, 'rb'), content_type)
        }

        try:
            response = requests.post(self.api_url, data=data, files=files)
            if response.status_code == 200:
                print(f"{filename} 及其处理结果已成功发送至接口地址。")
            else:
                print(f"发送请求失败，状态码: {response.status_code}")
        except Exception as e:
            print(f"发送请求时发生错误: {e}")
        finally:
            files['file'][1].close()

    def add_text_watermark(self, img, text, size, position, opacity):
        draw = ImageDraw.Draw(img)
        font = self.get_chinese_font(size)
        bbox = draw.textbbox((0, 0), text, font=font)
        textwidth, textheight = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y = self.get_watermark_position(img.size, (textwidth, textheight), position)
        watermark = Image.new('RGBA', img.size, (0, 0, 0, 0))
        watermark_draw = ImageDraw.Draw(watermark)
        watermark_draw.text((x, y), text, font=font, fill=(255, 255, 255, int(255 * opacity)))
        img.paste(watermark, (0, 0), watermark)

    def add_image_watermark(self, img, watermark_image, size, position, opacity):
        watermark = Image.fromarray((watermark_image.squeeze().cpu().numpy() * 255).astype(np.uint8))
        aspect_ratio = watermark.width / watermark.height
        new_width = int(img.width * size / 100)
        new_height = int(new_width / aspect_ratio)
        watermark = watermark.resize((new_width, new_height), Image.LANCZOS)
        x, y = self.get_watermark_position(img.size, watermark.size, position)
        watermark = watermark.convert('RGBA')
        watermark.putalpha(int(255 * opacity))
        img.paste(watermark, (x, y), watermark)

    def get_watermark_position(self, img_size, watermark_size, position):
        width, height = img_size
        w_width, w_height = watermark_size
        padding = 10
        if position == "Bottom Right":
            return width - w_width - padding, height - w_height - padding
        elif position == "Bottom Left":
            return padding, height - w_height - padding
        elif position == "Top Right":
            return width - w_width - padding, padding
        elif position == "Top Left":
            return padding, padding
        elif position == "Center":
            return (width - w_width) // 2, (height - w_height) // 2
        elif position == "Left":
            return padding, (height - w_height) // 2
        elif position == "Right":
            return width - w_width - padding, (height - w_height) // 2
        elif position == "Top":
            return (width - w_width) // 2, padding
        elif position == "Bottom":
            return (width - w_width) // 2, height - w_height - padding
        else:
            return width - w_width - padding, height - w_height - padding

    def get_chinese_font(self, size):
        chinese_fonts = [
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",  # Ubuntu
            "/System/Library/Fonts/PingFang.ttc",  # macOS
            "C:\\Windows\\Fonts\\msyh.ttc",  # Windows
            "/usr/share/fonts/truetype/arphic/uming.ttc",  # 其他 Linux
        ]

        for font_path in chinese_fonts:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except IOError:
                    continue

        print("警告：未找到支持中文的字体，将使用默认字体")
        return ImageFont.load_default()


class LmcqLoadFluxNF4Checkpoint:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"ckpt_name": (folder_paths.get_filename_list("checkpoints"),),
                             }}

    RETURN_TYPES = ("MODEL", "CLIP", "VAE")
    FUNCTION = "load_checkpoint"

    CATEGORY = "Lmcq/flux"

    def load_checkpoint(self, ckpt_name):
        ckpt_path = folder_paths.get_full_path("checkpoints", ckpt_name)
        out = comfy.sd.load_checkpoint_guess_config(ckpt_path, output_vae=True, output_clip=True,
                                                    embedding_directory=folder_paths.get_folder_paths("embeddings"),
                                                    model_options={"custom_operations": OPS})
        return out[:3]


class LmcqInputValidator:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "input_text": ("STRING", {"default": ""}),
                "check_type": (["is_digit", "is_string"],),  # 修改为判断数字或字符串
            }
        }

    RETURN_TYPES = ("BOOLEAN",)
    RETURN_NAMES = ("result",)
    FUNCTION = "validate_input"
    CATEGORY = "Lmcq/Utils"

    def validate_input(self, input_text, check_type):
        if not input_text:
            return (False,)

        if check_type == "is_digit":
            return (input_text.isdigit(),)
        else:  # is_string
            # 判断是否为字符串 - 只要不是纯数字就是字符串
            return (not input_text.isdigit(),)
        

class DeepModel:
    def __init__(self, model, patcher, tokenizer=None, processor=None):
        self.model = model
        self.tokenizer = tokenizer
        self.processor = processor
        self.patcher = patcher
        
        # hook modelClass.device setter
        def set_value(self, new_value):
            pass
        model.__class__.device = property(fget=model.__class__.device.fget, fset=set_value)
        


class LmcqDeepLoader:
    @classmethod
    def INPUT_TYPES(cls):
        model_lst = []
        for folder in deep_model_folder_path.iterdir():
            if folder.is_dir():
                config_file = folder / 'config.json'
                if config_file.is_file():
                    relative_path = str(folder.relative_to(deep_model_folder_path))
                    model_lst.append(relative_path)
        return {
            "required": {
                "model_name": (model_lst, {}),
            }
        }
        
    RETURN_TYPES = ("DEEP_MODEL", )
    RETURN_NAMES = ("model", )
    FUNCTION = "load_model"
    CATEGORY = "Lmcq/deepseek"

    def load_model(self, model_name):
        #offload_device = torch.device('cpu')
        offload_device = torch.device('cuda')
        load_device = model_management.get_torch_device()
        mymod=deep_model_folder_path / model_name
        model = AutoModelForCausalLM.from_pretrained(
            mymod,
            #deep_model_folder_path / model_name, 
            device_map=offload_device, 
            torch_dtype="auto", 
        )
        tokenizer = AutoTokenizer.from_pretrained(mymod)
        patcher = model_patcher.ModelPatcher(model, load_device=load_device, offload_device=offload_device)
        #patcher = model_patcher.ModelPatcher(model, load_device=load_device offload_device=NoneNone) #, offload_device=offload_device)
        #patcher = model_patcher.ModelPatcher(model, load_device=load_device offload_device=NoneNone) #, offload_device=offload_device)
    
        
        return (DeepModel(model, patcher, tokenizer=tokenizer), )

class LmcqDeepGen:

    @classmethod
    def INPUT_TYPES(cls):
        DEFAULT_INSTRUCT = ''
        return {
            "required": {
                "deep_model": ("DEEP_MODEL",),
                "system_prompt": ("STRING", {
                    "default": "", 
                    "placeholder": "在此定义deepseek前置规则",
                    "multiline": True
                }),
                "user_prompt": ("STRING", {"default": "", "multiline": True, "placeholder": "在此输入用户提示词"}),
                "seed": ("INT", {"default": 888, "min": 0, "max": 0xffffffffffffffff}),
                "max_tokens": ("INT", {"default": 500, "min": 0, "max": 0xffffffffffffffff}),
                "temperature": ("FLOAT", {"default": 1, "min": 0, "max": 2}),
                "top_k": ("INT", {"default": 50, "min": 0, "max": 101}),
                "top_p": ("FLOAT", {"default": 1, "min": 0, "max": 1}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("raw_output", "clean_output")
    FUNCTION = "deep_xgen"
    CATEGORY = "Lmcq/deepseek"


    def deep_xgen(self, deep_model, system_prompt, user_prompt, seed=0, temperature=1.0, max_tokens=500, top_k=50, top_p=1.0, **kwargs):
        set_seed(seed % 9999999)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt.format(**kwargs)},
        ]
        tokenizer = deep_model.tokenizer
        model = deep_model.model
        patcher = deep_model.patcher
        model_management.load_model_gpu(patcher)
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

        generated_ids = model.generate(
            **model_inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
        )
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]

        response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        def clean_think_tags(text):
            # 修改后的正则表达式，匹配从开头到第一个</think>之前的所有内容（包括</think>）
            cleaned = re.sub(r'^.*?</think>', '', text, flags=re.DOTALL)
            # 处理多余空行
            return re.sub(r'\n\s*\n', '\n', cleaned).strip()
        
        clean_response = clean_think_tags(response)
        
        return (response, clean_response)


# 节点映射
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
    "LmcqDeepLoader": LmcqDeepLoader,
    "LmcqDeepGen": LmcqDeepGen,
    "LmcqCodeEncryption": LmcqCodeEncryption,
    "LmcqCodeDecryptionLoader": LmcqCodeDecryptionLoader,
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
    "LmcqDeepLoader": "Lmcq DeepLoader",
    "LmcqDeepGen": "Lmcq DeepGen",
    "LmcqCodeEncryption": "Lmcq 代码加密保护",
    "LmcqCodeDecryptionLoader": "Lmcq 代码解密加载测试",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']