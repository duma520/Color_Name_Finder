import sys
import pyperclip
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, 
                            QTextEdit, QHBoxLayout, QGroupBox, QComboBox, QSpinBox, QColorDialog,
                            QMenu, QAction, QMessageBox, QFileDialog)
from PyQt5.QtGui import (QColor, QPixmap, QScreen, QPainter, QFont, QIcon, QPalette, QImage, 
                        QClipboard)
from PyQt5.QtCore import Qt, QTimer, QPoint, QSize
from PIL import ImageGrab
import numpy as np
import json
import os

class ColorNameFinder:
    def __init__(self):
        self.load_color_databases()
        
    def load_color_databases(self):
        """加载各种颜色数据库"""
        # 国标颜色名称 (GSB05-1426-2001)
        self.gb_colors = self.load_color_file('gb_colors.json')
        
        # 中国传统颜色
        self.chinese_traditional_colors = self.load_color_file('chinese_colors.json')
        
        # CSS颜色名称
        self.css_colors = self.load_color_file('css_colors.json')
        
        # X11颜色名称
        self.x11_colors = self.load_color_file('x11_colors.json')
        
        # RAL经典色卡
        self.ral_colors = self.load_color_file('ral_colors.json')
        
        # Pantone色卡
        self.pantone_colors = self.load_color_file('pantone_colors.json')
        
        # NCS自然色彩系统
        self.ncs_colors = self.load_color_file('ncs_colors.json')
        
        # 日本传统色
        self.japanese_colors = self.load_color_file('japanese_colors.json')
        
    def load_color_file(self, filename):
        """尝试加载颜色数据库文件"""
        try:
            # 首先尝试从当前目录加载
            filepath = os.path.join(os.path.dirname(__file__), filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # 如果不存在，使用内置的默认值
            return getattr(self, f'default_{filename.replace(".json", "")}', {})
        except:
            return {}

    # 默认颜色数据库（如果文件不存在）
    @property
    def default_gb_colors(self):
        return {
            (255, 255, 255): "白色",
            (0, 0, 0): "黑色",
            (255, 0, 0): "红色",
            # 更多颜色...
        }
    
    @property
    def default_chinese_colors(self):
        return {
            (238, 221, 187): "杏仁黄",
            (240, 223, 187): "麦秆黄",
            # 更多颜色...
        }
    
    # 其他默认颜色数据库...

    def find_closest_color(self, rgb, database='all'):
        """查找最接近的颜色名称"""
        r, g, b = rgb
        
        # 获取指定数据库
        if database == 'all':
            color_db = {**self.gb_colors, **self.chinese_traditional_colors, 
                       **self.css_colors, **self.x11_colors, **self.ral_colors,
                       **self.pantone_colors, **self.ncs_colors, **self.japanese_colors}
        else:
            color_db = getattr(self, f'{database}_colors', {})
        
        # 首先检查是否有精确匹配
        if (r, g, b) in color_db:
            return color_db[(r, g, b)], 0
        
        # 如果没有精确匹配，则查找最接近的颜色
        def color_distance(c1, c2):
            return sum((a - b) ** 2 for a, b in zip(c1, c2))
        
        # 查找最接近的颜色
        closest_color = min(color_db.keys(), key=lambda color: color_distance(color, rgb))
        distance = color_distance(closest_color, rgb)
        return color_db[closest_color], distance

    def get_all_color_names(self, rgb):
        """获取颜色的所有名称"""
        r, g, b = rgb
        names = []
        
        # 检查所有数据库
        databases = [
            ('国标', self.gb_colors),
            ('中国传统', self.chinese_traditional_colors),
            ('CSS', self.css_colors),
            ('X11', self.x11_colors),
            ('RAL', self.ral_colors),
            ('Pantone', self.pantone_colors),
            ('NCS', self.ncs_colors),
            ('日本传统', self.japanese_colors)
        ]
        
        for db_name, db in databases:
            if (r, g, b) in db:
                names.append(f"{db_name}: {db[(r, g, b)]}")
        
        # 如果没有找到精确匹配，查找最接近的颜色
        if not names:
            closest_name, distance = self.find_closest_color(rgb)
            names.append(f"近似: {closest_name} (Δ={distance})")
        
        return names
    
    def get_color_formats(self, r, g, b):
        """获取不同格式的颜色值"""
        hex_color = f"#{r:02x}{g:02x}{b:02x}".upper()
        cmyk = self.rgb_to_cmyk(r, g, b)
        hsv = self.rgb_to_hsv(r, g, b)
        hsl = self.rgb_to_hsl(r, g, b)
        
        return {
            'RGB': f"RGB({r}, {g}, {b})",
            'HEX': hex_color,
            'CMYK': f"CMYK({cmyk[0]}%, {cmyk[1]}%, {cmyk[2]}%, {cmyk[3]}%)",
            'HSV': f"HSV({hsv[0]}°, {hsv[1]}%, {hsv[2]}%)",
            'HSL': f"HSL({hsl[0]}°, {hsl[1]}%, {hsl[2]}%)"
        }
    
    def rgb_to_cmyk(self, r, g, b):
        """RGB转CMYK"""
        if (r, g, b) == (0, 0, 0):
            return 0, 0, 0, 100
            
        c = 1 - r / 255
        m = 1 - g / 255
        y = 1 - b / 255
        
        min_cmy = min(c, m, y)
        c = (c - min_cmy) / (1 - min_cmy) * 100
        m = (m - min_cmy) / (1 - min_cmy) * 100
        y = (y - min_cmy) / (1 - min_cmy) * 100
        k = min_cmy * 100
        
        return round(c), round(m), round(y), round(k)
    
    def rgb_to_hsv(self, r, g, b):
        """RGB转HSV"""
        r, g, b = r/255.0, g/255.0, b/255.0
        max_val = max(r, g, b)
        min_val = min(r, g, b)
        diff = max_val - min_val
        
        if max_val == min_val:
            h = 0
        elif max_val == r:
            h = (60 * ((g - b)/diff)) % 360
        elif max_val == g:
            h = (60 * ((b - r)/diff) + 120) % 360
        elif max_val == b:
            h = (60 * ((r - g)/diff) + 240) % 360
        
        if max_val == 0:
            s = 0
        else:
            s = (diff / max_val) * 100
            
        v = max_val * 100
        
        return round(h), round(s), round(v)
    
    def rgb_to_hsl(self, r, g, b):
        """RGB转HSL"""
        r, g, b = r/255.0, g/255.0, b/255.0
        max_val = max(r, g, b)
        min_val = min(r, g, b)
        diff = max_val - min_val
        
        l = (max_val + min_val) / 2
        
        if diff == 0:
            h = s = 0
        else:
            if l < 0.5:
                s = diff / (max_val + min_val)
            else:
                s = diff / (2 - max_val - min_val)
                
            if max_val == r:
                h = (g - b) / diff
            elif max_val == g:
                h = 2 + (b - r) / diff
            else:
                h = 4 + (r - g) / diff
                
            h *= 60
            if h < 0:
                h += 360
                
        return round(h), round(s*100), round(l*100)

class ColorPickerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.color_finder = ColorNameFinder()
        self.max_recent_colors = 10
        self.recent_colors = []
        self.favorite_colors = []
        
        self.initUI()
        
        # 定时器用于实时获取鼠标位置颜色
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_color)
        self.picking = False
        
        # 最近使用的颜色
        self.recent_colors = []

        
        # 收藏的颜色
        self.favorite_colors = []
        
        # 加载设置
        self.load_settings()
        
    def initUI(self):
        self.setWindowTitle('高级颜色识别工具')
        self.setGeometry(100, 100, 650, 700)
        
        # 设置窗口图标
        self.setWindowIcon(QIcon(self.create_color_icon(QColor(255, 0, 0))))
        
        # 主窗口布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 颜色拾取区域
        picker_group = QGroupBox("颜色拾取")
        picker_layout = QVBoxLayout()
        picker_group.setLayout(picker_layout)
        main_layout.addWidget(picker_group)
        
        # 颜色预览区域
        self.color_preview = QLabel()
        self.color_preview.setFixedHeight(80)
        self.color_preview.setStyleSheet("background-color: white; border: 2px solid black;")
        picker_layout.addWidget(self.color_preview)
        
        # 颜色值显示
        color_values_layout = QHBoxLayout()
        
        # RGB值显示
        self.rgb_label = QLabel("RGB: 未选择")
        color_values_layout.addWidget(self.rgb_label)
        
        # HEX值显示
        self.hex_label = QLabel("HEX: 未选择")
        color_values_layout.addWidget(self.hex_label)
        
        picker_layout.addLayout(color_values_layout)
        
        # 其他颜色格式显示
        other_formats_layout = QHBoxLayout()
        
        self.cmyk_label = QLabel("CMYK: 未选择")
        other_formats_layout.addWidget(self.cmyk_label)
        
        self.hsv_label = QLabel("HSV: 未选择")
        other_formats_layout.addWidget(self.hsv_label)
        
        self.hsl_label = QLabel("HSL: 未选择")
        other_formats_layout.addWidget(self.hsl_label)
        
        picker_layout.addLayout(other_formats_layout)
        
        # 颜色名称显示
        self.color_name_label = QLabel("颜色名称: 未选择")
        picker_layout.addWidget(self.color_name_label)
        
        # 所有颜色名称显示
        self.all_names_text = QTextEdit()
        self.all_names_text.setReadOnly(True)
        self.all_names_text.setPlaceholderText("所有已知颜色名称将显示在这里...")
        picker_layout.addWidget(self.all_names_text)
        
        # 按钮布局
        buttons_layout = QHBoxLayout()
        
        # 开始拾取按钮
        self.pick_button = QPushButton("开始拾取颜色")
        self.pick_button.clicked.connect(self.start_picking)
        buttons_layout.addWidget(self.pick_button)
        
        # 停止拾取按钮
        self.stop_button = QPushButton("停止拾取")
        self.stop_button.clicked.connect(self.stop_picking)
        self.stop_button.setEnabled(False)
        buttons_layout.addWidget(self.stop_button)
        
        # 颜色对话框按钮
        self.color_dialog_button = QPushButton("选择颜色...")
        self.color_dialog_button.clicked.connect(self.open_color_dialog)
        buttons_layout.addWidget(self.color_dialog_button)
        
        picker_layout.addLayout(buttons_layout)
        
        # 操作按钮布局
        action_buttons_layout = QHBoxLayout()
        
        # 复制按钮
        self.copy_button = QPushButton("复制颜色信息")
        self.copy_button.clicked.connect(self.copy_color_info)
        action_buttons_layout.addWidget(self.copy_button)
        
        # 添加到收藏
        self.favorite_button = QPushButton("添加到收藏")
        self.favorite_button.clicked.connect(self.add_to_favorites)
        action_buttons_layout.addWidget(self.favorite_button)
        
        # 保存颜色
        self.save_button = QPushButton("保存颜色")
        self.save_button.clicked.connect(self.save_color)
        action_buttons_layout.addWidget(self.save_button)
        
        picker_layout.addLayout(action_buttons_layout)
        
        # 最近颜色区域
        recent_group = QGroupBox("最近使用的颜色")
        recent_layout = QHBoxLayout()
        recent_group.setLayout(recent_layout)
        main_layout.addWidget(recent_group)
        
        self.recent_color_buttons = []
        for i in range(self.max_recent_colors):
            btn = QPushButton()
            btn.setFixedSize(30, 30)
            btn.setStyleSheet("background-color: transparent; border: 1px solid gray;")
            btn.clicked.connect(lambda _, idx=i: self.select_recent_color(idx))
            recent_layout.addWidget(btn)
            self.recent_color_buttons.append(btn)
        
        # 收藏颜色区域
        favorites_group = QGroupBox("收藏的颜色")
        favorites_layout = QVBoxLayout()
        favorites_group.setLayout(favorites_layout)
        main_layout.addWidget(favorites_group)
        
        self.favorites_list = QTextEdit()
        self.favorites_list.setReadOnly(True)
        self.favorites_list.setPlaceholderText("收藏的颜色将显示在这里...")
        favorites_layout.addWidget(self.favorites_list)
        
        # 更新收藏列表
        self.update_favorites_list()
        
        # 设置字体
        font = QFont("Microsoft YaHei", 10)
        self.setFont(font)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 状态栏
        self.statusBar().showMessage("就绪")
        
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        
        # 导入颜色
        import_action = QAction('导入颜色...', self)
        import_action.triggered.connect(self.import_colors)
        file_menu.addAction(import_action)
        
        # 导出颜色
        export_action = QAction('导出颜色...', self)
        export_action.triggered.connect(self.export_colors)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu('编辑')
        
        # 复制RGB
        copy_rgb_action = QAction('复制RGB值', self)
        copy_rgb_action.triggered.connect(lambda: self.copy_specific_format('RGB'))
        edit_menu.addAction(copy_rgb_action)
        
        # 复制HEX
        copy_hex_action = QAction('复制HEX值', self)
        copy_hex_action.triggered.connect(lambda: self.copy_specific_format('HEX'))
        edit_menu.addAction(copy_hex_action)
        
        # 复制CMYK
        copy_cmyk_action = QAction('复制CMYK值', self)
        copy_cmyk_action.triggered.connect(lambda: self.copy_specific_format('CMYK'))
        edit_menu.addAction(copy_cmyk_action)
        
        edit_menu.addSeparator()
        
        # 复制颜色名称
        copy_name_action = QAction('复制颜色名称', self)
        copy_name_action.triggered.connect(lambda: self.copy_specific_format('name'))
        edit_menu.addAction(copy_name_action)
        
        # 查看菜单
        view_menu = menubar.addMenu('查看')
        
        # 放大
        zoom_in_action = QAction('放大', self)
        zoom_in_action.setShortcut('Ctrl++')
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        # 缩小
        zoom_out_action = QAction('缩小', self)
        zoom_out_action.setShortcut('Ctrl+-')
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助')
        
        # 关于
        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_color_icon(self, color, size=32):
        """创建颜色图标"""
        pixmap = QPixmap(size, size)
        pixmap.fill(color)
        return pixmap
    
    def start_picking(self):
        self.picking = True
        self.pick_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.statusBar().showMessage("正在拾取颜色...移动鼠标到目标颜色上", 2000)
        self.timer.start(100)  # 每100毫秒更新一次
        
    def stop_picking(self):
        self.picking = False
        self.pick_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.timer.stop()
        self.statusBar().showMessage("颜色拾取已停止", 2000)
        
    def update_color(self):
        if not self.picking:
            return
            
        # 获取鼠标位置
        cursor_pos = QApplication.desktop().cursor().pos()
        
        # 获取屏幕截图
        screen = QApplication.primaryScreen()
        pixmap = screen.grabWindow(0, cursor_pos.x(), cursor_pos.y(), 1, 1)
        
        # 获取像素颜色
        image = pixmap.toImage()
        color = QColor(image.pixel(0, 0))
        r, g, b = color.red(), color.green(), color.blue()
        
        # 更新UI
        self.update_color_display(r, g, b)
        
    def update_color_display(self, r, g, b):
        # 更新颜色预览
        self.color_preview.setStyleSheet(f"background-color: rgb({r}, {g}, {b}); border: 2px solid black;")
        
        # 获取颜色格式
        color_formats = self.color_finder.get_color_formats(r, g, b)
        
        # 更新颜色值显示
        self.rgb_label.setText(f"RGB: {color_formats['RGB']}")
        self.hex_label.setText(f"HEX: {color_formats['HEX']}")
        self.cmyk_label.setText(f"CMYK: {color_formats['CMYK']}")
        self.hsv_label.setText(f"HSV: {color_formats['HSV']}")
        self.hsl_label.setText(f"HSL: {color_formats['HSL']}")
        
        # 获取颜色名称
        color_names = self.color_finder.get_all_color_names((r, g, b))
        
        # 显示主要颜色名称
        if color_names:
            primary_name = color_names[0].split(": ")[1].split(" (Δ=")[0]
            self.color_name_label.setText(f"颜色名称: {primary_name}")
        else:
            self.color_name_label.setText("颜色名称: 未知")
        
        # 显示所有颜色名称
        self.all_names_text.clear()
        self.all_names_text.append("所有已知名称:")
        for name in color_names:
            self.all_names_text.append(f"  - {name}")
        
        # 添加到最近颜色
        self.add_to_recent_colors(r, g, b)
        
        # 保存当前颜色
        self.current_color = (r, g, b)
    
    def add_to_recent_colors(self, r, g, b):
        """添加到最近使用的颜色"""
        color = (r, g, b)
        
        # 如果颜色已经在列表中，先移除
        if color in self.recent_colors:
            self.recent_colors.remove(color)
            
        # 添加到列表开头
        self.recent_colors.insert(0, color)
        
        # 确保不超过最大数量
        if len(self.recent_colors) > self.max_recent_colors:
            self.recent_colors = self.recent_colors[:self.max_recent_colors]
            
        # 更新按钮显示
        self.update_recent_colors_buttons()
    
    def update_recent_colors_buttons(self):
        """更新最近颜色按钮"""
        for i in range(self.max_recent_colors):
            if i < len(self.recent_colors):
                r, g, b = self.recent_colors[i]
                btn = self.recent_color_buttons[i]
                btn.setStyleSheet(f"background-color: rgb({r}, {g}, {b}); border: 1px solid gray;")
                btn.setToolTip(f"RGB: {r}, {g}, {b}")
            else:
                self.recent_color_buttons[i].setStyleSheet("background-color: transparent; border: 1px solid gray;")
                self.recent_color_buttons[i].setToolTip("")
    
    def select_recent_color(self, index):
        """选择最近使用的颜色"""
        if index < len(self.recent_colors):
            r, g, b = self.recent_colors[index]
            self.update_color_display(r, g, b)
            self.statusBar().showMessage(f"已选择最近使用的颜色: RGB({r}, {g}, {b})", 2000)
    
    def add_to_favorites(self):
        """添加到收藏"""
        if hasattr(self, 'current_color'):
            r, g, b = self.current_color
            color_names = self.color_finder.get_all_color_names((r, g, b))
            primary_name = color_names[0].split(": ")[1].split(" (Δ=")[0] if color_names else "自定义颜色"
            
            # 检查是否已经收藏
            for fav in self.favorite_colors:
                if fav['rgb'] == (r, g, b):
                    QMessageBox.information(self, "提示", "该颜色已经在收藏列表中!")
                    return
            
            self.favorite_colors.append({
                'rgb': (r, g, b),
                'name': primary_name,
                'hex': f"#{r:02x}{g:02x}{b:02x}".upper()
            })
            
            self.update_favorites_list()
            self.statusBar().showMessage(f"已添加到收藏: {primary_name}", 2000)
            
            # 保存收藏
            self.save_settings()
    
    def update_favorites_list(self):
        """更新收藏列表"""
        self.favorites_list.clear()
        if not self.favorite_colors:
            self.favorites_list.setPlainText("暂无收藏颜色")
            return
            
        self.favorites_list.append("收藏的颜色:")
        for idx, fav in enumerate(self.favorite_colors, 1):
            r, g, b = fav['rgb']
            self.favorites_list.append(f"{idx}. {fav['name']}")
            self.favorites_list.append(f"   RGB: {r}, {g}, {b}")
            self.favorites_list.append(f"   HEX: {fav['hex']}")
            self.favorites_list.append("")
    
    def open_color_dialog(self):
        """打开颜色选择对话框"""
        color = QColorDialog.getColor()
        if color.isValid():
            r, g, b = color.red(), color.green(), color.blue()
            self.update_color_display(r, g, b)
            self.statusBar().showMessage(f"已选择颜色: RGB({r}, {g}, {b})", 2000)
    
    def copy_color_info(self):
        """复制颜色信息"""
        if not hasattr(self, 'current_color'):
            QMessageBox.warning(self, "警告", "没有可复制的颜色信息!")
            return
            
        r, g, b = self.current_color
        color_formats = self.color_finder.get_color_formats(r, g, b)
        color_names = self.color_finder.get_all_color_names((r, g, b))
        
        text_to_copy = "颜色信息:\n"
        text_to_copy += f"RGB: {color_formats['RGB']}\n"
        text_to_copy += f"HEX: {color_formats['HEX']}\n"
        text_to_copy += f"CMYK: {color_formats['CMYK']}\n"
        text_to_copy += f"HSV: {color_formats['HSV']}\n"
        text_to_copy += f"HSL: {color_formats['HSL']}\n"
        text_to_copy += "颜色名称:\n"
        
        for name in color_names:
            text_to_copy += f"  - {name}\n"
        
        pyperclip.copy(text_to_copy)
        self.statusBar().showMessage("颜色信息已复制到剪贴板", 2000)
    
    def copy_specific_format(self, format_type):
        """复制特定格式的颜色值"""
        if not hasattr(self, 'current_color'):
            QMessageBox.warning(self, "警告", "没有可复制的颜色信息!")
            return
            
        r, g, b = self.current_color
        color_formats = self.color_finder.get_color_formats(r, g, b)
        color_names = self.color_finder.get_all_color_names((r, g, b))
        
        if format_type == 'RGB':
            pyperclip.copy(color_formats['RGB'])
        elif format_type == 'HEX':
            pyperclip.copy(color_formats['HEX'])
        elif format_type == 'CMYK':
            pyperclip.copy(color_formats['CMYK'])
        elif format_type == 'name':
            if color_names:
                primary_name = color_names[0].split(": ")[1].split(" (Δ=")[0]
                pyperclip.copy(primary_name)
            else:
                pyperclip.copy("未知颜色")
        
        self.statusBar().showMessage(f"已复制{format_type}到剪贴板", 2000)
    
    def save_color(self):
        """保存颜色为图片"""
        if not hasattr(self, 'current_color'):
            QMessageBox.warning(self, "警告", "没有可保存的颜色!")
            return
            
        r, g, b = self.current_color
        color_names = self.color_finder.get_all_color_names((r, g, b))
        primary_name = color_names[0].split(": ")[1].split(" (Δ=")[0] if color_names else "自定义颜色"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存颜色", 
            f"{primary_name.replace(' ', '_')}.png", 
            "PNG图像 (*.png);;JPEG图像 (*.jpg *.jpeg)"
        )
        
        if file_path:
            # 创建颜色图片
            img = QImage(200, 200, QImage.Format_RGB32)
            img.fill(QColor(r, g, b))
            
            # 保存图片
            img.save(file_path)
            self.statusBar().showMessage(f"颜色已保存为 {file_path}", 3000)
    
    def import_colors(self):
        """导入颜色"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入颜色", 
            "", "JSON文件 (*.json);;所有文件 (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    if isinstance(data, list):
                        self.favorite_colors = data
                        self.update_favorites_list()
                        self.save_settings()
                        QMessageBox.information(self, "成功", f"已导入 {len(data)} 种颜色!")
                    else:
                        QMessageBox.warning(self, "错误", "文件格式不正确!")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")
    
    def export_colors(self):
        """导出颜色"""
        if not self.favorite_colors:
            QMessageBox.warning(self, "警告", "没有可导出的颜色!")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出颜色", 
            "我的颜色收藏.json", "JSON文件 (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.favorite_colors, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "成功", f"已导出 {len(self.favorite_colors)} 种颜色!")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def zoom_in(self):
        """放大界面"""
        font = self.font()
        font.setPointSize(font.pointSize() + 1)
        self.setFont(font)
    
    def zoom_out(self):
        """缩小界面"""
        font = self.font()
        if font.pointSize() > 8:
            font.setPointSize(font.pointSize() - 1)
            self.setFont(font)
    
    def show_about(self):
        """显示关于对话框"""
        about_text = """
        <h2>高级颜色识别工具</h2>
        <p>版本: 1.0</p>
        <p>功能:</p>
        <ul>
            <li>实时拾取屏幕任意位置颜色</li>
            <li>识别颜色名称(国标、中国传统色、CSS等)</li>
            <li>多种颜色格式转换(RGB, HEX, CMYK, HSV, HSL)</li>
            <li>收藏和管理常用颜色</li>
            <li>导入导出颜色收藏</li>
        </ul>
        <p>© 2023 颜色识别工具</p>
        """
        QMessageBox.about(self, "关于", about_text)
    
    def load_settings(self):
        """加载设置"""
        try:
            settings = QApplication.instance().settings = QSettings("ColorPicker", "AdvancedColorTool")
            
            # 窗口大小和位置
            size = settings.value("window/size", QSize(650, 700))
            self.resize(size)
            
            pos = settings.value("window/position", QPoint(100, 100))
            self.move(pos)
            
            # 最近颜色
            recent_colors = settings.value("colors/recent", [])
            if recent_colors:
                self.recent_colors = [tuple(color) for color in recent_colors]
                self.update_recent_colors_buttons()
            
            # 收藏颜色
            favorite_colors = settings.value("colors/favorites", [])
            if favorite_colors:
                self.favorite_colors = []
                for fav in favorite_colors:
                    self.favorite_colors.append({
                        'rgb': tuple(fav['rgb']),
                        'name': fav['name'],
                        'hex': fav['hex']
                    })
                self.update_favorites_list()
                
        except:
            pass
    
    def save_settings(self):
        """保存设置"""
        try:
            settings = QApplication.instance().settings = QSettings("ColorPicker", "AdvancedColorTool")
            
            # 窗口大小和位置
            settings.setValue("window/size", self.size())
            settings.setValue("window/position", self.pos())
            
            # 最近颜色
            settings.setValue("colors/recent", self.recent_colors)
            
            # 收藏颜色
            settings.setValue("colors/favorites", self.favorite_colors)
            
        except:
            pass
    
    def closeEvent(self, event):
        """关闭窗口事件"""
        self.save_settings()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 创建并显示主窗口
    window = ColorPickerWindow()
    window.show()
    
    sys.exit(app.exec_())