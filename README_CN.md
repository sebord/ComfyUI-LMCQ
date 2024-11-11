# ComfyUI-LMCQ
**切换英文版: [English](README.md)**
## 介绍

ComfyUI小节点工具包，本工具包主要是更新一些实用的小节点，为comfyui生态做一份贡献，
PS：“LMCQ”是团队名称的简写

## 功能

当前主要有flux、image两个版本组成

## image

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

## 参与贡献

zebord