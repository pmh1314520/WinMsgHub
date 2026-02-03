"""
WinMsgHub - SVG图标管理器
作者：青云制作_彭明航

提供统一的SVG图标系统，替换所有Emoji表情
"""

from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QByteArray, Qt, QSize
from typing import Dict


class SvgIcon:
    """SVG图标类"""
    
    # 图标缓存
    _cache: Dict[str, QIcon] = {}
    
    # SVG图标定义
    ICONS = {
        # 基础图标
        "dashboard": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="3" y="3" width="7" height="7" rx="1" stroke="currentColor" stroke-width="2"/>
            <rect x="14" y="3" width="7" height="7" rx="1" stroke="currentColor" stroke-width="2"/>
            <rect x="3" y="14" width="7" height="7" rx="1" stroke="currentColor" stroke-width="2"/>
            <rect x="14" y="14" width="7" height="7" rx="1" stroke="currentColor" stroke-width="2"/>
        </svg>''',
        
        "chart": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M3 3v18h18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="M7 14l4-4 3 3 5-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="7" cy="14" r="1.5" fill="currentColor"/>
            <circle cx="11" cy="10" r="1.5" fill="currentColor"/>
            <circle cx="14" cy="13" r="1.5" fill="currentColor"/>
            <circle cx="19" cy="6" r="1.5" fill="currentColor"/>
        </svg>''',
        
        "calendar": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="3" y="5" width="18" height="16" rx="2" stroke="currentColor" stroke-width="2"/>
            <path d="M3 9h18" stroke="currentColor" stroke-width="2"/>
            <path d="M7 3v4M17 3v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        
        "database": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <ellipse cx="12" cy="6" rx="8" ry="3" stroke="currentColor" stroke-width="2"/>
            <path d="M4 6v6c0 1.657 3.582 3 8 3s8-1.343 8-3V6" stroke="currentColor" stroke-width="2"/>
            <path d="M4 12v6c0 1.657 3.582 3 8 3s8-1.343 8-3v-6" stroke="currentColor" stroke-width="2"/>
        </svg>''',
        
        "settings": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
            <path d="M12 3v2m0 14v2M3 12h2m14 0h2m-3.05-7.95l1.41-1.41M5.64 18.36l1.41-1.41m0-9.9L5.64 5.64m12.72 12.72l-1.41-1.41" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        
        "history": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M3 12a9 9 0 1 0 9-9v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="M12 7v5l3 3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="M8 3L12 7l4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "delete": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6h14z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="M10 11v6m4-6v6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        
        "tool": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "clean": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="M14 11v6m-4-6v6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        
        "upload": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "download": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "lightbulb": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M9 18h6M10 22h4M15 7a3 3 0 1 1-6 0 3 3 0 0 1 6 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="M12 3v1m6.36 1.64l-.7.7M21 12h-1M4 12H3m3.64-6.36l-.7-.7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="M9 14a5 5 0 0 1 0-8 5 5 0 0 1 6 8v4H9v-4z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
        </svg>''',
        
        "circle_red": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="8" fill="#E06C75" stroke="#C04C55" stroke-width="2"/>
        </svg>''',
        
        "circle_green": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="8" fill="#98C379" stroke="#78A359" stroke-width="2"/>
        </svg>''',
        
        "location": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" stroke="currentColor" stroke-width="2"/>
            <circle cx="12" cy="10" r="3" stroke="currentColor" stroke-width="2"/>
        </svg>''',
        
        "plug": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2v4m-2-4v4m4-4v4M8 6h8a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-2v4a2 2 0 0 1-4 0v-4H8a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        
        "globe": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" stroke="currentColor" stroke-width="2"/>
        </svg>''',
        
        "gamepad": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M6 11h4m-2-2v4m7-1h.01M18 10h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="M17 2H7a4 4 0 0 0-4 4v8a4 4 0 0 0 4 4h2l2 4 2-4h2a4 4 0 0 0 4-4V6a4 4 0 0 0-4-4z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "play": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M5 3l14 9-14 9V3z" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
        </svg>''',
        
        "stop": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor" stroke="currentColor" stroke-width="2"/>
        </svg>''',
        
        "refresh": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "book": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20M4 19.5A2.5 2.5 0 0 0 6.5 22H20V2H6.5A2.5 2.5 0 0 0 4 4.5v15z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "warning": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M12 9v4m0 4h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        
        "phone": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="5" y="2" width="14" height="20" rx="2" stroke="currentColor" stroke-width="2"/>
            <path d="M12 18h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        
        "computer": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
            <path d="M8 21h8M12 17v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        
        "question": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3m.08 4h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        
        "tomato": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="13" r="8" fill="#E06C75" stroke="#C04C55" stroke-width="2"/>
            <path d="M12 5c0-1 1-2 2-2s2 1 2 2-1 1-2 1-2 0-2-1z" fill="#98C379" stroke="#78A359" stroke-width="1.5"/>
            <circle cx="9" cy="11" r="1" fill="#FFFFFF" opacity="0.6"/>
        </svg>''',
        
        "coffee": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M18 8h1a4 4 0 0 1 0 8h-1M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M6 1v3m4-3v3m4-3v3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        
        "eye": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
        </svg>''',
        
        "water": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "yoga": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="4" r="2" fill="currentColor"/>
            <path d="M12 6v6m-4 2l4-2 4 2M8 14v6m8-6v6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "rest": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="4" r="2" fill="currentColor"/>
            <path d="M12 6v6m-4 2l4-2 4 2M8 14v6m8-6v6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "add": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 5v14m-7-7h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        
        "plus": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 5v14m-7-7h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        
        "edit": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "check": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M20 6L9 17l-5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "close": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "block": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <path d="M4.93 4.93l14.14 14.14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        
        "save": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M17 21v-8H7v8M7 3v5h8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "bell": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 0 1-3.46 0" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "zap": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M13 2L3 14h8l-1 8 10-12h-8l1-8z" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "palette": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2a10 10 0 0 0-9.95 9h11.64L9.74 7.05a1 1 0 0 1 1.41-1.41l3.99 3.99a1 1 0 0 1 0 1.42l-3.99 3.99a1 1 0 0 1-1.41-1.41L13.69 9H2.05A10 10 0 1 0 12 2z" stroke="currentColor" stroke-width="2"/>
            <circle cx="7.5" cy="10.5" r="1.5" fill="currentColor"/>
            <circle cx="12" cy="7.5" r="1.5" fill="currentColor"/>
            <circle cx="16.5" cy="10.5" r="1.5" fill="currentColor"/>
        </svg>''',
        
        "moon": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "sun": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="5" stroke="currentColor" stroke-width="2"/>
            <path d="M12 1v2m0 18v2M4.22 4.22l1.42 1.42m12.72 12.72l1.42 1.42M1 12h2m18 0h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        
        "lock": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="3" y="11" width="18" height="11" rx="2" stroke="currentColor" stroke-width="2"/>
            <path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        
        "unlock": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="3" y="11" width="18" height="11" rx="2" stroke="currentColor" stroke-width="2"/>
            <path d="M7 11V7a5 5 0 0 1 9.9-1" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        
        "clipboard": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <rect x="8" y="2" width="8" height="4" rx="1" stroke="currentColor" stroke-width="2"/>
        </svg>''',
        
        "target": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <circle cx="12" cy="12" r="6" stroke="currentColor" stroke-width="2"/>
            <circle cx="12" cy="12" r="2" fill="currentColor"/>
        </svg>''',
        
        "clock": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        
        "file": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9l-7-7z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M13 2v7h7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "document": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M14 2v6h6M16 13H8m8 4H8m2-8H8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        
        "search": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="11" cy="11" r="8" stroke="currentColor" stroke-width="2"/>
            <path d="m21 21-4.35-4.35" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        
        "info": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <path d="M12 16v-4m0-4h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        
        "user": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
        </svg>''',
        
        "license": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M14 2v6h6M10 13l2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "version": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7l10 5 10-5-10-5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "source": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2a3 3 0 0 0-3 3v4a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" stroke="currentColor" stroke-width="2"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v3m-4 0h8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        
        "uptime": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="M12 2v2m10 8h-2M4 12H2m3.05-6.95l1.41 1.41m12.02 0l1.41-1.41" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        
        "storage": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="2" y="4" width="20" height="6" rx="2" stroke="currentColor" stroke-width="2"/>
            <rect x="2" y="14" width="20" height="6" rx="2" stroke="currentColor" stroke-width="2"/>
            <circle cx="6" cy="7" r="1" fill="currentColor"/>
            <circle cx="6" cy="17" r="1" fill="currentColor"/>
            <path d="M10 7h8M10 17h8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        
        "author": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="8" r="5" stroke="currentColor" stroke-width="2"/>
            <path d="M3 21v-2a7 7 0 0 1 7-7h4a7 7 0 0 1 7 7v2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        
        "feature": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "network": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="2" fill="currentColor"/>
            <path d="M12 2v4m0 12v4M2 12h4m12 0h4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        
        "security": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M9 12l2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "performance": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M13 2L3 14h8l-1 8 10-12h-8l1-8z" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
        </svg>''',
        
        "schedule": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="3" y="4" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
            <path d="M16 2v4M8 2v4M3 10h18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <circle cx="8" cy="14" r="1" fill="currentColor"/>
            <circle cx="12" cy="14" r="1" fill="currentColor"/>
            <circle cx="16" cy="14" r="1" fill="currentColor"/>
            <circle cx="8" cy="18" r="1" fill="currentColor"/>
            <circle cx="12" cy="18" r="1" fill="currentColor"/>
        </svg>''',
        
        "tray": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="2" y="7" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
            <path d="M7 7V5a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="2"/>
            <circle cx="12" cy="14" r="2" stroke="currentColor" stroke-width="2"/>
        </svg>''',
        
        "filter": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M22 3H2l8 9.46V19l4 2v-8.54L22 3z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "github": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "docs": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20M4 19.5A2.5 2.5 0 0 0 6.5 22H20V2H6.5A2.5 2.5 0 0 0 4 4.5v15z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M8 7h8M8 11h8M8 15h4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        
        "feedback": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "timer": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="13" r="8" stroke="currentColor" stroke-width="2"/>
            <path d="M12 9v4l3 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="M9 2h6M12 5V2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="M16.5 7.5l1.5-1.5M6 7.5L4.5 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        
        "monitor": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
            <path d="M8 21h8M12 17v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="M7 7h10M7 11h6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        
        "trend_up": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M23 6l-9.5 9.5-5-5L1 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M17 6h6v6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "message": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "today": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="3" y="4" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
            <path d="M16 2v4M8 2v4M3 10h18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <circle cx="12" cy="15" r="2" fill="currentColor"/>
        </svg>''',
        
        "config": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M14 2v6h6M12 18v-6m-3 3l3-3 3 3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "test": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M9 11l3 3L22 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "rocket": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "arrow_up": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 19V5m0 0l-7 7m7-7l7 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        
        "arrow_down": '''<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 5v14m0 0l7-7m-7 7l-7-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
    }
    
    @classmethod
    def get_icon(cls, name: str, color: str = "#FFFFFF", size: int = 24) -> QIcon:
        """获取SVG图标
        
        Args:
            name: 图标名称
            color: 图标颜色（十六进制）
            size: 图标大小
            
        Returns:
            QIcon对象
        """
        cache_key = f"{name}_{color}_{size}"
        
        # 检查缓存
        if cache_key in cls._cache:
            return cls._cache[cache_key]
        
        # 获取SVG内容
        svg_content = cls.ICONS.get(name)
        if not svg_content:
            # 如果图标不存在，返回默认图标
            svg_content = cls.ICONS.get("info", "")
        
        # 替换颜色
        svg_content = svg_content.replace('currentColor', color)
        
        # 创建SVG渲染器
        svg_bytes = QByteArray(svg_content.encode('utf-8'))
        renderer = QSvgRenderer(svg_bytes)
        
        # 创建Pixmap
        pixmap = QPixmap(QSize(size, size))
        pixmap.fill(Qt.GlobalColor.transparent)
        
        # 渲染SVG到Pixmap
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        # 创建图标
        icon = QIcon(pixmap)
        
        # 缓存图标
        cls._cache[cache_key] = icon
        
        return icon
    
    @classmethod
    def get_pixmap(cls, name: str, color: str = "#FFFFFF", size: int = 24) -> QPixmap:
        """获取SVG Pixmap
        
        Args:
            name: 图标名称
            color: 图标颜色（十六进制）
            size: 图标大小
            
        Returns:
            QPixmap对象
        """
        # 获取SVG内容
        svg_content = cls.ICONS.get(name)
        if not svg_content:
            svg_content = cls.ICONS.get("info", "")
        
        # 替换颜色
        svg_content = svg_content.replace('currentColor', color)
        
        # 创建SVG渲染器
        svg_bytes = QByteArray(svg_content.encode('utf-8'))
        renderer = QSvgRenderer(svg_bytes)
        
        # 创建Pixmap
        pixmap = QPixmap(QSize(size, size))
        pixmap.fill(Qt.GlobalColor.transparent)
        
        # 渲染SVG到Pixmap
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        return pixmap
    
    @classmethod
    def get_icon(cls, name: str, color: str = "#FFFFFF", size: int = 24) -> QIcon:
        """获取SVG图标
        
        Args:
            name: 图标名称
            color: 图标颜色
            size: 图标大小
            
        Returns:
            QIcon: Qt图标对象
        """
        # 生成缓存键
        cache_key = f"{name}_{color}_{size}"
        
        # 检查缓存
        if cache_key in cls._cache:
            return cls._cache[cache_key]
        
        # 获取SVG代码
        svg_code = cls.ICONS.get(name)
        if not svg_code:
            # 如果图标不存在，返回默认图标
            svg_code = cls.ICONS.get("question", "")
        
        # 替换颜色
        svg_code = svg_code.replace('currentColor', color)
        
        # 创建SVG渲染器
        svg_bytes = QByteArray(svg_code.encode('utf-8'))
        renderer = QSvgRenderer(svg_bytes)
        
        # 创建Pixmap
        pixmap = QPixmap(QSize(size, size))
        pixmap.fill(Qt.GlobalColor.transparent)
        
        # 渲染SVG到Pixmap
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        # 创建图标
        icon = QIcon(pixmap)
        
        # 缓存图标
        cls._cache[cache_key] = icon
        
        return icon
