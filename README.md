# TikiDownloader-Client

## 项目概述

TikiDownloader-Client 是一个独立的桌面应用程序，旨在为用户提供一个简洁、高效的工具，用于下载无水印的TikTok视频。用户只需提供TikTok视频的URL，本应用将自动获取包括高清（HD）、标清（SD）以及带水印等多种格式的视频下载链接，并提供一键下载到本地的功能。

## 功能特点

- 简洁直观的用户界面
- 支持多种视频格式下载（HD、SD、带水印）
- 下载进度实时显示
- 支持代理设置，应对网络限制
- 内置反爬虫策略，提高稳定性

## 安装步骤

### 方法一：直接下载可执行文件（推荐）

1. 查看[本仓库 Releases 页面](https://github.com/change979666/tiki-downloader/releases)是否有已发布的可执行文件。
2. 如果没有可用的 Release，请使用下面的源码运行或打包步骤；仓库当前不保证始终提供预编译 EXE。

### 方法二：从源码运行

1. 确保已安装Python 3.9+
2. 克隆或下载本仓库
3. 安装依赖包：
   ```
   pip install -r requirements.txt
   ```
4. 运行程序：
   ```
   python main.py
   ```

## 使用方法

1. 启动应用程序
2. 将TikTok视频链接粘贴到输入框中
3. 点击"获取链接"按钮
4. 在显示的下载选项中，选择所需的视频格式
5. 选择保存位置，开始下载
6. 下载完成后，可以选择打开文件所在目录

## 代理设置

如果您所在的网络环境无法直接访问TikTok或相关服务，可以通过以下步骤设置代理：

1. 点击菜单栏中的"设置" -> "代理设置"
2. 输入代理服务器地址，格式为：`http://user:password@proxy.example.com:8080`
3. 勾选"使用代理服务器"
4. 点击"保存"按钮

## 打包为可执行文件

如果您想将源码打包为独立的可执行文件，可以使用PyInstaller：

1. 安装PyInstaller：
   ```
   pip install pyinstaller
   ```
2. 执行打包命令：
   ```
   pyinstaller TikiDownloader.spec
   ```
3. 打包完成后，可执行文件将位于`dist`目录中

## 注意事项

- 本工具本身不直接解析 TikTok，而是把链接发送到第三方在线解析服务（代码中对接了 `musicaldown.com` 与 `ssstik.io`）来获取无水印下载地址；这些第三方服务可能随时改版、加验证码、限流或停止服务，**从而导致本工具失效**。
- 因此本工具**不承诺永久可用**；失效通常是第三方解析服务或 TikTok 反爬策略变化所致，需自行评估替代方案。
- 代理设置目前作用于“下载文件”环节（见下文“代理设置”），解析请求的网络可达性仍取决于你本地网络；代理地址需你自备。
- 本工具仅供学习和个人使用
- 请尊重内容创作者的权益，不要用于商业用途
- 下载的视频可能受版权保护，请遵守相关法律法规

## 技术栈

- Python 3.9+
- Tkinter (GUI)
- Requests (HTTP通信)
- BeautifulSoup4 (HTML解析)

## License & Attribution / 许可与来源

Original project code authored for this repository is released under the MIT License; see [LICENSE](./LICENSE).

When reusing or redistributing a substantial portion, retain the LICENSE and its copyright notice. The copyright notice includes this original source URL: https://github.com/change979666/tiki-downloader. Please keep the source link visible in your redistributed source or project documentation.

This license applies only to original material that the repository maintainer has the right to license. Third-party libraries, vendor code, platform SDKs, trademarks, screenshots, icons, fonts, and other external assets remain subject to their respective licenses and terms. Review those terms before reuse.

**Project status:** personal/archived project, shared as-is. Maintenance, compatibility, and production readiness are not guaranteed.