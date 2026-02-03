"""
WinMsgHub - SVG图标提供器
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""

from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QByteArray, Qt


class IconProvider:
    """SVG图标提供器 - 不使用emoji"""
    
    @staticmethod
    def get_svg_icon(svg_data: str, color: str = "#4A9EFF", size: int = 20) -> QIcon:
        """
        从SVG数据创建图标
        :param svg_data: SVG XML字符串
        :param color: 图标颜色
        :param size: 图标大小
        """
        # 替换颜色
        svg_data = svg_data.replace("currentColor", color)
        
        # 创建SVG渲染器
        svg_bytes = QByteArray(svg_data.encode())
        renderer = QSvgRenderer(svg_bytes)
        
        # 创建pixmap
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        # 渲染SVG
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        return QIcon(pixmap)
    
    # ========== 导航图标 ==========
    
    @staticmethod
    def dashboard_icon(color: str = "#4A9EFF") -> QIcon:
        """仪表盘图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="7" height="7" rx="1"/>
            <rect x="14" y="3" width="7" height="7" rx="1"/>
            <rect x="14" y="14" width="7" height="7" rx="1"/>
            <rect x="3" y="14" width="7" height="7" rx="1"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def history_icon(color: str = "#4A9EFF") -> QIcon:
        """历史图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def sources_icon(color: str = "#4A9EFF") -> QIcon:
        """消息源图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
            <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
            <line x1="12" y1="22.08" x2="12" y2="12"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def popup_icon(color: str = "#4A9EFF") -> QIcon:
        """弹窗图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def theme_icon(color: str = "#4A9EFF") -> QIcon:
        """主题图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="5"/>
            <line x1="12" y1="1" x2="12" y2="3"/>
            <line x1="12" y1="21" x2="12" y2="23"/>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
            <line x1="1" y1="12" x2="3" y2="12"/>
            <line x1="21" y1="12" x2="23" y2="12"/>
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def filter_icon(color: str = "#4A9EFF") -> QIcon:
        """过滤图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def data_icon(color: str = "#4A9EFF") -> QIcon:
        """数据图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <ellipse cx="12" cy="5" rx="9" ry="3"/>
            <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
            <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def about_icon(color: str = "#4A9EFF") -> QIcon:
        """关于图标 - 圆圈中的i"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="11" x2="12" y2="16" stroke-linecap="round"/>
            <circle cx="12" cy="8" r="0.5" fill="currentColor"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def settings_icon(color: str = "#4A9EFF") -> QIcon:
        """系统设置图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"/>
            <path d="M12 1v6m0 6v6m8.66-15.66l-4.24 4.24m-4.24 4.24l-4.24 4.24M23 12h-6m-6 0H1m20.66 8.66l-4.24-4.24m-4.24-4.24l-4.24-4.24"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    # ========== 统计图标 ==========
    
    @staticmethod
    def message_icon(color: str = "#4A9EFF") -> QIcon:
        """消息图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def check_icon(color: str = "#98C379") -> QIcon:
        """检查图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def settings_icon(color: str = "#4A9EFF") -> QIcon:
        """设置图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"/>
            <path d="M12 1v6m0 6v6m5.2-13.2l-4.2 4.2m-2 2l-4.2 4.2M23 12h-6m-6 0H1m18.2 5.2l-4.2-4.2m-2-2l-4.2-4.2"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    # ========== 操作图标 ==========
    
    @staticmethod
    def add_icon(color: str = "#4A9EFF") -> QIcon:
        """添加图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def edit_icon(color: str = "#4A9EFF") -> QIcon:
        """编辑图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def delete_icon(color: str = "#E06C75") -> QIcon:
        """删除图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
            <line x1="10" y1="11" x2="10" y2="17"/>
            <line x1="14" y1="11" x2="14" y2="17"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def save_icon(color: str = "#98C379") -> QIcon:
        """保存图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
            <polyline points="17 21 17 13 7 13 7 21"/>
            <polyline points="7 3 7 8 15 8"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def refresh_icon(color: str = "#4A9EFF") -> QIcon:
        """刷新图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10"/>
            <polyline points="1 20 1 14 7 14"/>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def search_icon(color: str = "#4A9EFF") -> QIcon:
        """搜索图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def download_icon(color: str = "#4A9EFF") -> QIcon:
        """下载图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def upload_icon(color: str = "#4A9EFF") -> QIcon:
        """上传图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def copy_icon(color: str = "#4A9EFF") -> QIcon:
        """复制图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def close_icon(color: str = "#E06C75") -> QIcon:
        """关闭图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    # ========== 状态图标 ==========
    
    @staticmethod
    def success_icon(color: str = "#98C379") -> QIcon:
        """成功图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="16 8 10 14 8 12"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def warning_icon(color: str = "#E5C07B") -> QIcon:
        """警告图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def error_icon(color: str = "#E06C75") -> QIcon:
        """错误图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def info_icon(color: str = "#61AFEF") -> QIcon:
        """信息图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="16" x2="12" y2="12"/>
            <line x1="12" y1="8" x2="12.01" y2="8"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    # ========== 其他图标 ==========
    
    @staticmethod
    def link_icon(color: str = "#4A9EFF") -> QIcon:
        """链接图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
            <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def star_icon(color: str = "#E5C07B") -> QIcon:
        """星标图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def bell_icon(color: str = "#4A9EFF") -> QIcon:
        """通知图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def user_icon(color: str = "#4A9EFF") -> QIcon:
        """用户图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
            <circle cx="12" cy="7" r="4"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def folder_icon(color: str = "#4A9EFF") -> QIcon:
        """文件夹图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def file_icon(color: str = "#4A9EFF") -> QIcon:
        """文件图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/>
            <polyline points="13 2 13 9 20 9"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def timer_icon(color: str = "#4A9EFF") -> QIcon:
        """定时器图标 - 用于定时弹窗"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="13" r="8"/>
            <path d="M12 9v4l2 2"/>
            <path d="M16.51 17.35l-.35 3.83a2 2 0 0 1-2 1.82H9.83a2 2 0 0 1-2-1.82l-.35-3.83m.01-10.7l.35-3.83A2 2 0 0 1 9.83 1h4.35a2 2 0 0 1 2 1.82l.35 3.83"/>
            <path d="M9 1h6"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def calendar_icon(color: str = "#4A9EFF") -> QIcon:
        """日历图标 - 备用定时图标"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
            <line x1="16" y1="2" x2="16" y2="6"/>
            <line x1="8" y1="2" x2="8" y2="6"/>
            <line x1="3" y1="10" x2="21" y2="10"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
    
    @staticmethod
    def mqtt_icon(color: str = "#4A9EFF") -> QIcon:
        """MQTT图标 - 用于本地MQTT服务"""
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="2"/>
            <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/>
        </svg>'''
        return IconProvider.get_svg_icon(svg, color)
