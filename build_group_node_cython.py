import subprocess
import os
import shutil
from pathlib import Path
import sys

def compile_group_node_protection():
    """
    使用 Cython 编译 custom_nodes/ComfyUI-LMCQ-ZE/runtime/group_node_protection.py 文件。
    """
    # 假设此脚本位于 custom_nodes/ComfyUI-LMCQ-ZE/ 目录下
    project_root = Path(__file__).parent.resolve()
    setup_script_name = 'setup_group_node.py'
    target_py_file_relative = Path('runtime') / 'group_node_protection.py'
    
    print(f"项目根目录: {project_root}")
    print(f"准备使用 Cython 编译文件: {target_py_file_relative}...")
    
    # 确保 setup_group_node.py 存在
    if not (project_root / setup_script_name).exists():
        print(f"错误: {setup_script_name} 未在 {project_root} 中找到。")
        return

    # 构建编译命令
    # 'build_ext' 指示 setuptools 构建C扩展
    # '--inplace' 标志使编译后的 .pyd/.so 文件直接生成在源文件旁边或其包结构中正确的位置
    compile_command = [
        sys.executable,  # 使用当前Python解释器
        str(project_root / setup_script_name),
        'build_ext',
        '--inplace'
    ]
    
    print(f"执行编译命令: {' '.join(compile_command)}")
    
    # 在项目根目录执行编译命令
    process = subprocess.Popen(
        compile_command, 
        cwd=str(project_root), 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        text=True, 
        encoding='gbk'
    )
    stdout, stderr = process.communicate()
    
    if process.returncode == 0:
        print(f"Cython 编译成功完成: {target_py_file_relative}")
        if stdout and stdout.strip():
            print("-------------------- STDOUT --------------------")
            print(stdout)
            print("------------------------------------------------")
        if stderr and stderr.strip(): 
            # Cython/编译器经常在stderr输出有用的信息或警告
            print("-------------------- STDERR (可能包含重要信息) --------------------")
            print(stderr)
            print("--------------------------------------------------------------------")
        
        # 定位编译后的文件 (示例，实际名称可能因Python版本和平台而异)
        # 例如: custom_nodes/ComfyUI-LMCQ-ZE/runtime/group_node_protection.cp310-win_amd64.pyd
        compiled_file_found = False
        runtime_dir = project_root / 'runtime'
        for item in runtime_dir.glob('group_node_protection*.pyd'): # Windows
            print(f"成功生成文件: {item}")
            compiled_file_found = True
            break
        if not compiled_file_found:
            for item in runtime_dir.glob('group_node_protection*.so'): # Linux/macOS
                print(f"成功生成文件: {item}")
                compiled_file_found = True
                break
        
        if not compiled_file_found:
            print("警告: 未明确检测到编译后的 .pyd/.so 文件，请手动检查 runtime 目录。")
        else:
            print(f"请确保运行时环境能够找到并加载此编译模块。")

    else:
        print(f"Cython 编译文件失败: {target_py_file_relative} (返回码: {process.returncode})")
        if stdout and stdout.strip():
            print("-------------------- STDOUT --------------------")
            print(stdout)
            print("------------------------------------------------")
        if stderr and stderr.strip():
            print("-------------------- STDERR --------------------")
            print(stderr)
            print("------------------------------------------------")
        # raise Exception("Cython compilation failed.") # 决定是否要抛出异常

    # 清理：编译过程中可能会生成 build 目录和 .c 文件
    # 您可以根据需要取消注释以下清理代码
    build_dir_setuptools = project_root / 'build'
    c_file_in_runtime = project_root / 'runtime' / 'group_node_protection.c'

    if build_dir_setuptools.exists():
        print(f"正在清理 setuptools 构建目录: {build_dir_setuptools}")
        try:
            shutil.rmtree(build_dir_setuptools)
            print("清理完成。")
        except Exception as e:
            print(f"清理 build 目录失败: {e}")
        
    if c_file_in_runtime.exists():
        print(f"正在清理生成的C文件: {c_file_in_runtime}")
        try:
            os.remove(c_file_in_runtime)
            print("清理完成。")
        except Exception as e:
            print(f"清理 .c 文件失败: {e}")

    print(f"文件 {target_py_file_relative} 的 Cython 编译流程已处理。")

if __name__ == '__main__':
    print("重要提示：请确保已安装 Cython (pip install cython) 和 C 编译器 (如 MSVC Build Tools, GCC, Clang)。")
    try:
        compile_group_node_protection()
    except Exception as e:
        print(f"执行编译脚本时发生意外错误: {e}")
