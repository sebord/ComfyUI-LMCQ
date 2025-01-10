# ComfyUI-LMCQ
**切换英文版: [English](README.md)**
## 介绍

ComfyUI小节点工具包，本工具包主要是更新一些实用的小节点，为comfyui生态做一份贡献，
PS：“LMCQ”是团队名称的简写


## 更新日志 2025-01-10 （全新的代码加密方案！）

为了进一步提升代码安全性，我们完全重构了加密系统：

### 新的加密方案
- ✓ 基于 AES-GCM 的高强度加密
- ✓ 动态密钥生成与管理
- ✓ 源代码级别的加密保护
- ✓ 跨平台兼容性支持

### 安全性提升
- 移除了可能存在安全隐患的 PyArmor 依赖
- 实现了更安全的内存数据处理
- 增强了对张量数据的保护
- 改进了机器码验证机制

新的加密方案不仅提供了更强的安全保护，还显著提升了跨平台兼容性和运行时性能。结合已有的多层保护机制，为模型、LoRA和工作流提供了更可靠的安全保障。

## 更新日志 2025-01-08 （白盒加密与安全增强！）

我们实现了一套复杂的白盒加密系统并增强了安全机制：

### 白盒加密
- 动态T-box和S-box生成
- 复杂的密钥扩展算法
- 多轮变换机制
- 内存保护机制

### 增强的安全特性
- ✓ 安全的密钥存储
- ✓ 反调试保护
- ✓ 内存篡改检测
- ✓ 运行时完整性验证

新的白盒加密实现使得即使获得完整代码也极难提取加密密钥。结合我们现有的多层保护方案，为您的模型和工作流提供了最先进的安全保护。



现在项目中安全节点代码全部经过多层保护方案高强度加密，很大程度地抬高了逆向工程师的破解难度，从而保障了模型的安全保障问题


## Image

1. LmcqImageSaver：主要对生成出来的图像文件提供水印和是否保存元数据信息功能
2. LmcqImageSaverTransit：功能上与LmcqImageSaver没有太大差别，唯一的区别就是可以将处理过后的图像文件发送到下一个节点
3. LmcqImageSaverWeb：在LmcqImageSaver基础上添加主动发送文件及prompt_id到指定接口地址（设计它的目的是为了不用WS去保持大量的长连接请求）

![img.png](img.png)

~~~
功能详解

filename_prefix：    文件名前缀
format：             文件格式，目前支持‘png、jpg、webp’三种
quality：            文件压缩率，数值越小，压缩率越高，对应的文件大小越小，如果要使用该功能请在文件格式中选择jpg格式
apply_watermark：    是否开启水印功能
watermark_text：     水印文本内容
watermark_size：     水印大小，默认15，最高70
watermark_position： 水印在图片当中的位置
enhance_brightness： 设置图片的明暗程度，数值越低，图片越暗
enhance_contrast：   设置图片的色彩饱和程度，数值越低，饱和度越低
save_metadata：      是否保存图片背后的工作流信息
enable_api_call：    是否开启接口请求，若开启，则会在工作流完成之后将文件及api当中的prompt_id发送到对应接口
api_url：            请求的接口地址

~~~
## flux

1. 由于lllyasviel大佬更新了flux的NF4版本，但comfyui当中没有对应的加载其模型的节点，常规的checkpointLoader无法适配该模型，所以设计该节点用于方便模型使用,使用方式跟常规checkpointLoader一样

![img_1.png](img_1.png)


## 更新日志 2024-08-20

Image系列功能新增
~~~
watermark_type：水印类型，默认文本，可选项：文本、图片

watermark_image：连接你要用于作为水印的图片

watermark_opacity：水印透明度，默认0.5，最大值为1
~~~

## 更新日志 2024-11-11
### Utils

1. LmcqInputValidator：用于验证输入值的类型，可以判断输入是纯数字还是字符串

~~~
功能详解

input_text：    需要验证的输入文本
check_type：    验证类型，可选项：
               - is_digit：判断是否为纯数字
               - is_string：判断是否为字符串（任何非纯数字的输入都被视为字符串）
~~~


## 更新日志 2024-12-12 （模型加密！！！）

### 模型加解密
![img_2.png](img_2.png)
### LmcqModelEncryption
~~~
功能讲解
model_name：选择你要加密的模型
key       ：加密密钥（自定义，用于后续解密的关键密码）
save_name ：加密后的模型名称
~~~
填写完毕之后点击执行，会在你的模型文件夹下生成两个文件，一个模型和一个后缀名为.meta的文件，meta文件记录你的加密签名及版本信息，记住一定要将两个文件放在同一个目录，否则加密后的模型无法解密

### LmcqModelDecryption
~~~
功能讲解
model_name：选择你要解密的模型
key       ：加密密钥（输入加密时设置的密钥信息）
save_name ：解密后的模型名称
~~~

## 更新日志 2024-12-18 （工作流保护！）

### 工作流加解密
![workflow_encryption.png](workflow_encryption.png)

### LmcqWorkflowEncryption
~~~
功能详解：
action:        选择加密或解密操作
password:      加解密密码
workflow_file: 选择要处理的工作流文件（可从根目录或插件的 workflows 文件夹中选择）
save_name:     保存文件的名称
~~~

该节点允许你对工作流文件进行加密保护，防止未经授权的访问。加密后的工作流文件需要使用正确的密码解密后才能使用。

使用方法：
1. 将工作流文件保存到以下任一位置：
   - ComfyUI根目录的 workflows 文件夹（显示为 "root/文件名"）
   - 插件目录的 workflows 文件夹（显示为 "plugin/文件名"）
2. 使用 encrypt 操作创建加密版本
3. 分享加密后的工作流文件
4. 接收者需要使用 decrypt 操作并输入正确的密码才能使用该工作流

注意：加密/解密后的文件会保存在源文件所在的同一文件夹中。

## （LoRA加密！）

### LoRA模型加解密
![lora_encryption.png](lora_encryption.png)

### LmcqLoraEncryption
~~~
功能讲解：
lora_name：选择要加密的LoRA模型
key：      加密密钥（自定义，用于后续解密的关键密码）
save_name：加密后的模型名称
~~~
执行后会在 loras/encrypted 文件夹下生成两个文件：加密后的模型和一个后缀为 .meta 的文件。meta 文件记录了加密签名和版本信息，这两个文件必须放在同一目录才能成功解密。

### LmcqLoraDecryption
~~~
功能讲解：
lora_name：选择要解密的LoRA模型
key：      加密密钥（输入加密时设置的密钥信息）
save_name：解密后的模型名称
~~~
解密后的LoRA模型会保存在 loras/decrypted 文件夹中。


## 更新日志 2024-12-21 （运行时保护系统！）


### 机器码与运行时保护
![runtime_protection.png](runtime_protection.png)

### LmcqGetMachineCode
用于生成基于硬件和系统信息的唯一机器码的工具节点。此机器码用于运行时保护系统中的授权验证。

### 运行时模型保护
~~~
LmcqRuntimeModelEncryption（运行时模型加密）:
- model_name:    选择要加密的模型
- key:          加密密钥
- save_name:    加密后的模型名称
- machine_codes: 授权机器码列表（每行一个）

LmcqRuntimeModelDecryption（运行时模型解密）:
- model_name:    选择加密的模型
- key:          解密密钥
~~~
提供实时模型加解密和特定机器授权功能。模型只能在授权的机器上加载。
PS: 加密模型在内存中进行加载，所以不会在本地保存完整模型，只能用于工作流当中，最大程度保护完整模型不被传播(只能使用LmcqRuntimeModelDecryption去加载加密模型，其余无效)

### 运行时LoRA保护
~~~
LmcqRuntimeLoraEncryption（运行时LoRA加密）:
- lora_name:     选择要加密的LoRA
- key:          加密密钥
- save_name:    加密后的LoRA名称
- machine_codes: 授权机器码列表

LmcqRuntimeLoraDecryption（运行时LoRA解密）:
- model:         输入模型
- clip:         输入CLIP
- lora_name:    选择加密的LoRA
- key:          解密密钥
- strength_model: 模型的LoRA强度
- strength_clip:  CLIP的LoRA强度
~~~
使用机器特定授权和实时加载功能来保护LoRA模型。
PS: 加密模型在内存中进行加载，所以不会在本地保存完整模型，只能用于工作流当中，最大程度保护完整模型不被传播(只能使用LmcqRuntimeLoraDecryption去加载加密模型，其余无效)

### 运行时工作流保护
~~~
LmcqRuntimeWorkflowEncryption（运行时工作流加密）:
- workflow_file: 选择要加密的工作流
- key:          加密密钥
- save_name:    加密后的工作流名称（.lcwf格式）
- machine_codes: 授权机器码列表

LmcqRuntimeWorkflowDecryption（运行时工作流解密）:
- workflow_file: 选择加密的工作流
- key:          解密密钥
- save_name:    解密后的工作流名称
~~~
通过机器特定授权保护工作流。加密的工作流以.lcwf格式保存，只能在授权机器上解密。

注意：运行时保护系统确保受保护的资源只能在特定授权的机器上使用，比单纯的密码保护提供更强的安全性。

## 2024-12-29 TODO（接下来的计划）

我们现在正在筹备的工作：
   研发一套完整的认证服务系统，专用于更高效提升ComfyUi安全节点功能安全性，所有节点的核心功能逻辑将由第三方认证服务系统提供，最大程度保障模型、工作流安全（并会提供更花样的玩法如：加密模型使用次数限制、加密模型使用时间限制、加密模型使用设备限制等），为创作者提供更安全的创作环境，敬请期待！！！


## 参与贡献!

Zebord