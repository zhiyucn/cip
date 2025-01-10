import zipfile
import json
import shutil
import click
import sys
from pathlib import Path
import os
import configparser

def setup_config():
    """
    配置 cip
    """
    config = configparser.ConfigParser()
    config_path = Path("~/.cip/config.ini").expanduser()
    if not config_path.exists():
        config_path.parent.mkdir(exist_ok=True)
        config['CONFIG'] = {
            'lang': 'zh-CN'
        }
        with open(config_path, 'w') as configfile:
            config.write(configfile)

def get_config(key):
    """
    获取配置
    """
    config_path = Path("~/.cip/config.ini").expanduser()
    if not config_path.exists():
        click.echo("Error: 配置文件不存在，请先配置。")
        return
    config = configparser.ConfigParser()
    config.read(config_path)
    if key not in config['CONFIG']:
        if config['CONFIG']['lang'] == 'zh-CN':
            click.echo(f"Error: 配置项 {key} 不存在。")
        else:
            click.echo(f"Error: Config item {key} does not exist.")
        return
    return config['CONFIG'][key]


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
                # 读取配置文件的lang
                config = configparser.ConfigParser()
                config_path = Path("~/.cip/config.ini").expanduser()
                config.read(config_path)
                if config['CONFIG']['lang'] == 'zh-CN':
                    raise FileNotFoundError(f"目录 {package_dir} 不是有效的 Python 包（缺少 __init__.py）。")
                else:
                    raise FileNotFoundError(f"Directory {package_dir} is not a valid Python package (missing __init__.py).")

        # 创建 pack.json
        pack_data = {
            "name": package_name,
            "version": version,
            "packages": [str(dir.name) for dir in package_dirs]
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
                        # 使用相对路径保留目录结构
                        arcname = file.relative_to(package_dir.parent)  # 包含父目录，使得打包包含文件夹结构
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
    def install_cpack(cpack_path, python_dir):
        """
        安装 .cpack 包
        :param cpack_path: .cpack 文件路径
        :param python_dir: Python 安装目录
        """
        # 解压 .cpack 文件
        extract_dir = Path("extracted")
        extract_dir.mkdir(exist_ok=True)

        with zipfile.ZipFile(cpack_path, "r") as zipf:
            zipf.extractall(extract_dir)

        # 读取 pack.json
        pack_json_path = extract_dir / "pack.json"
        with open(pack_json_path, "r") as f:
            pack_data = json.load(f)

        # 提示用户确认安装每个包
        site_packages_dir = Path(python_dir) / "Lib" / "site-packages"
        for package_name in pack_data["packages"]:
            config = configparser.ConfigParser()
            config_path = Path("~/.cip/config.ini").expanduser()
            config.read(config_path)
            if config['CONFIG']['lang'] == 'zh-CN':
                click.echo(f"准备安装包: {package_name}")
            else:
                click.echo(f"Preparing to install package: {package_name}")
            if config['CONFIG']['lang'] == 'zh-CN':
                confirm = click.prompt("确认安装该包吗？(Y/n)", type=str)
            else:
                confirm = click.prompt("Do you want to install this package? (Y/n)", type=str)

            if confirm.lower() == 'y' or confirm.lower() == '':
                pack_zip_path = extract_dir / "pack.zip"
                # 仅解压包中的指定包
                with zipfile.ZipFile(pack_zip_path, "r") as zipf:
                    for file in zipf.namelist():
                        if file.startswith(f"{package_name}/"):
                            zipf.extract(file, extract_dir)

                # 移动包到 site-packages 目录
                shutil.move(extract_dir / package_name, site_packages_dir / package_name)
                if config['CONFIG']['lang'] == 'zh-CN':
                    click.echo(f"已安装 {package_name} 到 {site_packages_dir / package_name}")
                else:
                    click.echo(f"Installed {package_name} to {site_packages_dir / package_name}")
            else:
                if config['CONFIG']['lang'] == 'zh-CN':
                    click.echo(f"跳过安装包: {package_name}")
                else:
                    click.echo(f"Skipping package: {package_name}")
        # 清理临时文件
        shutil.rmtree(extract_dir)
        click.echo(f"安装完成!")

@click.group()
def cli():
    """ cip - Better then pip.
        cip - 比 pip 更好。

    Warning: cip is mainly used in enterprise environments for unified version management, and is not suitable for beginners, and involves direct operations on Python directories, which may be reported by antivirus software as malware.
    
    警告：cip 主要运用在企业等环境的统一版本管理，并不适合初学者使用，并且涉及对Python目录的直接操作，可能会被杀软误报。 """
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
        click.echo(f"Error: {e}", err=True)

@cli.command()
@click.argument("cpack_path", type=click.Path(exists=True))
@click.option("--python-dir", type=click.Path(), default=sys.prefix, help="Python installation directory (default: current Python environment)")
def install(cpack_path, python_dir):
    """ 安装 .cpack 包 """
    try:
        CPackTool.install_cpack(Path(cpack_path), Path(python_dir))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.command()
@click.argument("config_key")
@click.argument("config_value", required=False)
def config(config_key, config_value=None):
    """ 配置 cip """
    config = configparser.ConfigParser()
    config_path = Path("~/.cip/config.ini").expanduser()
    if not config_path.exists():
        click.echo("Error: 配置文件不存在，请先配置。")
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
    click.echo("cip 0.0.1 alpha")
    config = configparser.ConfigParser()
    config_path = Path("~/.cip/config.ini").expanduser()
    if not config_path.exists():
        click.echo("Error: 配置文件不存在，请先配置。")
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
if __name__ == "__main__":
    setup_config()
    cli()
