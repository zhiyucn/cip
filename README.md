# cip - 高级包管理器 🎉

## 目录 📚

- [cip - 高级包管理器 🎉](#cip---高级包管理器-)
  - [目录 📚](#目录-)
  - [介绍 🚀](#介绍-)
  - [特性 ✨](#特性-)
  - [安装 🛠️](#安装-️)
  - [使用指南 📖](#使用指南-)
    - [创建 .cpack 包 🆕](#创建-cpack-包-)
    - [安装 .cpack 包 📦](#安装-cpack-包-)
    - [配置 cip ⚙️](#配置-cip-️)
    - [显示版本信息 ℹ️](#显示版本信息-ℹ️)
    - [使用工具 🛠️](#使用工具-️)
    - [上传包 ⬆️](#上传包-️)
    - [下载包 ⬇️](#下载包-️)
    - [列出可用包 📜](#列出可用包-)
  - [服务端搭建 🔧](#服务端搭建-)
    - [1Panel运行环境](#1panel运行环境)
    - [Venv](#venv)
  - [官方源列表😎](#官方源列表)
    - [使用 SSL](#使用-ssl)
    - [不使用 SSL](#不使用-ssl)
  - [许可证 📜](#许可证-)
  - [贡献 🤝](#贡献-)
  - [联系信息 📬](#联系信息-)

## 介绍 🚀

`cip` 是一个先进的包管理器，专为企业环境设计，能够提供统一的版本管理，旨在简化 Python 包的安装和管理。它在企业使用中尤为有效，帮助用户高效地处理项目依赖性。

## 特性 ✨

- 直接操作 Python 目录，适合有一定经验的用户
- 支持创建、安装和配置 .cpack 包
- 大量实用工具，例如查找 Python 安装路径、安装 Flask 项目等
- 提供简体中文界面和命令行工具

## 安装 🛠️

要安装 `cip`，请确保你已经安装 Python（推荐版本为 3.6 及以上）。然后，使用以下命令安装 `cip`：

```bash
pip install cip
```

## 使用指南 📖

### 创建 .cpack 包 🆕

要创建一个新的 .cpack 包，使用以下命令：

```bash
cip create <package_name> <version> [package_dirs]
```

- `<package_name>`: 包的名称
- `<version>`: 包的版本
- `[package_dirs]`: 可选参数，包文件所在的目录

### 安装 .cpack 包 📦

要安装一个 .cpack 包，请使用以下命令：

```bash
cip install <cpack_path>
```

- `<cpack_path>`: .cpack 文件的路径

### 配置 cip ⚙️

可以通过以下命令配置 cip：

```bash
cip config <config_key> [config_value]
```

- `<config_key>`: 配置键
- `[config_value]`: 可选参数，如果提供，则会更新配置值

### 显示版本信息 ℹ️

要显示当前 cip 的版本信息，可以使用：

```bash
cip version
```

### 使用工具 🛠️

cip 提供一些实用工具，可以通过以下命令访问：

```bash
cip tools [tool_name]
```

- `find_python` 或 `fpy`: 查找 Python 安装路径
- `setup_flask`: 一键设置 Flask 项目
- `help`: 显示可用工具的帮助信息

### 上传包 ⬆️

要上传 .cpack 包，请使用以下命令：

```bash
cip upload <package_path>
```

- `<package_path>`: 要上传的 .cpack 包的路径

### 下载包 ⬇️

要下载 .cpack 包，请使用以下命令：

```bash
cip download <package_name> <version>
```

- `<package_name>`: 要下载的包名称
- `<version>`: 要下载的包版本

### 列出可用包 📜

要列出可用的 .cpack 包，可以使用：

```bash
cip list [url]
```

- `[url]`: 可选参数，用于指定要查询的 URL

## 服务端搭建 🔧

官方服务端谁都可以下载包，不适合企业内部使用，如果需要搭建私有服务端，那么可以参考以下步骤：
### 1Panel运行环境
1.打开1Panel面板，点击左侧菜单栏的“应用商店”，在搜索框中输入“Python”，找到Python运行环境，点击安装。  
2.点击左侧菜单栏的“网站”，选择“运行环境”，选择Python，点击创建运行环境。  
3.名称随意，选择Python版本（建议3.13），运行目录自定义，启动脚本填写`pip insatll flask && python server.py`，内部端口填写`5000`，点击创建。  
4.打开你使用的目录，上传本仓库的`server.py`文件。  
5.返回运行环境页面，点击运行环境右侧，点击“启动”。  
6.等待运行环境启动完成。  
### Venv
1.使用ssh或其他方式登录到服务器。  
2.mkdir一个目录，用来存放本项目服务端代码。  
3.在刚才创建的目录下，创建一个Python虚拟环境，并激活。  
4.使用`pip install flask`安装Flask。  
5.将本仓库的`server.py`文件上传到服务器。  
6.创建一个screen，并进入该screen。  
7.使用`python server.py`启动服务端。  
8.断开SSH连接。  
9.访问`http://ip:5000`查看服务端是否正常运行。

## 官方源列表😎
以下是已经过审核的镜像源，注意：虽然名字上叫官方源，但并不是所有都是官方提供的源，所以包可能不会同步。

### 使用 SSL  
https://cip.zhiyuhub.top (官方提供)

### 不使用 SSL  
http://cip.zhiyu.ink (官方提供，与 https://cip.zhiyuhub.top 同步)

## 许可证 📜

`cip` 使用 MIT 许可证。请参见 [LICENSE](LICENSE) 文件了解更多信息。

## 贡献 🤝

欢迎为 `cip` 项目贡献代码！请遵循以下步骤：

1. Fork 本项目 🍴
2. 创建功能分支 (`git checkout -b feature-xyz`) 🌿
3. 提交更改 (`git commit -m 'Add some feature'`) 📑
4. 推送到分支 (`git push origin feature-xyz`) 🚀
5. 创建合并请求 (Pull Request) 🔄

## 联系信息 📬

如有任何问题或建议，可以通过以下方式联系项目维护者：

- [GitHub Issues](https://github.com/zhiyucn/cip/issues) 🛠️
- 邮件: zhiyuxl@outlook.com ✉️

---

感谢您使用 `cip`！🌟 我们期待您的反馈和贡献！