import requests
from bs4 import BeautifulSoup
import random
import warnings

# 忽略BeautifulSoup的警告
warnings.filterwarnings("ignore", category=UserWarning, module='bs4')

# 准备一个User-Agent列表，从中随机选择
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
]

def get_random_headers():
    """返回一个包含随机User-Agent和常用头的字典"""
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        # 'Referer' 字段非常重要，它告诉服务器请求是从哪个页面发起的
        'Referer': 'https://musicaldown.com/en' 
    }
    return headers

def get_download_options(tiktok_url: str) -> tuple[list[dict], dict]:
    """
    核心函数：先获取动态令牌，再提交TikTok URL并解析返回的下载选项和用户信息。

    Args:
        tiktok_url (str): 用户输入的TikTok视频链接。

    Returns:
        tuple: 包含两个元素：
            - list[dict]: 一个包含下载选项的列表。每个选项是一个字典，
                        格式为 {'text': '按钮文本', 'url': '下载链接'}.
            - dict: 用户信息字典，包含用户名、签名、头像URL等信息。
                  如果无法获取，则为空字典。
    """
    # 初始化用户信息字典
    user_info = {
        'username': '',
        'nickname': '',
        'signature': '',
        'avatar_url': '',
        'video_desc': ''
    }
    
    # 尝试使用主要方法获取下载链接和用户信息
    try:
        download_links, user_info_main = get_download_options_musicaldown(tiktok_url)
        if user_info_main:
            user_info.update(user_info_main)
        if download_links and len(download_links) > 1:  # 如果找到了多个下载选项，直接返回
            return download_links, user_info
    except Exception as e:
        print(f"[错误] 主要下载方法失败: {str(e)}")
        import traceback
        print(f"[Debug] 错误详情: {traceback.format_exc()}")
    
    # 如果主要方法失败或只找到MP3选项，尝试备用方法
    try:
        print("[Debug] 尝试使用备用下载方法...")
        backup_links, user_info_backup = get_download_options_backup(tiktok_url)
        if user_info_backup:
            user_info.update(user_info_backup)
        if backup_links:
            return backup_links, user_info
    except Exception as e:
        print(f"[错误] 备用下载方法失败: {str(e)}")
        import traceback
        print(f"[Debug] 错误详情: {traceback.format_exc()}")
    
    # 如果所有方法都失败，返回一个占位符选项和空的用户信息
    print("[警告] 所有下载方法都失败，返回占位符选项")
    return [{
        'text': 'MP3 (仅可用选项)',
        'url': 'https://musicaldown.com/mp3/download'
    }], user_info


def get_download_options_musicaldown(tiktok_url: str) -> tuple[list[dict], dict]:
    """使用musicaldown.com获取TikTok视频的下载选项和用户信息
    
    Args:
        tiktok_url (str): 用户输入的TikTok视频链接。
        
    Returns:
        tuple: 包含两个元素：
            - list[dict]: 下载选项列表
            - dict: 用户信息字典
    """
    session = requests.Session() # 使用Session来保持cookie和连接
    session.headers.update(get_random_headers())

    try:
        print(f"[Debug] 开始处理TikTok URL: {tiktok_url}")
        print(f"[Debug] 使用的请求头: {session.headers}")
        
        # --- 第一步：访问主页，获取动态令牌 ---
        main_page_url = "https://musicaldown.com/en"
        print(f"[Debug] 正在访问主页: {main_page_url}")
        main_page_response = session.get(main_page_url)
        main_page_response.raise_for_status()
        
        # 打印主页HTML内容片段，用于调试
        print("[Debug] 主页HTML内容片段:")
        print(main_page_response.text[:300] + "..." if len(main_page_response.text) > 300 else main_page_response.text)
        
        soup_main = BeautifulSoup(main_page_response.text, 'html.parser')
        
        # 查找所有隐藏的input标签，并提取其name和value
        hidden_inputs = soup_main.select('form#submit-form input[type="hidden"]')
        print(f"[Debug] 找到隐藏输入字段数量: {len(hidden_inputs)}")
        payload = {input_tag['name']: input_tag.get('value', '') for input_tag in hidden_inputs}
        
        # 查找URL输入框的name属性
        url_input = soup_main.select_one('form#submit-form input[type="text"]')
        if url_input and 'name' in url_input.attrs:
            url_input_name = url_input['name']
            print(f"[Debug] 找到URL输入框name属性: {url_input_name}")
        else:
            # 如果找不到，使用默认值
            url_input_name = "link"
            print(f"[Debug] 未找到URL输入框，使用默认name: {url_input_name}")
            
            # 尝试查找所有表单
            all_forms = soup_main.find_all('form')
            print(f"[Debug] 网页中共有 {len(all_forms)} 个表单")
            for i, form in enumerate(all_forms):
                print(f"[Debug] 表单 {i+1} ID: {form.get('id')}, 操作: {form.get('action')}")
        
        # 将TikTok链接加入payload
        payload[url_input_name] = tiktok_url
        print(f"[Debug] 最终表单数据: {payload}")

        # --- 第二步：使用获取到的动态数据提交POST请求 ---
        # 获取表单的action属性，即提交地址
        form = soup_main.select_one('form#submit-form')
        if form and 'action' in form.attrs:
            post_url = form['action']
            print(f"[Debug] 找到表单提交地址: {post_url}")
            # 如果是相对URL，转换为绝对URL
            if not post_url.startswith('http'):
                post_url = f"https://musicaldown.com{post_url if post_url.startswith('/') else '/' + post_url}"
                print(f"[Debug] 转换为绝对URL: {post_url}")
        else:
            # 使用默认值
            post_url = "https://musicaldown.com/download"
            print(f"[Debug] 未找到表单提交地址，使用默认值: {post_url}")
        
        print(f"[Debug] 正在提交表单到: {post_url}")
        response = session.post(post_url, data=payload)
        response.raise_for_status()

        return parse_musicaldown_response(response, session)

    except requests.exceptions.RequestException as e:
        print(f"[Error] 请求musicaldown时出错: {e}")
        raise
    except Exception as e:
        print(f"[Error] 解析HTML时出错: {e}")
        raise


def parse_musicaldown_response(response, session) -> tuple[list[dict], dict]:
    """解析musicaldown.com的响应，提取下载链接和用户信息
    
    Args:
        response: 请求响应对象
        session: 请求会话对象
        
    Returns:
        tuple: 包含两个元素：
            - list[dict]: 下载选项列表，每个选项是一个字典，包含'text'和'url'键
            - dict: 用户信息字典，包含用户名、签名、头像URL等信息
    """
    try:
        # 使用BeautifulSoup解析HTML
        soup_result = BeautifulSoup(response.text, 'html.parser')
        
        # 打印HTML内容，用于调试
        print("[Debug] 接收到的HTML内容:")
        print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
        
        download_links = []

        # 查找所有下载按钮，尝试多种选择器
        # 1. 首先尝试原始的选择器
        link_elements = soup_result.find_all('a', class_='btn download')
        print(f"[Debug] 使用'a.btn.download'找到的元素数量: {len(link_elements)}")
        
        # 2. 如果没有找到，尝试其他可能的选择器
        if not link_elements:
            link_elements = soup_result.find_all('a', class_='download')
            print(f"[Debug] 使用'a.download'找到的元素数量: {len(link_elements)}")
            
        if not link_elements:
            link_elements = soup_result.find_all('a', class_='btn')
            print(f"[Debug] 使用'a.btn'找到的元素数量: {len(link_elements)}")
            
        if not link_elements:
            # 尝试查找所有包含'download'文本的链接
            link_elements = [a for a in soup_result.find_all('a') if 'download' in a.get_text().lower()]
            print(f"[Debug] 使用文本包含'download'的链接找到的元素数量: {len(link_elements)}")
            
        # 如果仍然没有找到，尝试查找所有链接
        if not link_elements:
            all_links = soup_result.find_all('a')
            print(f"[Debug] 找到所有链接数量: {len(all_links)}")
            print("[Debug] 所有链接:")
            for i, a in enumerate(all_links[:10]):  # 只打印前10个
                print(f"  {i+1}. 文本='{a.get_text(strip=True)}', href='{a.get('href')}'")    
             
        # 打印找到的所有链接，用于调试
        for i, element in enumerate(link_elements):
            print(f"[Debug] 链接 {i+1}: 文本='{element.get_text(strip=True)}', href='{element.get('href')}'")        
        
        for element in link_elements:
            link_text = element.get_text(strip=True)
            link_url = element.get('href')
            
            # 处理相对URL
            if link_url and not link_url.startswith('http'):
                link_url = f"https://musicaldown.com{link_url if link_url.startswith('/') else '/' + link_url}"
                
            if link_url:
                download_links.append({
                    'text': link_text,
                    'url': link_url
                })
        
        # 查找MP3下载表单
        mp3_form = soup_result.find('form', action='/mp3/download')
        if mp3_form:
            print("[Debug] 找到MP3下载表单")
            download_links.append({
                'text': 'Download MP3',
                'url': 'https://musicaldown.com/mp3/download' # 这是一个占位符
            })
        
        # 如果没有找到任何下载链接，尝试查找所有可能的下载按钮或链接
        if not download_links:
            print("[Debug] 未找到标准下载链接，尝试查找其他可能的下载选项...")
            
            # 尝试查找包含特定关键词的按钮或链接
            keywords = ['download', 'video', 'mp4', 'hd', 'no watermark', '无水印']
            for keyword in keywords:
                elements = [a for a in soup_result.find_all(['a', 'button']) 
                           if keyword in a.get_text().lower()]
                print(f"[Debug] 关键词'{keyword}'找到元素数量: {len(elements)}")
                
                for element in elements:
                    if element.name == 'a' and element.get('href'):
                        link_url = element.get('href')
                        if not link_url.startswith('http'):
                            link_url = f"https://musicaldown.com{link_url if link_url.startswith('/') else '/' + link_url}"
                        
                        link_text = element.get_text(strip=True) or f"下载 ({keyword})"
                        
                        # 检查是否已经添加过相同的URL
                        if not any(link['url'] == link_url for link in download_links):
                            download_links.append({
                                'text': link_text,
                                'url': link_url
                            })
                            print(f"[Debug] 添加额外下载选项: {link_text} - {link_url}")
            
            # 尝试查找视频元素
            video_elements = soup_result.find_all('video')
            print(f"[Debug] 找到视频元素数量: {len(video_elements)}")
            
            for i, video in enumerate(video_elements):
                source = video.find('source')
                if source and source.get('src'):
                    video_url = source.get('src')
                    if not video_url.startswith('http'):
                        video_url = f"https://musicaldown.com{video_url if video_url.startswith('/') else '/' + video_url}"
                    
                    download_links.append({
                        'text': f"视频 {i+1}",
                        'url': video_url
                    })
                    print(f"[Debug] 从视频元素添加下载选项: 视频 {i+1} - {video_url}")
        
        print(f"[Debug] 最终找到的下载选项数量: {len(download_links)}")
        for i, link in enumerate(download_links):
            print(f"[Debug] 选项 {i+1}: {link['text']} - {link['url']}")
        
        # 提取用户信息
        user_info = {
            'username': '',
            'nickname': '',
            'signature': '',
            'avatar_url': '',
            'video_desc': ''
        }
        
        try:
            # 尝试提取用户信息
            print("[Debug] 尝试提取用户信息...")
            
            # 查找用户头像
            avatar_img = soup_result.select_one('.video-header img, .img-area img, .author-img img')
            if avatar_img and avatar_img.get('src'):
                avatar_url = avatar_img.get('src')
                if not avatar_url.startswith('http'):
                    avatar_url = f"https://musicaldown.com{avatar_url if avatar_url.startswith('/') else '/' + avatar_url}"
                user_info['avatar_url'] = avatar_url
                print(f"[Debug] 找到用户头像: {avatar_url[:50]}...")
            
            # 查找用户名/昵称
            author_elem = soup_result.select_one('.video-author, .author-name, .nickname')
            if author_elem:
                user_info['nickname'] = author_elem.get_text(strip=True)
                print(f"[Debug] 找到用户昵称: {user_info['nickname']}")
            
            # 查找用户签名/描述
            desc_elem = soup_result.select_one('.video-desc, .description, .signature')
            if desc_elem:
                user_info['signature'] = desc_elem.get_text(strip=True)
                print(f"[Debug] 找到用户签名: {user_info['signature']}")
            
            # 查找视频描述
            video_desc_elem = soup_result.select_one('.video-info, .video-description')
            if video_desc_elem:
                user_info['video_desc'] = video_desc_elem.get_text(strip=True)
                print(f"[Debug] 找到视频描述: {user_info['video_desc']}")
                
            # 从URL中提取用户名
            if tiktok_url and '@' in tiktok_url:
                username = tiktok_url.split('@')[1].split('/')[0]
                user_info['username'] = username
                print(f"[Debug] 从URL提取用户名: {username}")
                
        except Exception as e:
            print(f"[警告] 提取用户信息时出错: {str(e)}")
            # 错误不影响主要功能，继续执行
            
        return download_links, user_info
    except Exception as e:
        print(f"[错误] 解析musicaldown响应时出错: {str(e)}")
        import traceback
        print(f"[Debug] 错误详情: {traceback.format_exc()}")
        raise


def get_download_options_backup(tiktok_url: str) -> tuple[list[dict], dict]:
    """使用备用网站获取TikTok视频的下载选项和用户信息
    
    Args:
        tiktok_url (str): 用户输入的TikTok视频链接。
        
    Returns:
        tuple: 包含两个元素：
            - list[dict]: 下载选项列表
            - dict: 用户信息字典
    """
    # 使用另一个无水印下载网站作为备选
    session = requests.Session()
    session.headers.update(get_random_headers())
    
    try:
        print(f"[Debug] 使用备用方法处理URL: {tiktok_url}")
        
        # 使用ssstik.io作为备用
        api_url = "https://ssstik.io/abc?url=dl"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://ssstik.io',
            'Referer': 'https://ssstik.io/'
        }
        
        # 首先访问主页获取必要的cookies和tokens
        print("[Debug] 访问备用网站主页")
        main_response = session.get("https://ssstik.io/")
        main_response.raise_for_status()
        
        soup = BeautifulSoup(main_response.text, 'html.parser')
        
        # 查找表单中的隐藏字段
        tt_token = ""
        form = soup.find('form', {'id': 'mainform'})
        if form:
            token_input = form.find('input', {'name': 'tt'})
            if token_input:
                tt_token = token_input.get('value', '')
                print(f"[Debug] 找到token: {tt_token[:10]}...")
        
        # 准备表单数据
        data = {
            'id': tiktok_url,
            'locale': 'en',
            'tt': tt_token
        }
        
        print("[Debug] 提交TikTok URL到备用网站")
        response = session.post(api_url, headers=headers, data=data)
        response.raise_for_status()
        
        # 解析响应
        soup_result = BeautifulSoup(response.text, 'html.parser')
        
        download_links = []
        
        # 查找所有下载按钮
        download_buttons = soup_result.select('a.download-file')
        print(f"[Debug] 备用网站找到下载按钮数量: {len(download_buttons)}")
        
        for button in download_buttons:
            link_text = button.get_text(strip=True)
            link_url = button.get('href')
            
            if link_url and link_url.startswith('http'):
                download_links.append({
                    'text': link_text or "无水印视频 (备用)",
                    'url': link_url
                })
                print(f"[Debug] 添加备用下载选项: {link_text} - {link_url[:50]}...")
        
        # 如果没有找到下载链接，尝试查找视频元素
        if not download_links:
            video_elements = soup_result.find_all('video')
            print(f"[Debug] 找到视频元素数量: {len(video_elements)}")
            
            for i, video in enumerate(video_elements):
                source = video.find('source')
                if source and source.get('src'):
                    video_url = source.get('src')
                    download_links.append({
                        'text': f"无水印视频 {i+1} (备用)",
                        'url': video_url
                    })
                    print(f"[Debug] 从视频元素添加下载选项: 视频 {i+1} - {video_url[:50]}...")
        
        # 提取用户信息
        user_info = {
            'username': '',
            'nickname': '',
            'signature': '',
            'avatar_url': '',
            'video_desc': ''
        }
        
        try:
            # 尝试提取用户信息
            print("[Debug] 尝试从备用网站提取用户信息...")
            
            # 查找用户头像
            avatar_img = soup_result.select_one('.user-avatar img, .author-img img')
            if avatar_img and avatar_img.get('src'):
                user_info['avatar_url'] = avatar_img.get('src')
                print(f"[Debug] 找到用户头像: {user_info['avatar_url'][:50]}...")
            
            # 查找用户名/昵称
            author_elem = soup_result.select_one('.user-name, .author-name')
            if author_elem:
                user_info['nickname'] = author_elem.get_text(strip=True)
                print(f"[Debug] 找到用户昵称: {user_info['nickname']}")
            
            # 查找用户签名/描述
            desc_elem = soup_result.select_one('.user-desc, .author-desc')
            if desc_elem:
                user_info['signature'] = desc_elem.get_text(strip=True)
                print(f"[Debug] 找到用户签名: {user_info['signature']}")
                
            # 从URL中提取用户名
            if tiktok_url and '@' in tiktok_url:
                username = tiktok_url.split('@')[1].split('/')[0]
                user_info['username'] = username
                print(f"[Debug] 从URL提取用户名: {username}")
                
        except Exception as e:
            print(f"[警告] 提取用户信息时出错: {str(e)}")
            # 错误不影响主要功能，继续执行
        
        return download_links, user_info
    
    except Exception as e:
        print(f"[错误] 备用方法出错: {str(e)}")
        raise


def download_file(url: str, save_path: str, progress_callback=None):
    """
    从给定的URL下载文件，并支持进度回调。

    Args:
        url (str): 文件的直接下载链接。
        save_path (str): 本地保存路径（包含文件名）。
        progress_callback (function, optional): 用于更新进度的回调函数。
                                                它接收(当前已下载字节, 文件总大小)。
    """
    try:
        response = requests.get(url, stream=True, headers=get_random_headers(), timeout=30)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        bytes_downloaded = 0
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                bytes_downloaded += len(chunk)
                if progress_callback:
                    # 调用回调函数更新UI
                    progress_callback(bytes_downloaded, total_size)

        return True # 表示下载成功

    except requests.exceptions.RequestException as e:
        print(f"[Error] 下载文件时出错: {e}")
        return False


def download_file_with_proxy(url: str, save_path: str, proxy_address: str, progress_callback=None):
    """
    使用代理从给定的URL下载文件，并支持进度回调。

    Args:
        url (str): 文件的直接下载链接。
        save_path (str): 本地保存路径（包含文件名）。
        proxy_address (str): 代理服务器地址，格式为 "http://user:password@proxy.example.com:8080"。
        progress_callback (function, optional): 用于更新进度的回调函数。
    """
    proxies = {
       "http": proxy_address,
       "https": proxy_address,
    }

    try:
        response = requests.get(url, stream=True, headers=get_random_headers(), 
                               proxies=proxies, timeout=30)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        bytes_downloaded = 0
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                bytes_downloaded += len(chunk)
                if progress_callback:
                    # 调用回调函数更新UI
                    progress_callback(bytes_downloaded, total_size)

        return True # 表示下载成功

    except requests.exceptions.RequestException as e:
        print(f"[Error] 通过代理下载文件时出错: {e}")
        return False