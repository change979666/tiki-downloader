import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Toplevel
import threading
import os
import io
import requests
import tempfile
import shutil
import atexit
import webbrowser
from PIL import Image, ImageTk
from downloader_core import get_download_options, download_file, download_file_with_proxy
from video_id_gui import VideoIdFrame

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("TikiDownloader-Client v1.0")
        self.root.geometry("700x550")
        self.root.resizable(True, True)
        
        # 创建缓存目录在程序根目录
        self.cache_dir = os.path.join(os.getcwd(), ".cache")
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        print(f"[Debug] 创建缓存目录: {self.cache_dir}")
        
        # 注册程序退出时清理缓存文件的函数
        atexit.register(self.cleanup_temp_files)
        
        # 创建选项卡控件
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 创建主界面选项卡
        self.main_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.main_tab, text="主界面")

        # 创建日志选项卡
        self.log_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.log_tab, text="日志")

        # 初始化日志选项卡UI
        self.show_debug_window()

        # 日志选项卡已创建，无需独立窗口
        self.debug_window = None

        # --- UI组件定义 ---
        # URL输入部分
        self.url_frame = ttk.Frame(self.main_tab, padding="10")
        self.url_frame.pack(fill=tk.X)
        self.url_label = ttk.Label(self.url_frame, text="TikTok URL:")
        self.url_label.pack(side=tk.LEFT, padx=5)
        self.url_entry = ttk.Entry(self.url_frame, width=50)
        self.url_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.fetch_button = ttk.Button(self.url_frame, text="获取链接", command=self.start_fetching)
        self.fetch_button.pack(side=tk.LEFT, padx=5)
        
        # 视频ID输入部分
        self.video_id_frame = VideoIdFrame(self.main_tab, self)
        self.video_id_frame.pack(fill=tk.X)
        
        # 用户名输入部分
        self.username_frame = ttk.Frame(self.main_tab, padding="10")
        self.username_frame.pack(fill=tk.X)
        self.username_label = ttk.Label(self.username_frame, text="TikTok用户名:")
        self.username_label.pack(side=tk.LEFT, padx=5)
        self.username_entry = ttk.Entry(self.username_frame, width=30)
        self.username_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.username_button = ttk.Button(self.username_frame, text="复制用户名", command=lambda: self.copy_to_clipboard(self.username_entry.get()))
        self.username_button.pack(side=tk.LEFT, padx=2)
        
        # 打开用户主页按钮
        self.open_profile_button = ttk.Button(self.username_frame, text="打开用户主页", command=self.open_user_page_from_entry)
        self.open_profile_button.pack(side=tk.LEFT, padx=2)
        
        # 调试模式默认开启但不显示按钮
        self.debug_var = tk.BooleanVar(value=True)
        # self.debug_button = ttk.Button(self.username_frame, text="调试模式(开启)", 
        #                               command=self.toggle_debug_mode)
        # self.debug_button.pack(side=tk.LEFT, padx=10)

        # 下载选项显示部分
        self.options_frame = ttk.LabelFrame(self.main_tab, text="下载选项", padding="10")
        self.options_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 状态栏
        self.status_bar = ttk.Label(root, text="准备就绪...", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 进度条
        self.progress_bar = ttk.Progressbar(root, orient='horizontal', mode='determinate')
        self.progress_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        self.progress_bar.pack_forget() # 默认隐藏

        # 设置菜单
        self.create_menu()

    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="退出", command=self.root.quit)

        # 设置菜单
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="设置", menu=settings_menu)
        settings_menu.add_command(label="代理设置", command=self.show_proxy_settings)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)

    def show_proxy_settings(self):
        """显示代理设置对话框"""
        proxy_window = tk.Toplevel(self.root)
        proxy_window.title("代理设置")
        proxy_window.geometry("400x200")
        proxy_window.resizable(False, False)
        proxy_window.transient(self.root)  # 设置为主窗口的子窗口
        proxy_window.grab_set()  # 模态窗口

        # 创建代理设置界面
        ttk.Label(proxy_window, text="代理服务器地址:").pack(pady=(20, 5))
        proxy_entry = ttk.Entry(proxy_window, width=40)
        proxy_entry.pack(pady=5, padx=20)
        proxy_entry.insert(0, "http://user:password@proxy.example.com:8080")

        # 使用代理的复选框
        use_proxy_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(proxy_window, text="使用代理服务器", variable=use_proxy_var).pack(pady=5)

        # 保存按钮
        def save_proxy_settings():
            # 这里可以保存代理设置到配置文件或全局变量
            self.proxy_address = proxy_entry.get() if use_proxy_var.get() else None
            messagebox.showinfo("成功", "代理设置已保存")
            proxy_window.destroy()

        ttk.Button(proxy_window, text="保存", command=save_proxy_settings).pack(pady=20)

    def show_about(self):
        """显示关于对话框"""
        about_text = "TikiDownloader-Client v1.0\n\n"
        about_text += "一个简洁、高效的TikTok无水印视频下载工具\n\n"
        about_text += "© 2023 TikiDownloader Team"
        messagebox.showinfo("关于", about_text)

    def set_status(self, message):
        self.status_bar.config(text=message)
        self.root.update_idletasks()

    def clear_options(self):
        # 清除上一次的结果
        for widget in self.options_frame.winfo_children():
            widget.destroy()

    def start_fetching(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("错误", "请输入TikTok链接！")
            return
        
        # 显示调试信息
        if self.debug_var.get():
            print(f"[Debug] 正在处理URL: {url}")
            
        self.fetch_button.config(state=tk.DISABLED)
        self.set_status("正在获取下载链接，请稍候...")
        self.clear_options()
        
        # 使用线程以防止UI卡死
        threading.Thread(target=self.fetch_links_thread, args=(url,)).start()
        
    def open_user_page_from_entry(self):
        """从输入框获取用户名并打开用户主页"""
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showerror("错误", "请输入TikTok用户名！")
            return
            
        # 显示调试信息
        if self.debug_var.get():
            print(f"[Debug] 正在获取用户视频: {username}")
            self.log_debug(f"打开用户主页: @{username}")
            
        # 直接打开用户主页
        self.open_user_profile(username)
        self.set_status(f"已打开用户 @{username} 的主页")
        
    def open_in_browser(self, url):
        """在默认浏览器中打开URL"""
        import webbrowser
        webbrowser.open(url)
        
    def load_avatar_image(self, avatar_url):
        """从URL加载头像图片并显示，添加缓存检查和错误处理"""
        import os
        import time
        import requests
        from PIL import Image, ImageTk
        import hashlib

        # 确保缓存目录存在
        cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.cache')
        if not os.path.exists(cache_dir):
            try:
                os.makedirs(cache_dir)
                self.log_debug(f"创建缓存目录: {cache_dir}")
            except Exception as e:
                self.log_debug(f"创建缓存目录失败: {str(e)}")
                return

        # 生成唯一的缓存文件名
        avatar_hash = hashlib.md5(avatar_url.encode()).hexdigest()
        cache_path = os.path.join(cache_dir, f"avatar_{avatar_hash}.jpg")
        self.log_debug(f"头像缓存路径: {cache_path}")

        # 检查缓存文件是否存在且有效
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
            self.log_debug(f"使用缓存头像: {cache_path}")
            try:
                # 尝试直接从缓存加载
                image = Image.open(cache_path)
                photo = ImageTk.PhotoImage(image.resize((100, 100), Image.LANCZOS))
                self.user_avatar_label.config(image=photo)
                self.user_avatar_label.image = photo  # 保存引用
                return
            except Exception as e:
                self.log_debug(f"缓存头像加载失败: {str(e)}, 将重新下载")
                os.remove(cache_path)  # 删除损坏的缓存文件

        # 添加延迟后下载新头像
        self.log_debug(f"开始下载头像: {avatar_url}")
        try:
            # 使用requests库下载图片
            response = requests.get(avatar_url, stream=True, timeout=10)
            response.raise_for_status()

            # 保存图片到缓存
            with open(cache_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            self.log_debug(f"头像下载成功并保存到缓存: {cache_path}")

            # 延迟0.5秒确保文件写入完成
            time.sleep(0.5)

            # 加载并显示头像
            image = Image.open(cache_path)
            photo = ImageTk.PhotoImage(image.resize((100, 100), Image.LANCZOS))
            self.user_avatar_label.config(image=photo)
            self.user_avatar_label.image = photo  # 保存引用

        except Exception as e:
            self.log_debug(f"头像加载失败: {str(e)}")
            # 设置错误占位图
            self.user_avatar_label.config(text="头像加载失败")
            # 清除之前的图片引用
            if hasattr(self.user_avatar_label, 'image'):
                del self.user_avatar_label.image
        try:
            # 保存引用以防止垃圾回收
            if not hasattr(self, 'avatar_image'):
                self.avatar_image = None
                
            # 保存当前的头像URL
            self.current_avatar_url = avatar_url
                
            # 创建一个线程来加载图片，避免阻塞UI
            threading.Thread(target=self._load_avatar_thread, args=(avatar_url,), daemon=True).start()
            
            if self.debug_var.get():
                self.log_debug(f"开始加载头像: {avatar_url[:60]}...")
            
        except Exception as e:
            error_msg = f"加载头像失败: {str(e)}"
            if self.debug_var.get():
                self.log_debug(error_msg, "error")
            else:
                print(f"[错误] {error_msg}")
            self.user_avatar_label.config(text="头像: 加载失败")
            
    def _load_avatar_thread(self, avatar_url):
        """在后台线程中加载头像"""
        try:
            # 生成缓存文件路径
            import hashlib
            url_hash = hashlib.md5(avatar_url.encode()).hexdigest()
            cache_path = os.path.join(self.cache_dir, f"avatar_{url_hash}.jpg")
            
            # 检查缓存是否存在
            if os.path.exists(cache_path):
                if self.debug_var.get():
                    self.log_debug(f"使用缓存的头像图片: {cache_path}")
                    
                # 直接从缓存加载图片
                pil_image = Image.open(cache_path)
                
                # 保存原始图像用于放大显示
                self.original_avatar = pil_image.copy()
                
                # 调整图像大小用于缩略图显示
                thumbnail = pil_image.resize((100, 100), Image.LANCZOS)
                tk_image = ImageTk.PhotoImage(thumbnail)
                
                # 在主线程中更新UI
                self.root.after(0, lambda: self._update_avatar_ui(tk_image, cache_path))
                return
                
            # 设置请求头，模拟浏览器
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://musicaldown.com/'
            }
            
            # 下载图片
            response = requests.get(avatar_url, headers=headers, timeout=10)
            response.raise_for_status()  # 如果请求失败，抛出异常
            
            # 将图片数据转换为PIL图像
            image_data = io.BytesIO(response.content)
            pil_image = Image.open(image_data)
            
            # 保存到缓存
            pil_image.save(cache_path)
            if self.debug_var.get():
                self.log_debug(f"头像已缓存到: {cache_path}")
                
            # 保存原始图像用于放大显示
            self.original_avatar = pil_image.copy()
            
            # 调整图像大小用于缩略图显示
            thumbnail = pil_image.resize((100, 100), Image.LANCZOS)
            tk_image = ImageTk.PhotoImage(thumbnail)
            
            # 在主线程中更新UI
            self.root.after(0, lambda: self._update_avatar_ui(tk_image, cache_path))
            
        except Exception as e:
            error_msg = f"加载头像线程出错: {str(e)}"
            if self.debug_var.get():
                self.log_debug(error_msg, "error")
            else:
                print(f"[错误] {error_msg}")
            self.root.after(0, lambda: self.user_avatar_label.config(text="头像: 加载失败"))
    
    def _update_avatar_ui(self, tk_image, cache_path):
        """在主线程中更新头像UI"""
        try:
            # 保存引用以防止垃圾回收
            self.avatar_image = tk_image
            self.avatar_cache_path = cache_path
            
            # 检查用户头像标签是否存在
            if not hasattr(self, 'user_avatar_label') or not self.user_avatar_label.winfo_exists():
                if self.debug_var.get():
                    self.log_debug("头像标签不存在，无法更新UI")
                return
                
            # 调整头像大小并显示在主界面
            img.thumbnail((100, 100))  # 设置合适的缩略图尺寸
            tk_image = ImageTk.PhotoImage(img)
            
            # 更新现有标签的图像
            self.user_avatar_label.config(image=tk_image, text="")
            self.user_avatar_label.image = tk_image  # 保持引用
            
            # 检查是否已经添加了放大按钮
            if not hasattr(self, 'zoom_button') or not self.zoom_button.winfo_exists():
                # 创建放大按钮（放在头像下方）
                parent = self.user_avatar_label.master
                avatar_button_frame = ttk.Frame(parent)
                avatar_button_frame.pack(fill=tk.X, pady=5)
                self.zoom_button = ttk.Button(avatar_button_frame, text="放大", width=5,
                                          command=self.show_large_avatar)
                self.zoom_button.pack(side=tk.LEFT, padx=5)
                
            if self.debug_var.get():
                self.log_debug("头像加载成功", "success")
            
        except Exception as e:
            error_msg = f"更新头像UI出错: {str(e)}"
            if self.debug_var.get():
                self.log_debug(error_msg, "error")
            else:
                print(f"[错误] {error_msg}")
            if hasattr(self, 'user_avatar_label') and self.user_avatar_label.winfo_exists():
                self.user_avatar_label.config(text="头像: 显示失败")
                
    def show_large_avatar(self):
        """显示大图头像"""
        try:
            if not hasattr(self, 'original_avatar') or not hasattr(self, 'avatar_cache_path'):
                messagebox.showinfo("提示", "头像尚未加载完成，请稍后再试。")
                return
                
            # 创建新窗口
            avatar_window = Toplevel(self.root)
            avatar_window.title("用户头像")
            avatar_window.geometry("600x750")  # 进一步增加窗口高度
            avatar_window.resizable(True, True)
            
            # 加载原始图像
            img = Image.open(self.avatar_cache_path)
            
            # 调整大小，保持比例 - 增加最大高度
            width, height = img.size
            max_size = 580  # 进一步增加图像显示尺寸，优先保证高度
            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))
                
            img = img.resize((new_width, new_height), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            # 显示图像
            img_label = ttk.Label(avatar_window, image=photo)
            img_label.photo = photo  # 保持引用
            img_label.pack(pady=10)
            
            # 添加用户信息
            if hasattr(self, 'current_avatar_url'):
                info_frame = ttk.Frame(avatar_window)
                info_frame.pack(fill=tk.X, padx=20, pady=10)
                
                # 显示用户名和昵称
                if hasattr(self, 'user_name_label'):
                    user_text = self.user_name_label.cget("text")
                    ttk.Label(info_frame, text=user_text, font=("Arial", 10, "bold")).pack(anchor=tk.W)
                
                # 创建按钮框架，确保按钮完整显示
            button_frame = ttk.Frame(avatar_window)
            button_frame.pack(fill=tk.X, padx=20, pady=10)
            
            # 添加关闭按钮，设置fill=tk.X确保完整显示
            ttk.Button(button_frame, text="关闭", command=avatar_window.destroy).pack(fill=tk.X, pady=5)
            
            # 添加打开用户主页按钮
            if hasattr(self, 'username_entry') and self.username_entry.get():
                username = self.username_entry.get()
                ttk.Button(button_frame, text=f"打开 @{username} 的主页", 
                         command=lambda: self.open_user_profile(username)).pack(fill=tk.X, pady=5)
            
        except Exception as e:
            error_msg = f"显示大图头像失败: {str(e)}"
            if self.debug_var.get():
                self.log_debug(error_msg, "error")
            else:
                print(f"[错误] {error_msg}")
            messagebox.showerror("错误", f"无法显示大图: {str(e)}")
            
    def open_user_profile(self, username):
        """打开用户TikTok主页"""
        if not username:
            messagebox.showinfo("提示", "用户名为空，无法打开主页。")
            return
            
        url = f"https://www.tiktok.com/@{username}"
        try:
            webbrowser.open(url)
            self.log_debug(f"已打开用户主页: {url}", "success")
        except Exception as e:
            error_msg = f"打开用户主页失败: {str(e)}"
            if self.debug_var.get():
                self.log_debug(error_msg, "error")
            else:
                print(f"[错误] {error_msg}")
            messagebox.showerror("错误", f"无法打开浏览器: {str(e)}")
            
    def copy_to_clipboard(self, text):
        """复制文本到剪贴板"""
        if not text:
            messagebox.showinfo("提示", "没有可复制的内容。")
            return
            
        try:
            # 清除剪贴板
            self.root.clipboard_clear()
            # 设置剪贴板内容
            self.root.clipboard_append(text)
            # 显示提示
            self.set_status("已复制到剪贴板")
            if self.debug_var.get():
                self.log_debug(f"已复制到剪贴板: {text[:30]}..." if len(text) > 30 else f"已复制到剪贴板: {text}", "success")
        except Exception as e:
            error_msg = f"复制到剪贴板失败: {str(e)}"
            if self.debug_var.get():
                self.log_debug(error_msg, "error")
            else:
                print(f"[错误] {error_msg}")
            messagebox.showerror("错误", f"无法复制到剪贴板: {str(e)}")

    def fetch_links_thread(self, url):
        try:
            # 显示调试信息
            if self.debug_var.get():
                self.log_debug(f"开始获取下载选项: {url}")
                
            # 获取下载选项和用户信息
            links, user_info = get_download_options(url)
            
            # 显示调试信息
            if self.debug_var.get():
                self.log_debug(f"获取到的下载选项数量: {len(links)}")
                for i, option in enumerate(links):
                    self.log_debug(f"选项 {i+1}: {option.get('text', '未知类型')} - {option.get('url', '无URL')}")
                self.log_debug(f"获取到的用户信息: {user_info}")
                
                # 同步用户名到输入框
                if user_info.get('username'):
                    self.root.after(0, lambda: self.username_entry.delete(0, tk.END))
                    self.root.after(0, lambda: self.username_entry.insert(0, user_info.get('username')))
                # 同时同步昵称作为备选
                elif user_info.get('nickname'):
                    self.root.after(0, lambda: self.username_entry.delete(0, tk.END))
                    self.root.after(0, lambda: self.username_entry.insert(0, user_info.get('nickname').lstrip('@')))
            
            # 检查是否只有MP3选项
            if len(links) == 1 and "MP3" in links[0].get('text', ''):
                self.log_debug("[警告] 只找到MP3下载选项，可能是网站结构已更改或反爬虫机制已升级", "error")
                
                # 尝试添加一个临时的视频下载选项用于测试
                if self.debug_var.get():
                    self.log_debug("添加临时视频下载选项用于测试")
                    links.append({
                        'text': '无水印视频 (测试)',
                        'url': url,  # 使用原始URL作为占位符
                        'is_test': True  # 标记为测试选项
                    })
            
            # 确保UI更新在主线程中执行
            self.root.after(0, lambda: self.display_download_options(links, user_info))
        except Exception as e:
            # 显示详细错误信息
            error_msg = f"获取下载链接失败: {str(e)}"
            if self.debug_var.get():
                self.log_debug(error_msg, "error")
                import traceback
                self.log_debug(f"错误详情: {traceback.format_exc()}", "error")
            else:
                print(f"[错误] {error_msg}")
            
            # 在主线程中显示错误
            self.set_status(error_msg)
            self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
        finally:
            # 在主线程中恢复按钮状态
            self.root.after(0, lambda: self.fetch_button.config(state=tk.NORMAL))

    def display_download_options(self, links, user_info=None):
        self.fetch_button.config(state=tk.NORMAL)
        if not links:
            self.set_status("获取失败，请检查链接或网络。")
            messagebox.showerror("失败", "未能获取到下载链接。请确认TikTok链接有效且公开。")
            return

        self.set_status(f"成功获取 {len(links)} 个下载选项。")
        
        # 如果没有提供用户信息，创建一个空字典
        if user_info is None:
            user_info = {
                'username': '',
                'nickname': '',
                'signature': '',
                'avatar_url': '',
                'video_desc': ''
            }
            
        # 清除上一次的结果
        for widget in self.options_frame.winfo_children():
            widget.destroy()
            
        # 创建主内容区域（使用Frame替代LabelFrame以便更灵活布局）
        main_content_frame = ttk.Frame(self.options_frame)
        main_content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建下载选项区域（左侧）
        download_frame = ttk.LabelFrame(main_content_frame, text="可用下载选项")
        download_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5), pady=5)
        
        # 创建固定的下载选项区域（不使用滚动条，因为只有4个固定选项）
        options_frame = ttk.Frame(download_frame)
        options_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建用户信息区域（右侧）
        self.user_info_frame = ttk.LabelFrame(main_content_frame, text="用户信息")
        self.user_info_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5, ipadx=10, ipady=10)
        
        # 用户信息区域的内容 - 确保user_avatar_label是类的属性
        self.user_avatar_label = ttk.Label(self.user_info_frame, text="头像加载中...")
        self.user_avatar_label.pack(pady=(10, 5))
        
        # 更新用户信息标签
        username = user_info.get('username', '')
        nickname = user_info.get('nickname', '')
        signature = user_info.get('signature', '')
        video_desc = user_info.get('video_desc', '')
        
        # 显示用户名/昵称（带框架）
        name_frame = ttk.Frame(self.user_info_frame)
        name_frame.pack(fill=tk.X, pady=5, anchor=tk.W)
        
        if nickname:
            self.user_name_label = ttk.Label(name_frame, text=f"昵称: {nickname}", font=("Arial", 10, "bold"))
        elif username:
            self.user_name_label = ttk.Label(name_frame, text=f"用户名: @{username}", font=("Arial", 10, "bold"))
        else:
            self.user_name_label = ttk.Label(name_frame, text="用户名: 未获取到", font=("Arial", 10, "bold"))
        self.user_name_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # 添加打开用户主页按钮
        if username:
            open_profile_button = ttk.Button(name_frame, text="打开主页", width=8,
                                         command=lambda: self.open_user_profile(username))
            open_profile_button.pack(side=tk.LEFT, padx=5)
        
        # 视频描述（使用签名内容替换）
        video_desc_frame = ttk.Frame(self.user_info_frame)
        video_desc_frame.pack(fill=tk.X, pady=5, anchor=tk.W)
        
        # 使用签名内容替换视频描述
        display_text = signature if signature else video_desc
        if display_text:
            self.user_video_info_label = ttk.Label(video_desc_frame, text=f"视频描述: {display_text}", wraplength=200)
        else:
            self.user_video_info_label = ttk.Label(video_desc_frame, text="视频描述: 未获取到", wraplength=200)
        self.user_video_info_label.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X)
        
        # 创建按钮容器（水平排列）
        button_container = ttk.Frame(self.user_info_frame)
        button_container.pack(fill=tk.X, pady=10)
        
        # 头像放大按钮（左侧）
        self.avatar_zoom_button = ttk.Button(button_container, text="放大", command=self.show_large_avatar)
        self.avatar_zoom_button.pack(side=tk.LEFT, padx=5)
        
        # 复制按钮（右侧）
        if display_text:
            copy_desc_button = ttk.Button(button_container, text="复制", width=5,
                                      command=lambda: self.copy_to_clipboard(display_text))
            copy_desc_button.pack(side=tk.RIGHT, padx=5)
        
        # 尝试加载头像
        avatar_url = user_info.get('avatar_url', '')
        if avatar_url:
            print(f"[Debug] 尝试加载头像: {avatar_url}")
            self.load_avatar_image(avatar_url)
        else:
            self.user_avatar_label.config(text="头像: 未获取到")
        
        # 添加下载选项（最多显示4个固定选项）
        max_options = min(len(links), 4)  # 最多显示4个选项
        for i in range(max_options):
            link_info = links[i]
            text = link_info['text']
            url = link_info['url']
            
            # 创建带边框的选项框
            option_frame = ttk.Frame(options_frame, relief=tk.GROOVE, borderwidth=1)
            option_frame.pack(fill=tk.X, pady=5, padx=5)
            
            # 选项编号
            num_label = ttk.Label(option_frame, text=f"选项 {i+1}", width=8)
            num_label.pack(side=tk.LEFT, padx=5, pady=8)
            
            # 显示选项类型
            option_label = ttk.Label(option_frame, text=text, width=25)
            option_label.pack(side=tk.LEFT, padx=5, pady=8)
            
            # 下载按钮
            if "MP3" in text:
                # MP3下载功能尚未实现
                btn = ttk.Button(option_frame, text="下载", width=10,
                               command=lambda: messagebox.showinfo("提示", "MP3下载功能正在开发中"))
            elif link_info.get('is_test', False):
                # 测试选项
                btn = ttk.Button(option_frame, text="测试下载", width=10,
                               command=lambda: messagebox.showinfo("测试", "这是一个测试选项，实际下载功能正在开发中"))
                # 如果是测试选项，添加标记
                test_label = ttk.Label(option_frame, text="[测试选项]", foreground="red")
                test_label.pack(side=tk.RIGHT, padx=5, pady=8)
            else:
                # 视频下载
                btn = ttk.Button(option_frame, text="下载", width=10,
                               command=lambda u=url, t=text: self.start_download(u, t))
                
            btn.pack(side=tk.RIGHT, padx=10, pady=8)
            
        # 在调试窗口中显示下载选项信息
        if self.debug_var.get():
            # 记录调试信息
            self.log_debug(f"找到 {len(links)} 个下载选项", "header")
            for i, link in enumerate(links):
                self.log_debug(f"选项 {i+1}: {link.get('text', '未知')} - {link.get('url', '无URL')[:60]}...")
            
            # 记录用户信息
            self.log_debug("用户信息:", "header")
            for key, value in user_info.items():
                if key == 'avatar_url' and value:
                    self.log_debug(f"  {key}: {value[:60]}...")
                else:
                    self.log_debug(f"  {key}: {value}")
                    
            # 显示调试窗口（如果尚未显示）
            if not self.debug_window or not self.debug_window.winfo_viewable():
                self.show_debug_window()

    def start_download(self, url, text):
        if "MP3" in text:
            messagebox.showinfo("提示", "MP3下载功能正在开发中。")
            return
            
        file_extension = ".mp4"
        file_name = f"tiktok_video_{text.replace(' ', '_')}{file_extension}"
        
        save_path = filedialog.asksaveasfilename(
            initialfile=file_name,
            defaultextension=file_extension,
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
        )
        
        if not save_path:
            self.set_status("下载已取消。")
            return
            
        self.set_status(f"开始下载: {text}...")
        self.progress_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        self.progress_bar['value'] = 0

        # 使用线程进行下载
        threading.Thread(target=self.download_file_thread, args=(url, save_path)).start()

    def download_file_thread(self, url, save_path):
        # 检查是否使用代理
        if hasattr(self, 'proxy_address') and self.proxy_address:
            success = download_file_with_proxy(url, save_path, self.proxy_address, self.update_progress)
        else:
            success = download_file(url, save_path, self.update_progress)
        
        if success:
            self.root.after(0, self.download_complete, save_path)
        else:
            self.root.after(0, self.download_failed)

    def update_progress(self, bytes_downloaded, total_size):
        if total_size > 0:
            percentage = (bytes_downloaded / total_size) * 100
            self.progress_bar['value'] = percentage
            self.set_status(f"下载中... {int(percentage)}%")
        else:
            self.set_status(f"下载中... {bytes_downloaded // 1024} KB")

    def download_complete(self, save_path):
        self.set_status("下载完成！")
        result = messagebox.askyesno("成功", f"视频已成功下载到：\n{save_path}\n\n是否打开文件所在目录？")
        if result:
            # 打开文件所在目录
            os.startfile(os.path.dirname(save_path))
        self.progress_bar.pack_forget()

    def download_failed(self):
        self.set_status("下载失败。")
        messagebox.showerror("错误", "下载过程中发生错误。")
        self.progress_bar.pack_forget()
    
    def cleanup_temp_files(self):
        """清理临时文件和目录"""
        try:
            if hasattr(self, 'cache_dir') and os.path.exists(self.cache_dir):
                print(f"[Debug] 清理缓存目录: {self.cache_dir}")
                shutil.rmtree(self.cache_dir, ignore_errors=True)
        except Exception as e:
            print(f"[错误] 清理缓存文件失败: {str(e)}")
    
    def show_debug_window(self):
        """在日志选项卡中显示调试信息"""
        # 创建文本区域和滚动条
        frame = ttk.Frame(self.log_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.debug_text = tk.Text(frame, wrap=tk.WORD, font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.debug_text.yview)
        
        self.debug_text.configure(yscrollcommand=scrollbar.set)
        self.debug_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 添加清除按钮
        clear_button = ttk.Button(self.log_tab, text="清除日志", 
                                command=lambda: self.debug_text.delete(1.0, tk.END))
        clear_button.pack(side=tk.BOTTOM, pady=5)
        
        # 配置标签和颜色
        self.debug_text.tag_configure("header", foreground="blue", font=("Consolas", 9, "bold"))
        self.debug_text.tag_configure("error", foreground="red")
        self.debug_text.tag_configure("success", foreground="green")
        
        # 添加初始内容
        self.debug_text.insert(tk.END, "=== 调试日志 ===\n", "header")
        self.debug_text.insert(tk.END, "调试日志已启动。\n")
    
    def log_debug(self, message, tag=None):
        """向调试窗口添加日志"""
        if self.debug_var.get():
            # 确保调试窗口已创建
            if not self.debug_text or not self.debug_text.winfo_exists():
                self.show_debug_window()
            
            # 添加时间戳和消息
            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"

            # 插入消息并应用标签
            self.debug_text.insert(tk.END, log_entry, tag)
            self.debug_text.see(tk.END)  # 滚动到底部

            # 同时打印到控制台
            print(message)
    
    def toggle_debug_mode(self):
        """切换调试模式并复制调试信息"""
        self.debug_var.set(not self.debug_var.get())
        if self.debug_var.get():
            # 切换到日志选项卡
            self.notebook.select(self.log_tab)
            self.show_debug_window()
            self.log_debug("调试模式已启用")
            self.debug_button.config(text="调试模式(开启)")
            # 复制调试信息到剪贴板
            if self.debug_text:
                debug_info = self.debug_text.get(1.0, tk.END)
                self.copy_to_clipboard(debug_info)
        else:
            self.log_debug("调试模式已禁用")
            self.debug_button.config(text="调试模式(关闭)")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()