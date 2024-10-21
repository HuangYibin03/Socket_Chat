import sys
import re
from PyQt5 import QtCore
from PyQt5.QtWidgets import QSplitter, QVBoxLayout, QDialog, QPushButton, QListWidget, QApplication, QTextEdit, QLineEdit, QScrollBar, QListWidgetItem,QWidget,QHBoxLayout,QSizePolicy,QSpacerItem,QScrollArea
import socket
from PyQt5.QtCore import Qt
from threading import Thread
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QFont  # 从 PyQt5.QtGui 导入 QFont
from PIL import Image, ImageDraw, ImageFont
import random
from PyQt5.QtGui import QPixmap, QIcon,QFontMetrics
from PyQt5 import QtGui
# from PIL.ImageQt import ImageQt
from PIL import ImageQt as IQ
from io import BytesIO
import base64
from PyQt5.QtWidgets import QLabel
class CustomTextEdit(QTextEdit):
    enter_pressed_signal = pyqtSignal()  # 自定义信号，用于传递 Enter 键按下的事件

    def __init__(self, parent=None):
        super().__init__(parent)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if not event.modifiers() & Qt.ShiftModifier:  # 如果没有按下 Shift 键，直接发送
                self.enter_pressed_signal.emit()  # 发射 Enter 键按下信号
                return  # 阻止默认行为（防止在输入框中换行）
        super().keyPressEvent(event)  # 保留其他按键的默认行为
class Window(QDialog):
    # 定义信号，用于更新成员列表和聊天记录
    update_member_list_signal = pyqtSignal(list)
    append_chat_signal = pyqtSignal(str)

    def __init__(self, client_name):
        super().__init__()
        self.client_name = client_name
        self.avatars={}
        self.icons={}
        # 主布局，使用 QVBoxLayout 使组件能垂直排列
        main_layout = QVBoxLayout(self)

        left_layout = QVBoxLayout(self)
        # # 聊天记录区域
        self.chat = QScrollArea()
        self.chat.setWidgetResizable(True)
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)  # 垂直布局
        self.chat.setWidget(self.chat_container)
        font = self.chat.font()
        font.setPointSize(13)
        self.chat.setFont(font)
        left_layout.addWidget(self.chat)

        # 创建底部输入框和按钮的布局
        bottom_widget = QWidget()  # 创建一个 QWidget 作为底部布局的容器
        bottom_layout = QVBoxLayout(bottom_widget)  # 将底部布局添加到容器中

        # 设置底部容器的背景颜色
        bottom_widget.setStyleSheet("background-color: #F9F9F9;")  # 白色背景
        # 输入框
        # 替换 QLineEdit 为 QTextEdit
        self.chatTextField = CustomTextEdit()
        font = self.chatTextField.font()
        font.setPointSize(13)
        self.chatTextField.setFont(font)
        self.chatTextField.setFixedHeight(180)  # 固定输入框高度
        self.chatTextField.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.chatTextField.setStyleSheet("border:none; padding: 5px; background-color:#F9F9F9;")  # 白色背景，无边框
        self.chatTextField.setWordWrapMode(QtGui.QTextOption.WrapAtWordBoundaryOrAnywhere)  # 自动换行
        self.chatTextField.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)  
        self.chatTextField.setStyleSheet("""
            QTextEdit {
                border: none;
                padding: 5px;
                background-color: #F9F9F9;
            }
            QScrollBar:vertical {
                width: 8px;
                background: #F9F9F9;
                margin: 0px 0px 0px 0px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background: #CCCCCC;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #888888;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        self.chatTextField.enter_pressed_signal.connect(self.send)  # 连接信号到发送方法
        bottom_layout.addWidget(self.chatTextField)

        bottom_right_layout=QHBoxLayout()
        bottom_right_layout.addStretch()  # 添加拉伸项，将按钮推向右边
        # spacer = QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.Fixed)  
        # bottom_right_layout.addItem(spacer)
        # 发送按钮
        self.btnSend = QPushButton("Send", self)
        font = self.btnSend.font()
        font.setPointSize(13)
        self.btnSend.setFont(font)
        self.btnSend.setFixedSize(100, 50)  # 按钮大小固定
        self.btnSend.setStyleSheet("background-color:#F9F9F9;padding: 5px; border:none;")  # 白色背景，无边框
        self.btnSend.clicked.connect(self.send)
        bottom_right_layout.addWidget(self.btnSend)
        bottom_layout.addLayout(bottom_right_layout)

        # 将底部布局添加到主布局
        left_layout.addWidget(bottom_widget)

        # 右侧成员列表（单独一个布局用于竖直排版）
        right_layout = QVBoxLayout()
        self.member_list = QListWidget()
        self.count_item=QListWidgetItem(f"群聊成员: 1")
        self.count_item.setFlags(Qt.NoItemFlags)
        self.count_item.setSizeHint(QtCore.QSize(200,60))
        self.member_list.addItem(self.count_item)
        # 创建一个 QFont 对象并设置字体样式和大小
        font = QFont()
        font.setPointSize(13)  # 设置字体大小
        # font.setBold(True)  # 设置为加粗
        self.member_list.item(0).setFont(font)  # 设置第0项的字体
        self.member_list.setFixedWidth(200)
        self.member_list.setStyleSheet("background-color:#EAEAEA;")  # 浅灰色背景
        # 添加用户
        user_item = QListWidgetItem(self.client_name)
        avatar,pixmap=self.generate_avatar(self.client_name)
        self.avatars[self.client_name]=avatar
        self.icons[self.client_name]=pixmap
        user_item.setIcon(QIcon(pixmap))
        # user_item.setSizeHint(QtCore.QSize(200,50))
        # 设置每个列表项的高度
        user_item.setSizeHint(QtCore.QSize(200, 50))  # 宽度200像素，高度50像素
        self.member_list.addItem(user_item)

        # 添加聊天窗口和成员列表
        # right_layout.addLayout(main_layout)
        right_layout.addWidget(self.member_list)
        under_layout=QHBoxLayout()
        under_layout.addLayout(left_layout)
        under_layout.addLayout(right_layout)
        # self.setLayout(right_layout)
        main_layout.addLayout(under_layout)
        self.setLayout(main_layout)
        self.setWindowTitle(f"飞机杯✈️交友群")
        self.resize(1200, 800)
        self.setMinimumSize(1200, 800)

        # 信号连接槽函数
        self.update_member_list_signal.connect(self.update_member_list)
        self.append_chat_signal.connect(self.append_chat)
    def closeEvent(self, event):
        """ 在点击 × 时退出聊天 """
        if self.client_socket:
            try:
                print()
            except Exception as e:
                print(f"Error when trying to notify server: {e}")
            finally:
                self.client_socket.close()
        event.accept()
    import base64

    def generate_avatar(self, name, size=100):
        # 创建空白头像图像
        image = Image.new('RGB', (size, size), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)
    
        # 随机背景颜色
        color = tuple(random.randint(0, 255) for _ in range(3))
        draw.rectangle([0, 0, size, size], fill=color)
    
        # 显示名字首字母
        initial = name[0].upper()
        font = ImageFont.truetype("arial.ttf", size // 2)
    
        # 计算文本位置
        text_bbox = draw.textbbox((0, 0), initial, font=font)
        text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
        position = ((size - text_width) // 2, (size - text_height) // 2)
    
        draw.text(position, initial, font=font, fill="black")
    
        # 保存图像到 BytesIO 缓存
        buffer = BytesIO()
        image.save(buffer, format='PNG')
    
        # 将图像转换为 base64 编码
        base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue())
        return f"data:image/png;base64,{base64_image}",pixmap


    def send(self):
        try:
            text = self.chatTextField.toPlainText()
            if text:
                # 手动换行：假设每行最多40个字符
                max_chars_per_line = 40
                lines = [text[i:i + max_chars_per_line] for i in range(0, len(text), max_chars_per_line)]
                wrapped_text = '\n'.join(lines)
                # 创建消息部件
                message_widget = QWidget()
                message_layout = QHBoxLayout(message_widget)
                # 消息文本
                message_label = QLabel(wrapped_text)
                message_label.setStyleSheet("""
                    background-color: #DCF8C6;
                    border-radius: 2px;
                    padding: 5px 10px 5px 10px;
                """)
                font = QFont()
                font.setPointSize(13)  # 设置字体大小
                message_label.setFont(font)  # 应用字体
                # 计算行数和高度
                font_metrics = QFontMetrics(message_label.font())
                line_height = font_metrics.lineSpacing()  # 每行的高度
                line_count = len(lines)  # 计算行数
                bubble_height = line_height * line_count + 20  # 设置气泡的高度，加上padding的高度  
                # 设置固定的高度
                message_label.setFixedHeight(bubble_height)
                message_layout.addWidget(message_label)
                # 头像
                avatar_label = QLabel()
                avatar_label.setPixmap(self.icons[self.client_name].scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                message_layout.addWidget(avatar_label)
                message_layout.setAlignment(Qt.AlignRight)  
                # 添加消息内容到聊天区域
                self.chat_layout.addWidget(message_widget)
                # 添加固定间隔的Spacer
                spacer = QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)  # 10是间隔高度
                self.chat_layout.addItem(spacer)
                self.chat.verticalScrollBar().setValue(self.chat.verticalScrollBar().maximum())
                # 发送消息到服务器
                self.client_socket.send(text.encode())
                self.chatTextField.setPlainText("")
                # 确保聊天区域始终在最顶部
                # self.chat.verticalScrollBar().setValue(0)
        except Exception as e:
            print(f"Error occurred while sending message: {e}")



    def append_chat(self, message):
        """更新聊天内容"""
        clean_message = re.sub(r'<[^>]*>', '', message)
        user = clean_message.split(":")[0]

        # 创建消息部件
        message_widget = QWidget()
        message_layout = QHBoxLayout(message_widget)

        if user == "server@wind":
            # 系统消息居中
            message_label = QLabel()
            message_label.setText(clean_message.split(":")[1])  # 设置消息内容
            message_label.setStyleSheet("""
                font-size: 13px;
                color: #666666;
            """)  # 系统消息样式
            font = QFont()
            font.setPointSize(12)  # 设置字体大小
            message_label.setFont(font)  # 应用字体
            font_metrics = QFontMetrics(message_label.font())
            line_height = font_metrics.lineSpacing()  # 每行的高度
            line_count = 1  # 计算行数
            bubble_height = line_height * line_count + 20  # 设置气泡的高度，加上padding的高度  
            # 设置固定的高度                
            message_label.setFixedHeight(bubble_height)
            message_layout.addWidget(message_label)
            message_layout.setAlignment(Qt.AlignCenter)  # 系统消息居中
        else:
            message_label = QLabel()
            text=clean_message.split(":")[1]
            max_chars_per_line = 40
            lines = [text[i:i + max_chars_per_line] for i in range(0, len(text), max_chars_per_line)]
            wrapped_text = '\n'.join(lines)
            # 用户消息处理
            if user in self.avatars.keys():
                avatar_image = self.icons[user]
                avatar_label = QLabel()
                avatar_label.setPixmap(QPixmap(avatar_image).scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                message_layout.addWidget(avatar_label)
                print(self.avatars)
                print("ahiofhiasdpoifhasdp90vyhsa8ohvdpash8pfgo98aysp89fga&G*")
            print(f"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa{clean_message}")
            # 消息文本
            message_label.setText(wrapped_text)  # 设置消息内容
            message_label.setStyleSheet("""
                background-color: #666666;
                border-radius: 2px;
                padding: 5px 10px 5px 10px; /* 上、右、下、左*/
                max-width: 400px;  # 限制最大宽度
            """)
            font = QFont()
            font.setPointSize(13)  # 设置字体大小
            message_label.setFont(font)  # 应用字体
            font_metrics = QFontMetrics(message_label.font())
            line_height = font_metrics.lineSpacing()  # 每行的高度
            line_count = len(lines)  # 计算行数
            bubble_height = line_height * line_count + 20  # 设置气泡的高度，加上padding的高度  
            # 设置固定的高度
            message_label.setFixedHeight(bubble_height)
            # message_layout.addWidget(message_label)
            # message_label.setMaximumWidth(400)
            # message_label.setWordWrap(True)
            message_layout.addWidget(message_label)

            # 设置对齐：用户消息左对齐
            message_layout.setAlignment(Qt.AlignLeft)
        
        # 将消息内容添加到聊天区域
        self.chat_layout.addWidget(message_widget)
        spacer = QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)  # 10是间隔高度
        self.chat_layout.addItem(spacer)
        # 确保聊天区域自动滚动到底部
        self.chat.verticalScrollBar().setValue(self.chat.verticalScrollBar().maximum())


    def update_member_list(self, users):
        """更新成员列表"""
        self.member_list.clear()
        self.count_item = QListWidgetItem(f"人员数量: {len(users)}")
        self.count_item.setFlags(Qt.NoItemFlags)  # 设置为不可选中
        self.count_item.setSizeHint(QtCore.QSize(200, 60))  # 设置高度
        self.member_list.addItem(self.count_item)
        font = QFont()
        font.setPointSize(13)  # 设置字体大小
        # font.setBold(True)  # 设置为加粗
        self.member_list.item(0).setFont(font)  # 设置第0项的字体
        for user in users:
            # 添加用户
            user_item = QListWidgetItem(user)
            if user not in self.avatars:
                avatar,pixmap=self.generate_avatar(user)
                self.avatars[user]=avatar
                self.icons[user]=pixmap
            user_item.setIcon(QIcon(self.icons[user]))
            # 设置每个列表项的高度
            user_item.setSizeHint(QtCore.QSize(200, 40))  # 宽度200像素，高度50像素
            self.member_list.addItem(user_item)
            # self.member_list.addItem(user)

class ClientThread(Thread):
    def __init__(self, window, client_name):
        Thread.__init__(self)
        self.window = window
        self.client_name = client_name

    def run(self):
        host = socket.gethostname()
        port = 8080

        BUFFER_SIZE = 2000
        self.window.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.window.client_socket.connect((host, port))

        self.window.client_socket.send(self.client_name.encode())

        while True:
            try:
                data = self.window.client_socket.recv(BUFFER_SIZE)
                if data:
                    decoded_message = data.decode("utf-8")
                    if decoded_message.startswith("USER_LIST"):
                        user_list = decoded_message[len("USER_LIST:"):].split(',')
                        self.window.update_member_list_signal.emit(user_list)
                    else:
                        self.window.append_chat_signal.emit(decoded_message)
                else:
                    break
            except socket.error as e:
                print(f"Socket error: {e}")
                break
        
        self.window.client_socket.close()


if __name__ == '__main__':
    client_name = input("Enter your name: ")

    app = QApplication(sys.argv)
    window = Window(client_name)
    clientThread = ClientThread(window, client_name)
    clientThread.start()
    window.show()
    sys.exit(app.exec_())
