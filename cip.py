# 客户端代码
import zipfile
import json
import shutil
import click
import sys
from pathlib import Path
import os                   
import configparser
import subprocess
import requests
import certifi
CIP_VERSION = "0.0.4 beta"
# 颜色设置
WHITE = '\033[0m'
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
BOLD = '\033[1m'
SKYBLUE = '\033[36m'



def setup_config():
    """
    配置 cip
    """
    config = configparser.ConfigParser()
    config_path = Path("~/.cip/config.ini").expanduser()
    if not config_path.exists():
        config_path.parent.mkdir(exist_ok=True)
        config['CONFIG'] = {
            'lang': 'zh-CN',
            'web_url': 'https://cip.zhiyuhub.top',
            'version': CIP_VERSION
            }
        with open(config_path, 'w') as configfile:
            config.write(configfile)
    try:
        config = configparser.ConfigParser()
        config.read(config_path)
        if config['CONFIG']['version']!= CIP_VERSION:
            click.echo(f"{RED}{BOLD}警告:{WHITE} 配置文件版本不是{CIP_VERSION}，可能存在兼容性问题。")
            # 修改配置文件版本
            config['CONFIG']['version'] = CIP_VERSION
            with open(config_path, 'w') as configfile:
                config.write(configfile)
    except Exception as e:
        click.echo(f"{RED}{BOLD}错误:{WHITE} 读取配置文件失败。")
        click.echo(f"{RED}{BOLD}错误信息:{WHITE} {e}")
        click.echo(f"请使用cip reset命令重新生成配置文件。")
        #sys.exit(1)

def get_config(key):
    """
    获取配置
    """
    config_path = Path("~/.cip/config.ini").expanduser()
    if not config_path.exists():
        click.echo("{RED}{BOLD}ERROR:{WHITE} 配置文件不存在，请先配置。")
        return
    config = configparser.ConfigParser()
    config.read(config_path)
    if key not in config['CONFIG']:
        if config['CONFIG']['lang'] == 'zh-CN':
            click.echo(f"{RED}{BOLD}ERROR:{WHITE} 配置项 {key} 不存在。")
        else:
            click.echo(f"{RED}{BOLD}ERROR:{WHITE} Config item {key} does not exist.")
        return
    return config['CONFIG'][key]


def find_python_path():
    """
    查找Python安装路径
    """
    def find_python_in_directory(directory):
        paths = []
        if os.name == 'nt':
            for path in directory.glob("**/python.exe"):
                click.echo(f"{BLUE}已找到{path.parent}中的Python:{WHITE}")
                paths.append(str(path.parent))  # 返回Python安装目录
        else:
            for path in directory.glob("python*"):
                click.echo(f"{BLUE}已找到{path.parent}中的Python:{WHITE}")
                if path.is_file() and os.access(path, os.X_OK):
                    paths.append(str(path.parent))  # 返回Python安装目录
        return paths

    # 首先尝试从默认安装路径中查找
    if os.name == 'nt':
        default_path = Path(os.path.expanduser("~")) / "AppData" / "Local" / "Programs" / "Python"
    else:
        default_path = Path("/usr/local/bin")

    python_paths = find_python_in_directory(default_path)
    
    if python_paths:
        # 如果找到多个路径，提示用户选择
        if len(python_paths) > 1:
            click.echo(f"{BLUE}找到多个Python安装路径，请选择一个:{WHITE}")
            for idx, path in enumerate(python_paths, start=1):
                click.echo(f"{idx}: {path} 版本：{path.split('\\')[-1]}")
            choice = click.prompt("请输入选择的数字", type=int)
            return python_paths[choice - 1]
        else:
            return python_paths[0]

    # 如果默认路径未找到，提示用户手动输入路径
    click.echo("未找到Python安装路径，请手动输入路径:")
    python_dir = click.prompt("Python 安装目录 (输入 'All' 查找整个电脑)", type=str)
    
    if python_dir.lower() == 'all':
        # 查找整个电脑
        if os.name == 'nt':
            # Windows 系统
            drives = [f"{d}:\\" for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:\\")]
            for drive in drives:
                drive_path = Path(drive)
                python_paths.extend(find_python_in_directory(drive_path))
        else:
            # Unix/Linux 系统
            root_path = Path("/")
            python_paths.extend(find_python_in_directory(root_path))
    else:
        custom_path = Path(python_dir)
        python_paths = find_python_in_directory(custom_path)
    
    if python_paths:
        if len(python_paths) > 1:
            click.echo(f"{BLUE}找到多个Python安装路径，请选择一个:{WHITE}")
            for idx, path in enumerate(python_paths, start=1):
                # 计算版本
                import subprocess
                version = subprocess.run([str(os.path.join(path, "python")), "--version"], capture_output=True, text=True).stdout.strip()
                if version.startswith("Python "):
                    pass
                else:
                    version = "未激活的虚拟环境或其他"
                click.echo(f"{idx}: {path} 版本：{version}")
            choice = click.prompt("请输入选择的数字", type=int)
            return python_paths[choice - 1]
        else:
            return python_paths[0]

    click.echo("未找到有效的Python安装路径。")
    return None



class CPackTool:
    @staticmethod
    def create_cpack(package_name, version, package_dirs):
        """
        创建 .cpack 包
        :param package_name: 包名
        :param version: 版本号
        :param package_dirs: 包含 __init__.py 的多个 Python 包目录
        """
        # 检查所有包目录是否有效
        package_dirs = [Path(d) for d in package_dirs]
        for package_dir in package_dirs:
            if not (package_dir / "__init__.py").exists():
                config = configparser.ConfigParser()
                config_path = Path("~/.cip/config.ini").expanduser()
                config.read(config_path)
                if config['CONFIG']['lang'] == 'zh-CN':
                    raise FileNotFoundError(f"{RED}{BOLD}目录 {package_dir} 不是有效的 Python 包（缺少 __init__.py）。{WHITE}")
                else:
                    raise FileNotFoundError(f"{RED}{BOLD}Directory {package_dir} is not a valid Python package (missing __init__.py).{WHITE}")

        # 创建 pack.json
        pack_data = {
            "name": package_name,
            "version": version,
            "packages": [str(dir.name) for dir in package_dirs],
            "cip_version": CIP_VERSION
        }
        pack_json_path = Path(f"{package_name}-{version}.json")
        with open(pack_json_path, "w") as f:
            json.dump(pack_data, f, indent=4)

        # 将每个包目录打包为 pack.zip
        pack_zip_path = Path("pack.zip")
        with zipfile.ZipFile(pack_zip_path, "w") as zipf:
            for package_dir in package_dirs:
                for file in package_dir.rglob("*"):
                    if file.is_file():
                        arcname = file.relative_to(package_dir.parent)
                        zipf.write(file, arcname=arcname)

        # 创建 .cpack 文件
        cpack_path = Path(f"{package_name}-{version}.cpack")
        with zipfile.ZipFile(cpack_path, "w") as zipf:
            zipf.write(pack_zip_path, arcname="pack.zip")
            zipf.write(pack_json_path, arcname="pack.json")

        # 清理临时文件
        pack_json_path.unlink()
        pack_zip_path.unlink()
        click.echo(f"Created {cpack_path}")

    @staticmethod
    def install_cpack(cpack_path):
        """
        安装 .cpack 包
        :param cpack_path: .cpack 文件路径
        """
        extract_dir = Path("extracted")
        extract_dir.mkdir(exist_ok=True)

        with zipfile.ZipFile(cpack_path, "r") as zipf:
            zipf.extractall(extract_dir)

        pack_json_path = extract_dir / "pack.json"
        with open(pack_json_path, "r") as f:
            pack_data = json.load(f)

        # 查找Python路径
        python_dir = find_python_path()
        

        site_packages_dir = Path(python_dir) / "Lib" / "site-packages"
        packages_dir = Path(python_dir) / "Lib"
        
        for package_name in pack_data["packages"]:
            config = configparser.ConfigParser()
            config_path = Path("~/.cip/config.ini").expanduser()
            config.read(config_path)
            click.echo(f"加载中...")
            try:
                if pack_data["cip_version"] == CIP_VERSION:
                    pass
                else:
                    click.echo(f"{RED}{BOLD}警告:{WHITE} cip 版本不匹配，可能存在兼容性问题。")
            except:
                click.echo(f"{RED}{BOLD}警告:{WHITE} 未知的 cip 版本，可能存在兼容性问题。")
            if config['CONFIG']['lang'] == 'zh-CN':
                click.echo(f"准备安装包: {package_name}")
            else:
                click.echo(f"Preparing to install package: {package_name}")

            # 确认安装
            confirm = click.prompt("确认安装该包吗？(Y/n)", type=str)
            if confirm.lower() == 'y' or confirm.lower() == '':
                pack_zip_path = extract_dir / "pack.zip"
                with zipfile.ZipFile(pack_zip_path, "r") as zipf:
                    for file in zipf.namelist():
                        if file.startswith(f"{package_name}/"):
                            
                            zipf.extract(file, extract_dir)

                shutil.move(extract_dir / package_name, site_packages_dir / package_name)
                shutil.move(extract_dir / package_name, packages_dir / package_name)
                if config['CONFIG']['lang'] == 'zh-CN':
                    click.echo(f"已安装 {package_name} 到 {site_packages_dir / package_name} 和 {packages_dir / package_name}")
                else:
                    click.echo(f"Installed {package_name} to {site_packages_dir / package_name} and {packages_dir / package_name}")
            else:
                if config['CONFIG']['lang'] == 'zh-CN':
                    click.echo(f"跳过安装包: {package_name}")
                else:
                    click.echo(f"Skipping package: {package_name}")

        shutil.rmtree(extract_dir)
        click.echo(f"安装完成!")

@click.group()
def cli():
    """ cip - An advanced package manager.
        cip - 更高级的包管理器。

    Warning: cip is mainly used in enterprise environments for unified version management, and is not suitable for beginners, and involves direct operations on Python directories, which may be reported by antivirus software as malware.
    
    警告：cip 主要运用在企业环境的统一版本管理，并不适合初学者使用，并且涉及对Python目录的直接操作，可能会被杀软误报。 
    
    Only speak to groups where Chinese is not the primary language. This program does not provide complete support for other languages, only Chinese has full language support."""
    pass

@cli.command()
@click.argument("package_name")
@click.argument("version")
@click.argument("package_dirs", type=click.Path(exists=True), nargs=-1)
def create(package_name, version, package_dirs):
    """ 创建 .cpack 包 """
    try:
        CPackTool.create_cpack(package_name, version, package_dirs)
    except Exception as e:
        click.echo(f"{RED}{BOLD}ERROR:{WHITE} {e}", err=True)

@cli.command()
@click.argument("cpack_path", type=click.Path(exists=True))
def install(cpack_path):
    """ 安装 .cpack 包 """
    try:
        CPackTool.install_cpack(Path(cpack_path))
    except Exception as e:
        click.echo(f"{RED}{BOLD}ERROR:{WHITE} {e}", err=True)

@cli.command()
@click.argument("config_key")
@click.argument("config_value", required=False)
def config(config_key, config_value=None):
    """ 配置 cip """
    config = configparser.ConfigParser()
    config_path = Path("~/.cip/config.ini").expanduser()
    if not config_path.exists():
        click.echo("{RED}{BOLD}ERROR:{WHITE} 配置文件不存在，请先配置。")
        return
    config.read(config_path)
    if config_value is None:
        if config['CONFIG']['lang'] == 'zh-CN':
            click.echo(f"{config_key} 的值: {config['CONFIG'][config_key]}")
        else:
            click.echo(f"The value of {config_key}: {config['CONFIG'][config_key]}")
    else:
        config['CONFIG'][config_key] = config_value
        with open(config_path, 'w') as configfile:
            config.write(configfile)
        if config['CONFIG']['lang'] == 'zh-CN':
            click.echo(f"{config_key} 的值已设置为 {config_value}")
        else:
            click.echo(f"{config_key} has been set to {config_value}")

@cli.command()
def version():
    """ 显示 cip 版本 """
    click.echo("cip "+ CIP_VERSION)
    config = configparser.ConfigParser()
    config_path = Path("~/.cip/config.ini").expanduser()
    if not config_path.exists():
        click.echo("{RED}{BOLD}ERROR:{WHITE} 配置文件不存在，请先配置。")
        return
    config.read(config_path)
    if config['CONFIG']['lang'] == 'zh-CN':
        click.echo("语言: 中文")
        click.echo(f"Python 版本: {sys.version}")
        click.echo("开源许可证: MIT License")
        click.echo("在Github上查看: https://github.com/zhiyucn/cip")
    else:
        click.echo("Language: English")
        click.echo(f"Python version: {sys.version}")
        click.echo("License: MIT License")
        click.echo("View on Github: https://github.com/zhiyucn/cip")

@cli.command()
@click.argument("tool_name", required=False)
def tools(tool_name):
    """ 一些杂七杂八的工具 """
    if tool_name == "find_python" or tool_name == "fpy":
        click.echo(f"{BLUE}这个工具用于查找Python安装路径，以及用来查看你的电脑里有多少个Python。（作者的电脑里有36个，几乎都是虚拟环境）{WHITE}")
        find_python_path()
    elif tool_name == "检测父母性别":
        click.echo(f"{BLUE}这个工具用于检测父母性别。{WHITE}")
        click.echo(f"{BLUE}请输入检测对象（填写父亲或母亲）：{WHITE}")
        name = click.prompt("检测对象", type=str)
        if name.lower() == "父亲":
            click.echo(f"{BLUE}你的父亲是男的。{WHITE}")
        elif name.lower() == "母亲":
            click.echo(f"{BLUE}你的母亲是女的。{WHITE}")
        else:
            click.echo(f"{RED}{BOLD}ERROR:{WHITE} 未知的对象。")
    elif tool_name == "help":
        click.echo(f"{BLUE}小工具帮助：{WHITE}")
        click.echo(f"{YELLOW}cip tools find_python{WHITE} - 查找Python安装路径")
        click.echo(f"{YELLOW}cip tools fpy{WHITE} - 查找Python安装路径（别名）")
        click.echo(f"{YELLOW}cip tools help{WHITE} - 显示工具帮助（此页面）")
        click.echo(f"{YELLOW}cip tools 检测父母性别{WHITE} - 检测父母性别")
        click.echo(f"{YELLOW}cip tools setup_flask{WHITE} - 一键配置Flask项目")
    elif tool_name == "setup_flask":
        click.echo(f"{BLUE}正在配置Flask项目...{WHITE}")
        setup_flask_project()
    elif tool_name is None:
        click.echo(f"{YELLOW}cip tools find_python{WHITE} - 查找Python安装路径")
        click.echo(f"{YELLOW}cip tools fpy{WHITE} - 查找Python安装路径（别名）")
        click.echo(f"{YELLOW}cip tools help{WHITE} - 显示工具帮助（此页面）")
        click.echo(f"{YELLOW}cip tools 检测父母性别{WHITE} - 检测父母性别")
        click.echo(f"{YELLOW}cip tools setup_flask{WHITE} - 一键配置Flask项目")
    else:
        click.echo(f"{RED}{BOLD}ERROR:{WHITE} 未知的工具 {tool_name}")
        click.echo(f"{BLUE}我猜你可能需要输入{YELLOW} cip tools help{WHITE} 来查看工具帮助。")

def setup_flask_project():
    """ 一键配置Flask项目 """
    import os
    import subprocess

    # 选择项目路径
    project_path = click.prompt("请输入项目路径（默认为当前目录）", type=str, default=os.getcwd())
    project_name = click.prompt("请输入项目名称", type=str)

    # 创建项目目录
    full_project_path = os.path.join(project_path, project_name)
    os.makedirs(full_project_path, exist_ok=True)
    os.chdir(full_project_path)

    # 创建虚拟环境
    click.echo(f"{BLUE}正在创建虚拟环境...{WHITE}")
    subprocess.run(["python", "-m", "venv", "venv"])

    # 激活虚拟环境并安装Flask
    click.echo(f"{BLUE}正在安装Flask...{WHITE}")
    if os.name == "nt":  # Windows
        activate_script = os.path.join("venv", "Scripts", "activate")
        subprocess.run([activate_script, "&&", "pip", "install", "flask"], shell=True)
    else:  # Unix or MacOS
        activate_script = os.path.join("venv", "bin", "activate")
        subprocess.run(f"source {activate_script} && pip install flask", shell=True, executable="/bin/bash")

    # 创建基本的Flask应用结构
    click.echo(f"{BLUE}正在创建Flask应用结构...{WHITE}")
    with open("app.py", "w") as f:
        f.write("""from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

if __name__ == '__main__':
    app.run(debug=True)
""")

    click.echo(f"{GREEN}Flask项目配置完成！{WHITE}")
    click.echo(f"{BLUE}你可以通过以下命令启动项目：{WHITE}")
    click.echo(f"{YELLOW}cd {full_project_path}{WHITE}")
    click.echo(f"{YELLOW}python app.py{WHITE}")

@cli.command()
@click.argument("package_path")
#@click.argument("version")
def upload(package_path):
    """ 上传 .cpack 包 """
    package_name = package_path
    filename = f"{package_name}"
    version = filename.split("-")[-1]
    file_path = os.path.join(filename)  # 根据需求设置文件路径
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        click.echo(f"ERROR: 文件 {file_path} 不存在。")
        return
    
    # 上传文件
    with open(file_path, 'rb') as f:
        # 跳过SSL验证
        response = requests.post(f"{BASE_URL}/cip/upload", files={'file': f}, data={'package_name': package_name, 'package_version': version},verify=False)
        
    if response.status_code == 200:
        click.echo(f"成功上传 {filename}！")
    else:
        click.echo(f"ERROR: 上传失败：{response.json().get('error', '未知错误')}。")

@cli.command()
@click.argument("package_name")
@click.argument("version")
def download(package_name, version):
    """ 下载 .cpack 包 """
    url = f"{BASE_URL}/download/{package_name}/{version}/{package_name}-{version}.cpack"
    response = requests.get(url, verify=False)
    
    if response.status_code == 200:
        with open(f"{package_name}-{version}.cpack", "wb") as f:
            f.write(response.content)
        click.echo(f"下载 {package_name}-{version}.cpack")
        
        # 可选：运行安装命令
        yes = click.prompt("是否立即安装？(Y/n)", type=str)
        if yes.lower() == 'y' or yes.lower() == '':
            CPackTool.install_cpack(Path(f"{package_name}-{version}.cpack"))
        else:
            pass
    elif response.status_code == 404:
        click.echo(f"ERROR: 未找到 {package_name} {version} 版本的包。")
    else:
        click.echo(f"ERROR: 下载失败")

@cli.command()
@click.argument("url", required=False)
def list(url=None):
    """ 列出可用的 .cpack 包 """
    if url is None:
        print(BASE_URL)
        response = requests.get(f"{BASE_URL}/cip/packages")
    else:
        response = requests.get(f"{url}/cip/packages")
    if response.status_code == 200:
        packages = response.json()
        click.echo("可下载的包及版本：")
        for package_name, versions in packages.items():
            click.echo(f"{package_name}: {', '.join(versions)}")
    else:
        click.echo("ERROR: 获取包列表失败。")

@cli.command()
def reset():
    """ 重置 cip 配置 """
    config_path = Path("~/.cip/config.ini").expanduser()
    if config_path.exists():
        os.remove(config_path)
        setup_config()
        click.echo("已重置 cip 配置。")
    else:
        click.echo("ERROR: 配置文件不存在。")

if __name__ == "__main__":

    setup_config()
    config = configparser.ConfigParser()
    config_path = Path("~/.cip/config.ini").expanduser()
    BASE_URL = get_config("web_url")
    print(BASE_URL)
    #print(BASE_URL)
    cli()
