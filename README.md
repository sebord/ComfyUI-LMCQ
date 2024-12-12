# ComfyUI-LMCQ
**Read this in other languages: [中文](README_CN.md).**

## Introduction

ComfyUI small node toolkit, this toolkit is mainly to update some practical small nodes, to make a contribution to the comfyui ecosystem,
PS: "LMCQ" is the abbreviation of the team name

## Function

Currently, there are two versions: flux and image

## image

1. LmcqImageSaver: mainly provides watermarks and metadata information for the generated image files

2. LmcqImageSaverTransit: There is not much difference in function from LmcqImageSaver, the only difference is that the processed image files can be sent to the next node

3. LmcqImageSaverWeb: Add active sending of files and prompt_id to the specified interface address based on LmcqImageSaver (the purpose of its design is to avoid WS to maintain a large number of long connection requests)

![img.png](img.png)

~~~
Function details

filename_prefix:        File name prefix
format:                 File format, currently supports 'png, jpg, webp'
quality:                File compression rate, the smaller the value, the higher the compression rate, the smaller the corresponding file size, if you want to use this function, please select jpg format in the file format
apply_watermark:        Whether to enable the watermark function
watermark_text:         Watermark text content
watermark_size:         Watermark size, default 15, maximum 70
watermark_position:     The position of the watermark in the image
enhance_brightness:     Set the brightness of the image, the lower the value, the darker the image
enhance_contrast:       Set the color saturation of the image, the lower the value, the lower the saturation
save_metadata:          Whether to save the workflow information behind the image
enable_api_call:        Whether to enable the interface request, if enabled, the prompt_id in the file and api will be sent to the corresponding interface after the workflow is completed
api_url:                The requested interface address

~~~
## flux

1. Since lllyasviel updated the NF4 version of flux, but there is no corresponding node in comfyui to load its model, the conventional checkpointLoader cannot adapt to the model, so this node is designed to facilitate the use of the model, and the usage is the same as the conventional checkpointLoader

![img_1.png](img_1.png)

## Update log 2024-08-20

Image series features added
~~~
watermark_type: watermark type, default text, options: text, image

watermark_image: connect the image you want to use as a watermark

watermark_opacity: watermark transparency, default 0.5, maximum value 1
~~~

## Update log 2024-12-12 (Model encryption!!!)

### Model encryption and decryption
![img_2.png](img_2.png)
### LmcqModelEncryption
~~~
Function explanation

model_name: Select the model you want to encrypt
key       : Encryption key (custom, key password for subsequent decryption)
save_name : Encrypted model name
~~~
After filling in, click Execute. Two files will be generated in your model folder, a model and a file with the suffix .meta. The meta file records your encryption signature and version information. Remember to put the two files in the same directory, otherwise the encrypted model cannot be decrypted

### LmcqModelDecryption
~~~
Function explanation

model_name: Select the model you want to decrypt
key       : Encryption key (enter the key information set during encryption)
save_name : Decrypted model name
~~~

## Contribute

zebord