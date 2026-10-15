import tkinter as tk
from tkinter import ttk, messagebox
import threading
from video_id_handler import VideoIdHandler
from downloader_core import get_download_options

class VideoIdFrame(ttk.Frame):
    """
    处理视频ID输入和URL构建的GUI组件
    """
    def __init__(self, parent, app_instance):
        super().__init__(parent, padding="10")
        self.app = app_instance  # 保存对主应用的引用
        
        # 创建UI组件
        self.create_widgets()
        
    def create_widgets(self):
        # 视频ID输入部分
        self.id_label = ttk.Label(self, text="TikTok视频ID:")
        self.id_label.pack(side=tk.LEFT, padx=5)
        
        self.id_entry = ttk.Entry(self, width=20)
        self.id_entry.pack(side=tk.LEFT, padx=5)
        
        # 可选的用户名输入
        self.username_var = tk.StringVar()
        self.username_check = ttk.Checkbutton(self, text="指定用户名", 
                                           command=self.toggle_username_entry,
                                           variable=self.username_var, onvalue="1", offvalue="0")
        self.username_check.pack(side=tk.LEFT, padx=5)
        
        # 用户名输入框（默认隐藏）
        self.username_entry = ttk.Entry(self, width=15)
        
        # 获取链接按钮
        self.fetch_button = ttk.Button(self, text="通过ID获取链接", command=self.process_video_id)
        self.fetch_button.pack(side=tk.LEFT, padx=5)
    
    def toggle_username_entry(self):
        """切换用户名输入框的显示状态"""
        if self.username_var.get() == "1":
            self.username_entry.pack(side=tk.LEFT, padx=5, before=self.fetch_button)
        else:
            self.username_entry.pack_forget()
    
    def process_video_id(self):
        """处理视频ID并构建URL"""
        video_id = self.id_entry.get().strip()
        
        # 验证视频ID
        if not VideoIdHandler.is_valid_video_id(video_id):
            messagebox.showerror("错误", "请输入有效的TikTok视频ID！\n视频ID应该是一串数字。")
            return
        
        # 获取用户名（如果提供）
        username = None
        if self.username_var.get() == "1":
            username = self.username_entry.get().strip()
        
        # 构建完整URL
        full_url = VideoIdHandler.build_url_from_id(video_id, username)
        
        # 显示调试信息
        if hasattr(self.app, 'debug_var') and self.app.debug_var.get():
            print(f"[Debug] 从视频ID构建URL: {full_url}")
        
        # 将URL设置到主应用的URL输入框
        if hasattr(self.app, 'url_entry'):
            self.app.url_entry.delete(0, tk.END)
            self.app.url_entry.insert(0, full_url)
            
            # 自动触发获取链接
            self.app.start_fetching()
        else:
            # 如果无法访问主应用的URL输入框，直接处理URL
            self.fetch_button.config(state=tk.DISABLED)
            if hasattr(self.app, 'set_status'):
                self.app.set_status("正在获取下载链接，请稍候...")
            if hasattr(self.app, 'clear_options'):
                self.app.clear_options()
            
            # 使用线程以防止UI卡死
            threading.Thread(target=self.fetch_links_thread, args=(full_url,)).start()
    
    def fetch_links_thread(self, url):
        """在单独的线程中获取下载链接"""
        try:
            links = get_download_options(url)
            
            # 确保UI更新在主线程中执行
            if hasattr(self.app, 'root'):
                self.app.root.after(0, self.app.display_download_options, links)
            
        except Exception as e:
            print(f"[错误] 获取下载链接时出错: {str(e)}")
            import traceback
            print(traceback.format_exc())
            
            # 在主线程中显示错误消息
            if hasattr(self.app, 'root'):
                self.app.root.after(0, lambda: messagebox.showerror("错误", f"获取下载链接时出错: {str(e)}"))
        finally:
            # 恢复按钮状态
            if hasattr(self.app, 'root'):
                self.app.root.after(0, lambda: self.fetch_button.config(state=tk.NORMAL))
            if hasattr(self.app, 'set_status'):
                self.app.root.after(0, lambda: self.app.set_status("准备就绪..."))