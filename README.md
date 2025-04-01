# ComfyUI-LMCQ
**Read this in other languages: [中文](README_CN.md).**

## Introduction

ComfyUI small node toolkit, this toolkit is mainly to update some practical small nodes, to make a contribution to the comfyui ecosystem,
PS: "LMCQ" is the abbreviation of the team name

## Update Log 2025-03-04 (Authentication Server Encryption System!)

We have launched a new authentication server encryption system that provides stronger and more flexible protection mechanisms for model creators:

### Authentication Server Encryption System
- ✓ HTTP-based Authentication Server Verification
- ✓ Dynamic Key Distribution Mechanism
- ✓ Real-time Authorization Validation
- ✓ Online Management Platform

### Key Features
1. **Model Usage Management**
   - Dynamically adjust authorized machine codes
   - Flexible model usage period settings
   - Customizable usage count limits
   - Real-time usage statistics

2. **Online Management Platform**
   - URL: https://modelkey.cn/#/login
   - One-click management of all encrypted models
   - Real-time model usage monitoring
   - Quick authorization updates

3. **Supported Model Types**
   - Checkpoint Model Encryption (LmcqAuthModelEncryption/LmcqAuthModelDecryption)
   - LoRA Model Encryption (LmcqAuthLoraEncryption/LmcqAuthLoraDecryption)
   - Workflow Encryption (LmcqAuthWorkflowEncryption/LmcqAuthWorkflowDecryption)
   - Flux Model Encryption (LmcqAuthFluxEncryption/LmcqAuthFluxDecryption)

4. **Security Features**
   - Real-time Machine Code Validation
   - Timestamp Anti-replay Protection
   - Encrypted Communication Protection

### Usage Process
1. Register an account on the authentication server
2. Obtain creator key (auth_key) and key secret (auth_secret)
3. Configure key information in auth_key.json
4. Use corresponding encryption nodes for model encryption
5. Log in to the management platform for permission management

### Important Notes
- Keep the key information in auth_key.json secure
- Regularly change keys to enhance security
- Update authorization information through the management platform promptly

## Update Log 2025-02-10 (DeepSeek model integration!)

### Deepseek series nodes
![deepseek_nodes.png](deepseek_nodes.png) <!-- You need to add a screenshot and replace the actual file name -->

#### LmcqDeepLoader
~~~text
Function details:
model_name: Select the locally downloaded Deepseek large language model (the default model is read in the /models/deepseek/ directory)
~~~
Model download address:
1B model: https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-1B/tree/main
7B model: https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-7B/tree/main
14B model: https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B/tree/main
32B model: https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B/tree/main
70B model: https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Llama-70B/tree/main

Please download all the corresponding files for each model, use its name as the folder name, put all the files into the folder, and put it in the /models/deepseek/ directory: such as /models/deepseek/DeepSeek-R1-Distill-Qwen-7B/

#### LmcqDeepGen
~~~text
Function details:
system_prompt: system-level command setting (define model behavior rules)
user_prompt: user input prompt words

seed: random seed (0-9999999)
max_tokens: maximum number of generated tokens (0-unlimited)
temperature: Generation temperature (0-2, the higher the value, the more random)
top_k: Number of candidate words (0-100)
top_p: Core sampling probability (0-1)

Output port:
raw_output: Raw output including the thinking process
clean_output: Clean output after cleaning
~~~

Feature description:
1. Support setting model behavior rules through system_prompt
2. Automatically clean the <think>thinking process</think> tag of the model output
3. Provide dual output ports to meet the needs of different scenarios
4. Fully support Deepseek model parameter system
~~~

## Update Log 2025-01-08 (White-box Encryption & Enhanced Security!)

We have implemented a sophisticated white-box encryption system and enhanced our security mechanisms:

### White-box Encryption
- Dynamic T-box and S-box generation
- Complex key expansion algorithm
- Multiple round transformations
- Memory protection mechanism

### Enhanced Security Features
- ✓ Secure key storage
- ✓ Anti-debugging protection
- ✓ Memory tampering detection
- ✓ Runtime integrity verification

The new white-box encryption implementation makes it extremely difficult to extract encryption keys even with full access to the code. Combined with our existing multi-layer protection scheme, this provides state-of-the-art security for your models and workflows.

## Update log 2024-12-29 (Introducing a multi-layer protection mechanism in the core code of the runtime protection system package!)
Because the encryption and decryption node code of the previous version was displayed in plain text, it was easy for reverse engineers to crack it, thus failing to ensure the security of the model. Now the core encryption and decryption code uniformly introduces a multi-layer protection mechanism

- Multi-layer protection scheme
   - AST-level code obfuscation
   - PyArmor basic encryption
   - Variable name/function name obfuscation
   - Interference code injection
   - String obfuscation

Now all the security node codes in the project are highly encrypted with a multi-layer protection scheme, which greatly increases the difficulty of cracking by reverse engineers, thereby ensuring the security of the model.

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

## Update log 2024-11-11

### Utils

1. LmcqInputValidator: Used to validate input value types, can determine whether the input is a pure number or a string

~~~
Function details

input_text:     Input text to be validated
check_type:     Validation type, options:
               - is_digit: Check if it's a pure number
               - is_string: Check if it's a string (any input that's not a pure number is considered a string)
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

## Update Log 2024-12-18 (Workflow Protection!)

### Workflow Encryption/Decryption
![workflow_encryption.png](workflow_encryption.png)

### LmcqWorkflowEncryption
~~~
Function Details:
action:        Choose to encrypt or decrypt workflow
password:      Password for encryption/decryption
workflow_file: Select the workflow file to process (from root or plugin workflows folder)
save_name:     Name for the saved file
~~~

This node allows you to encrypt your workflow files with a password, preventing unauthorized access. The encrypted workflow can only be loaded after decryption with the correct password.

Usage:
1. Save your workflow file to either:
   - ComfyUI root/workflows folder (shown as "root/filename")
   - Plugin's workflows folder (shown as "plugin/filename")
2. Use 'encrypt' action to create an encrypted version
3. Share the encrypted workflow file
4. Recipients must use 'decrypt' action with the correct password to use the workflow

Note: The encrypted/decrypted file will be saved in the same folder as the source file.

## (LoRA Protection!)

### LoRA Model Encryption/Decryption
![lora_encryption.png](lora_encryption.png)

### LmcqLoraEncryption
~~~
Function Details:
lora_name:  Select the LoRA model to encrypt
key:        Encryption key (for later decryption)
save_name:  Name for the encrypted model
~~~
After execution, two files will be generated in your loras/encrypted folder: an encrypted model and a .meta file. The meta file contains encryption signature and version information. Both files must be kept together for successful decryption.

### LmcqLoraDecryption
~~~
Function Details:
lora_name:  Select the encrypted LoRA model
key:        Decryption key (must match encryption key)
save_name:  Name for the decrypted model
~~~
The decrypted LoRA will be saved in the loras/decrypted folder.

## Update Log 2024-12-21 (Runtime Protection System!)

### Machine Code & Runtime Protection
![runtime_protection.png](runtime_protection.png)

### LmcqGetMachineCode
A utility node that generates a unique machine code based on hardware and system information. This code is used for authorization in the runtime protection system.

### Runtime Model Protection
~~~
LmcqRuntimeModelEncryption:
- model_name:    Select the model to encrypt
- key:          Encryption key
- save_name:    Name for the encrypted model
- machine_codes: List of authorized machine codes (one per line)

LmcqRuntimeModelDecryption:
- model_name:    Select the encrypted model
- key:          Decryption key
~~~
Provides real-time model encryption/decryption with machine-specific authorization. Models can only be loaded on authorized machines.
PS: The encrypted model is loaded in memory, so the complete model will not be saved locally. It can only be used in the workflow to protect the complete model from being spread to the greatest extent (only LmcqRuntimeModelDecryption can be used to load the encrypted model, and the rest are invalid)

### Runtime LoRA Protection
~~~
LmcqRuntimeLoraEncryption:
- lora_name:     Select the LoRA to encrypt
- key:          Encryption key
- save_name:    Name for the encrypted LoRA
- machine_codes: List of authorized machine codes

LmcqRuntimeLoraDecryption:
- model:         Input model
- clip:         Input CLIP
- lora_name:    Select the encrypted LoRA
- key:          Decryption key
- strength_model: LoRA strength for model
- strength_clip:  LoRA strength for CLIP
~~~
Secure LoRA models with machine-specific authorization and real-time loading.
PS: The encrypted model is loaded in memory, so the complete model will not be saved locally. It can only be used in the workflow to protect the complete model from being spread to the greatest extent (only LmcqRuntimeLoraDecryption can be used to load the encrypted model, and the rest are invalid)
### Runtime Workflow Protection
~~~
LmcqRuntimeWorkflowEncryption:
- workflow_file: Select workflow to encrypt
- key:          Encryption key
- save_name:    Name for encrypted workflow (.lcwf)
- machine_codes: List of authorized machine codes

LmcqRuntimeWorkflowDecryption:
- workflow_file: Select encrypted workflow
- key:          Decryption key
- save_name:    Name for decrypted workflow
~~~
Protects workflows with machine-specific authorization. Encrypted workflows are saved in .lcwf format and can only be decrypted on authorized machines.

Note: The runtime protection system ensures that protected assets can only be used on specifically authorized machines, providing stronger security than password-only protection.

## 2024-12-29 TODO (next plan)

What we are preparing now:
Developing a complete authentication service system dedicated to more efficiently improving the functional security of ComfyUi security nodes. The core functional logic of all nodes will be provided by a third-party authentication service system to maximize the security of models and workflows (and provide more fancy gameplay such as: encryption model usage limit, encryption model usage time limit, encryption model usage device limit, etc.), providing creators with a safer creative environment, so stay tuned! ! !

## Contribute

zebord
