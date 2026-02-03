"""
WinMsgHub - 更新检查器
作者：青云制作_彭明航
"""

import requests
from typing import Optional, Dict, Any
from packaging import version
from utils.logger import get_logger

logger = get_logger('UpdateChecker')


class UpdateChecker:
    """更新检查器 - 检查GitHub Release"""
    
    # 当前版本
    CURRENT_VERSION = "1.1.0"
    
    # GitHub仓库信息
    GITHUB_OWNER = "pmh1314520"
    GITHUB_REPO = "WinMsgHub"
    
    # API端点
    RELEASE_API = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
    
    @classmethod
    def check_update(cls, timeout: int = 5) -> Optional[Dict[str, Any]]:
        """
        检查是否有新版本
        
        Args:
            timeout: 请求超时时间（秒）
            
        Returns:
            如果有新版本，返回包含更新信息的字典：
            {
                'has_update': True,
                'latest_version': '1.1.0',
                'current_version': '1.0.0',
                'release_url': 'https://github.com/...',
                'release_notes': '更新内容...',
                'download_url': 'https://github.com/.../releases/download/...'
            }
            如果没有新版本或检查失败，返回None
        """
        try:
            logger.info("开始检查更新...")
            
            # 发送请求
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': f'{cls.GITHUB_REPO}/{cls.CURRENT_VERSION}'
            }
            
            response = requests.get(
                cls.RELEASE_API,
                headers=headers,
                timeout=timeout
            )
            
            # 检查响应状态
            if response.status_code != 200:
                logger.warning(f"检查更新失败，状态码：{response.status_code}")
                return None
            
            # 解析响应
            release_data = response.json()
            
            # 获取最新版本号（去掉v前缀）
            latest_version = release_data.get('tag_name', '').lstrip('v')
            if not latest_version:
                logger.warning("无法获取最新版本号")
                return None
            
            # 比较版本
            try:
                current = version.parse(cls.CURRENT_VERSION)
                latest = version.parse(latest_version)
                
                if latest > current:
                    logger.info(f"发现新版本：{latest_version}")
                    
                    # 构建更新信息
                    update_info = {
                        'has_update': True,
                        'latest_version': latest_version,
                        'current_version': cls.CURRENT_VERSION,
                        'release_url': release_data.get('html_url', ''),
                        'release_notes': release_data.get('body', '暂无更新说明'),
                        'download_url': release_data.get('html_url', ''),
                        'published_at': release_data.get('published_at', '')
                    }
                    
                    # 尝试获取下载链接
                    assets = release_data.get('assets', [])
                    if assets:
                        # 优先选择.exe文件
                        for asset in assets:
                            if asset.get('name', '').endswith('.exe'):
                                update_info['download_url'] = asset.get('browser_download_url', '')
                                break
                    
                    return update_info
                else:
                    logger.info(f"当前已是最新版本：{cls.CURRENT_VERSION}")
                    return None
                    
            except Exception as e:
                logger.error(f"版本比较失败：{e}")
                return None
                
        except requests.Timeout:
            logger.warning("检查更新超时")
            return None
        except requests.RequestException as e:
            logger.warning(f"检查更新失败：{e}")
            return None
        except Exception as e:
            logger.error(f"检查更新时发生错误：{e}")
            return None
    
    @classmethod
    def get_current_version(cls) -> str:
        """获取当前版本号"""
        return cls.CURRENT_VERSION
    
    @classmethod
    def get_github_url(cls) -> str:
        """获取GitHub仓库URL"""
        return f"https://github.com/{cls.GITHUB_OWNER}/{cls.GITHUB_REPO}"
    
    @classmethod
    def get_releases_url(cls) -> str:
        """获取GitHub Releases页面URL"""
        return f"{cls.get_github_url()}/releases"
