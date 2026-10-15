class VideoIdHandler:
    """
    处理TikTok视频ID，将其转换为完整的TikTok URL
    """
    
    @staticmethod
    def build_url_from_id(video_id: str, username: str = None) -> str:
        """
        根据视频ID构建完整的TikTok URL
        
        Args:
            video_id (str): TikTok视频ID
            username (str, optional): TikTok用户名，如果不提供则使用占位符
            
        Returns:
            str: 完整的TikTok URL
        """
        # 移除可能的空格和特殊字符
        video_id = video_id.strip()
        
        # 如果用户名未提供，使用占位符
        if not username or username.strip() == "":
            username = "placeholder"
        else:
            username = username.strip()
            # 确保用户名格式正确（移除@符号如果存在）
            if username.startswith("@"):
                username = username[1:]
        
        # 构建完整URL
        return f"https://www.tiktok.com/@{username}/video/{video_id}"
    
    @staticmethod
    def is_valid_video_id(video_id: str) -> bool:
        """
        检查视频ID是否有效
        
        Args:
            video_id (str): 要检查的视频ID
            
        Returns:
            bool: 如果ID看起来有效则返回True
        """
        # 移除空格
        video_id = video_id.strip()
        
        # 检查是否为空
        if not video_id:
            return False
        
        # TikTok视频ID通常是数字，长度约为19位
        # 这里做一个简单的长度检查
        if len(video_id) < 5:
            return False
            
        # 检查是否只包含数字
        if not video_id.isdigit():
            return False
            
        return True