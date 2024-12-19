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
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from .protection_utils import ModelProtector

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 Image Plus Nodes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""


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

            # 果开启了接口调用，则发送数据到接口
            if self.enable_api_call:
                self.send_to_api(filename, current_prompt_id)

        return {"ui": {"images": results}}

    def send_to_api(self, filename, prompt):
        filepath = os.path.join(self.output_dir, filename)

        # 获取文件的MIME类型
        content_type, _ = mimetypes.guess_type(filepath)
        if content_type is None:
            content_type = 'application/octet-stream'  # 默认二进制流

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
                print(f"{filename} 及其处理果已成功发送至接口地址。")
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


"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 Flux Nodes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

import torch
import bitsandbytes as bnb
from bitsandbytes.nn.modules import Params4bit, QuantState


def functional_linear_4bits(x, weight, bias):
    out = bnb.matmul_4bit(x, weight.t(), bias=bias, quant_state=weight.quant_state)
    out = out.to(x)
    return out


def copy_quant_state(state: QuantState, device: torch.device = None) -> QuantState:
    if state is None:
        return None

    device = device or state.absmax.device

    state2 = (
        QuantState(
            absmax=state.state2.absmax.to(device),
            shape=state.state2.shape,
            code=state.state2.code.to(device),
            blocksize=state.state2.blocksize,
            quant_type=state.state2.quant_type,
            dtype=state.state2.dtype,
        )
        if state.nested
        else None
    )

    return QuantState(
        absmax=state.absmax.to(device),
        shape=state.shape,
        code=state.code.to(device),
        blocksize=state.blocksize,
        quant_type=state.quant_type,
        dtype=state.dtype,
        offset=state.offset.to(device) if state.nested else None,
        state2=state2,
    )


class ForgeParams4bit(Params4bit):
    def to(self, *args, **kwargs):
        device, dtype, non_blocking, convert_to_format = torch._C._nn._parse_to(*args, **kwargs)
        if device is not None and device.type == "cuda" and not self.bnb_quantized:
            return self._quantize(device)
        else:
            n = ForgeParams4bit(
                torch.nn.Parameter.to(self, device=device, dtype=dtype, non_blocking=non_blocking),
                requires_grad=self.requires_grad,
                quant_state=copy_quant_state(self.quant_state, device),
                blocksize=self.blocksize,
                compress_statistics=self.compress_statistics,
                quant_type=self.quant_type,
                quant_storage=self.quant_storage,
                bnb_quantized=self.bnb_quantized,
                module=self.module
            )
            self.module.quant_state = n.quant_state
            self.data = n.data
            self.quant_state = n.quant_state
            return n


class ForgeLoader4Bit(torch.nn.Module):
    def __init__(self, *, device, dtype, quant_type, **kwargs):
        super().__init__()
        self.dummy = torch.nn.Parameter(torch.empty(1, device=device, dtype=dtype))
        self.weight = None
        self.quant_state = None
        self.bias = None
        self.quant_type = quant_type

    def _save_to_state_dict(self, destination, prefix, keep_vars):
        super()._save_to_state_dict(destination, prefix, keep_vars)
        quant_state = getattr(self.weight, "quant_state", None)
        if quant_state is not None:
            for k, v in quant_state.as_dict(packed=True).items():
                destination[prefix + "weight." + k] = v if keep_vars else v.detach()
        return

    def _load_from_state_dict(self, state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys,
                              error_msgs):
        quant_state_keys = {k[len(prefix + "weight."):] for k in state_dict.keys() if k.startswith(prefix + "weight.")}

        if any('bitsandbytes' in k for k in quant_state_keys):
            quant_state_dict = {k: state_dict[prefix + "weight." + k] for k in quant_state_keys}

            self.weight = ForgeParams4bit.from_prequantized(
                data=state_dict[prefix + 'weight'],
                quantized_stats=quant_state_dict,
                requires_grad=False,
                device=self.dummy.device,
                module=self
            )
            self.quant_state = self.weight.quant_state

            if prefix + 'bias' in state_dict:
                self.bias = torch.nn.Parameter(state_dict[prefix + 'bias'].to(self.dummy))

            del self.dummy
        elif hasattr(self, 'dummy'):
            if prefix + 'weight' in state_dict:
                self.weight = ForgeParams4bit(
                    state_dict[prefix + 'weight'].to(self.dummy),
                    requires_grad=False,
                    compress_statistics=True,
                    quant_type=self.quant_type,
                    quant_storage=torch.uint8,
                    module=self,
                )
                self.quant_state = self.weight.quant_state

            if prefix + 'bias' in state_dict:
                self.bias = torch.nn.Parameter(state_dict[prefix + 'bias'].to(self.dummy))

            del self.dummy
        else:
            super()._load_from_state_dict(state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys,
                                          error_msgs)


# Global variables for device and dtype management
current_device = None
current_dtype = None
current_manual_cast_enabled = False
current_bnb_dtype = None

# You may need to import comfy.ops or define it here
import comfy.ops


class OPS(comfy.ops.manual_cast):
    class Linear(ForgeLoader4Bit):
        def __init__(self, *args, device=None, dtype=None, **kwargs):
            super().__init__(device=device, dtype=dtype, quant_type=current_bnb_dtype)
            self.parameters_manual_cast = current_manual_cast_enabled

        def forward(self, x):
            self.weight.quant_state = self.quant_state

            if self.bias is not None and self.bias.dtype != x.dtype:
                self.bias.data = self.bias.data.to(x.dtype)

            if not self.parameters_manual_cast:
                return functional_linear_4bits(x, self.weight, self.bias)
            elif not self.weight.bnb_quantized:
                assert x.device.type == 'cuda', 'BNB Must Use CUDA as Computation Device!'
                layer_original_device = self.weight.device
                self.weight = self.weight._quantize(x.device)
                bias = self.bias.to(x.device) if self.bias is not None else None
                out = functional_linear_4bits(x, self.weight, bias)
                self.weight = self.weight.to(layer_original_device)
                return out
            else:
                weight, bias, signal = weights_manual_cast(self, x, skip_weight_dtype=True, skip_bias_dtype=True)
                with main_stream_worker(weight, bias, signal):
                    return functional_linear_4bits(x, weight, bias)


import folder_paths
import comfy.sd


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


# 节点映射保持不变
NODE_CLASS_MAPPINGS = {
    "LmcqImageSaver": LmcqImageSaver,
    "LmcqImageSaverTransit": LmcqImageSaverTransit,
    "LmcqImageSaverWeb": LmcqImageSaverWeb,
    "LmcqLoadFluxNF4Checkpoint": LmcqLoadFluxNF4Checkpoint
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LmcqImageSaver": "Lmcq Image Saver",
    "LmcqImageSaverTransit": "Lmcq Image Saver Transit",
    "LmcqImageSaverWeb": "Lmcq Image Saver Web",
    "LmcqLoadFluxNF4Checkpoint": "Lmcq Load Flux NF4 Checkpoint"
}


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
            # 判断是否为字符串 - 只要不是纯数字就为是字符串
            return (not input_text.isdigit(),)


# 在 NODE_CLASS_MAPPINGS 字典中添加新节点
NODE_CLASS_MAPPINGS.update({
    "LmcqInputValidator": LmcqInputValidator
})

# 在 NODE_DISPLAY_NAME_MAPPINGS 字典中添加显示名称
NODE_DISPLAY_NAME_MAPPINGS.update({
    "LmcqInputValidator": "Lmcq Input Validator"
})

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 ModelEncryptionNode 模型加密、解密
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""


class LmcqModelEncryption:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model_name": (folder_paths.get_filename_list("checkpoints"),),
                "key": ("STRING", {"default": ""}),
                "save_name": ("STRING", {"default": "encrypted_model"})
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "encrypt_model"
    OUTPUT_NODE = True
    CATEGORY = "Lmcq/model_protection"

    def encrypt_model(self, model_name, key, save_name):
        if not key:
            raise ValueError("Encryption key cannot be empty")

        # 获取模型路径
        model_path = folder_paths.get_full_path("checkpoints", model_name)
        if not model_path:
            raise ValueError(f"Model {model_name} not found")

        # 构建保存路径
        save_dir = os.path.join(os.path.dirname(model_path), "encrypted")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, f"{save_name}.safetensors")

        # 加密模型
        protector = ModelProtector()
        protector.encrypt(model_path, save_path, key)

        print(f"Model encrypted successfully: {save_path}")
        return {}


class LmcqModelDecryption:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model_name": (folder_paths.get_filename_list("checkpoints"),),
                "key": ("STRING", {"default": ""}),
                "save_name": ("STRING", {"default": "decrypted_model"})
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "decrypt_model"
    OUTPUT_NODE = True
    CATEGORY = "Lmcq/model_protection"

    def decrypt_model(self, model_name, key, save_name):
        if not key:
            raise ValueError("Decryption key cannot be empty")

        # 获取模型路径
        model_path = folder_paths.get_full_path("checkpoints", model_name)
        if not model_path:
            raise ValueError(f"Model {model_name} not found")

        # 构建保存路径
        save_dir = os.path.join(os.path.dirname(model_path), "decrypted")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, f"{save_name}.safetensors")

        # 解密模型
        protector = ModelProtector()
        protector.decrypt(model_path, save_path, key)

        print(f"Model decrypted successfully: {save_path}")
        return {}


# 注册节点
NODE_CLASS_MAPPINGS.update({
    "LmcqModelEncryption": LmcqModelEncryption,
    "LmcqModelDecryption": LmcqModelDecryption
})

NODE_DISPLAY_NAME_MAPPINGS.update({
    "LmcqModelEncryption": "Lmcq Model Encryption",
    "LmcqModelDecryption": "Lmcq Model Decryption"
})


"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 LmcqWorkflowEncryption 工作流加解密
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

class LmcqWorkflowEncryption:
    @classmethod
    def INPUT_TYPES(s):
        import os
        import folder_paths
        import sys
        
        # 获取 ComfyUI 根目录的 workflows 文件夹
        root_workflow_dir = os.path.join(os.path.dirname(folder_paths.base_path), "workflows")
        if not os.path.exists(root_workflow_dir):
            os.makedirs(root_workflow_dir)
        
        # 获取插件目录的 workflows 文件夹
        current_file_path = os.path.abspath(__file__)
        plugin_dir = os.path.dirname(current_file_path)
        plugin_workflow_dir = os.path.join(plugin_dir, "workflows")
        if not os.path.exists(plugin_workflow_dir):
            os.makedirs(plugin_workflow_dir)
        
        # 获取两个目录中的所有 json 文件
        root_workflow_files = [f for f in os.listdir(root_workflow_dir) if f.endswith('.json')]
        plugin_workflow_files = [f for f in os.listdir(plugin_workflow_dir) if f.endswith('.json')]
        
        # 合并文件列表，添加目录前缀以区分
        workflow_files = (
            [f"root/{f}" for f in root_workflow_files] + 
            [f"plugin/{f}" for f in plugin_workflow_files]
        )
        
        if not workflow_files:
            workflow_files = [""]
            
        return {
            "required": {
                "action": (["encrypt", "decrypt"],),
                "password": ("STRING", {"default": "", "multiline": False}),
                "workflow_file": (workflow_files,),
                "save_name": ("STRING", {"default": "encrypted_workflow", "multiline": False}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "process_workflow"
    OUTPUT_NODE = True
    CATEGORY = "Lmcq/Utils"

    def process_workflow(self, action, password, workflow_file, save_name):
        if not password:
            raise ValueError("密码不能为空")

        try:
            import os
            import json
            import folder_paths
            
            # 获取当前文件路径
            current_file_path = os.path.abspath(__file__)
            plugin_dir = os.path.dirname(current_file_path)
            
            # 根据文件路径前缀确定实际文件位置
            if workflow_file.startswith("root/"):
                workflow_dir = os.path.join(os.path.dirname(folder_paths.base_path), "workflows")
                actual_workflow_file = workflow_file[5:]  # 移除 "root/" 前缀
            elif workflow_file.startswith("plugin/"):
                workflow_dir = os.path.join(plugin_dir, "workflows")
                actual_workflow_file = workflow_file[7:]  # 移除 "plugin/" 前缀
            else:
                raise ValueError("无效的工作流文件路径")
                
            workflow_path = os.path.join(workflow_dir, actual_workflow_file)
            if not os.path.exists(workflow_path):
                raise ValueError(f"工作流文件不存在: {actual_workflow_file}")
                
            # 保存到与源文件相同的目录
            save_path = os.path.join(workflow_dir, f"{save_name}.json")
            
            def get_key(password, salt=None):
                if salt is None:
                    salt = os.urandom(16)
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
                return key, salt

            if action == "encrypt":
                try:
                    with open(workflow_path, 'r', encoding='utf-8') as f:
                        workflow_data = f.read()
                except Exception as e:
                    raise ValueError(f"读取工作流文件失败: {str(e)}")

                try:
                    key, salt = get_key(password)
                    fernet = Fernet(key)
                    encrypted_data = fernet.encrypt(workflow_data.encode())
                except Exception as e:
                    raise ValueError(f"加密过程失败: {str(e)}")

                try:
                    final_data = {
                        "salt": base64.b64encode(salt).decode(),
                        "data": base64.b64encode(encrypted_data).decode(),
                        "type": "encrypted_workflow"
                    }
                    with open(save_path, 'w', encoding='utf-8') as f:
                        json.dump(final_data, f)
                except Exception as e:
                    raise ValueError(f"保存加密文件失败: {str(e)}")

                print(f"工作流已加密并保存到: {save_path}")
                return {}

            elif action == "decrypt":
                try:
                    with open(workflow_path, 'r', encoding='utf-8') as f:
                        encrypted_data = json.load(f)
                except Exception as e:
                    raise ValueError(f"读取加密文件失败: {str(e)}")

                if encrypted_data.get("type") != "encrypted_workflow":
                    raise ValueError("不是有效的加密工作流文件")

                try:
                    salt = base64.b64decode(encrypted_data["salt"])
                    data = base64.b64decode(encrypted_data["data"])

                    key, _ = get_key(password, salt)
                    fernet = Fernet(key)
                    decrypted_data = fernet.decrypt(data).decode()
                except Exception as e:
                    raise ValueError("密码错误或文件已损坏")

                try:
                    with open(save_path, 'w', encoding='utf-8') as f:
                        f.write(decrypted_data)
                except Exception as e:
                    raise ValueError(f"保存解密文件失败: {str(e)}")

                print(f"工作流已解密并保存到: {save_path}")
                return {}

        except Exception as e:
            import traceback
            print(f"错误详情:\n{traceback.format_exc()}")
            raise ValueError(str(e))

# 注册工作流加密节点
NODE_CLASS_MAPPINGS.update({
    "LmcqWorkflowEncryption": LmcqWorkflowEncryption
})

NODE_DISPLAY_NAME_MAPPINGS.update({
    "LmcqWorkflowEncryption": "Lmcq Workflow Encryption"
})

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 LoraEncryptionNode Lora模型加密、解密
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

class LmcqLoraEncryption:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "lora_name": (folder_paths.get_filename_list("loras"),),  # 从loras文件夹获取文件列表
                "key": ("STRING", {"default": ""}),
                "save_name": ("STRING", {"default": "encrypted_lora"})
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "encrypt_lora"
    OUTPUT_NODE = True
    CATEGORY = "Lmcq/lora_protection"

    def encrypt_lora(self, lora_name, key, save_name):
        if not key:
            raise ValueError("加密密钥不能为空")

        # 获取LoRA模型路径
        lora_path = folder_paths.get_full_path("loras", lora_name)
        if not lora_path:
            raise ValueError(f"LoRA模型 {lora_name} 未找到")

        # 构建保存路径
        save_dir = os.path.join(os.path.dirname(lora_path), "encrypted")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, f"{save_name}.safetensors")

        # 加密LoRA模型
        protector = LoraProtector()
        protector.encrypt(lora_path, save_path, key)

        print(f"LoRA模型加密成功: {save_path}")
        return {}


class LmcqLoraDecryption:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "lora_name": (folder_paths.get_filename_list("loras"),),
                "key": ("STRING", {"default": ""}),
                "save_name": ("STRING", {"default": "decrypted_lora"})
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "decrypt_lora"
    OUTPUT_NODE = True
    CATEGORY = "Lmcq/lora_protection"

    def decrypt_lora(self, lora_name, key, save_name):
        if not key:
            raise ValueError("解密密钥不能为空")

        # 获取LoRA模型路径
        lora_path = folder_paths.get_full_path("loras", lora_name)
        if not lora_path:
            raise ValueError(f"LoRA模型 {lora_name} 未找到")

        # 构建保存路径
        save_dir = os.path.join(os.path.dirname(lora_path), "decrypted")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, f"{save_name}.safetensors")

        # 解密LoRA模型
        protector = LoraProtector()
        protector.decrypt(lora_path, save_path, key)

        print(f"LoRA模型解密成功: {save_path}")
        return {}


class LoraProtector:
    def __init__(self):
        self.version = "1.0.0"
        self.meta_extension = ".meta"

    def encrypt(self, input_path, output_path, key):
        try:
            # 读取LoRA模型
            with open(input_path, 'rb') as f:
                model_data = f.read()

            # 生成加密密钥
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            encryption_key = base64.urlsafe_b64encode(kdf.derive(key.encode()))
            
            # 加密模型数据
            fernet = Fernet(encryption_key)
            encrypted_data = fernet.encrypt(model_data)

            # 保存加密后的模型
            with open(output_path, 'wb') as f:
                f.write(encrypted_data)

            # 保存元数据
            meta_data = {
                "version": self.version,
                "salt": base64.b64encode(salt).decode(),
                "type": "encrypted_lora"
            }
            
            meta_path = output_path + self.meta_extension
            with open(meta_path, 'w') as f:
                json.dump(meta_data, f)

        except Exception as e:
            raise ValueError(f"LoRA模型加密失败: {str(e)}")

    def decrypt(self, input_path, output_path, key):
        try:
            # 读取元数据
            meta_path = input_path + self.meta_extension
            if not os.path.exists(meta_path):
                raise ValueError("未找到加密元数据文件")

            with open(meta_path, 'r') as f:
                meta_data = json.load(f)

            if meta_data.get("type") != "encrypted_lora":
                raise ValueError("无效的LoRA加密文件")

            # 读取加密的模型数据
            with open(input_path, 'rb') as f:
                encrypted_data = f.read()

            # 重建解密密钥
            salt = base64.b64decode(meta_data["salt"])
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            decryption_key = base64.urlsafe_b64encode(kdf.derive(key.encode()))

            # 解密模型数据
            fernet = Fernet(decryption_key)
            decrypted_data = fernet.decrypt(encrypted_data)

            # 保存解密后的模型
            with open(output_path, 'wb') as f:
                f.write(decrypted_data)

        except Exception as e:
            raise ValueError(f"LoRA模型解密失败: {str(e)}")


# 注册节点
NODE_CLASS_MAPPINGS.update({
    "LmcqLoraEncryption": LmcqLoraEncryption,
    "LmcqLoraDecryption": LmcqLoraDecryption
})

NODE_DISPLAY_NAME_MAPPINGS.update({
    "LmcqLoraEncryption": "Lmcq Lora Encryption",
    "LmcqLoraDecryption": "Lmcq Lora Decryption"
})