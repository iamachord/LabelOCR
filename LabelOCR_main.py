import sys, os
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QGraphicsPixmapItem, QGraphicsScene, QApplication
from PyQt5.QtGui import QPixmap
import LabelOCR, LogBrowser

from glob import glob
import time

img_formats = ['.bmp', '.jpg', '.jpeg', '.png']  # 支持的图片格式
label_formats = [".txt"]  # 支持的标注文件格式

# 标识符定义
LAST_PAGE = 0
NEXT_PAGE = 2
TO_PAGE = 1

# logger标识符
SAVE_LABEL = 0
JUMP_PAGE = 1
SHOW_PAGE = 2
LOAD_IMG = 3
LOAD_LABEL = 4


class MainCode(QMainWindow, LabelOCR.Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        LabelOCR.Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.btn_load_img.clicked.connect(self.load_img)
        self.btn_load_text.clicked.connect(self.load_text)
        self.btn_last_page.clicked.connect(lambda: self.go_to_page(LAST_PAGE))  # 传参0,1,2  表示 上一页，指定页，下一页
        self.btn_next_page.clicked.connect(lambda: self.go_to_page(NEXT_PAGE))
        self.btn_go.clicked.connect(lambda: self.go_to_page(TO_PAGE))

        self.horizontalSlider.valueChanged.connect(self.show_img_rescled)
        self.btn_save.clicked.connect(self.save_file)
        self.btn_show_log.clicked.connect(self.show_history_log)

        self.log_window = LogWindow()

        self.init()

    def init(self):
        self.img_dir = None
        self.img_list = None
        self.image_files = []  # 图片文件名list
        self.text_dir = None
        self.text_list = None

        self.img_now = None
        self.text_now = None
        self.text_now_path = None
        self.page_now = 0
        self.img_num_total = 0

        self.pixmap = None

        self.page_init()
        self.screen_size_init()

    def page_init(self):
        self.resize_scale = 10  # 10 就是1倍， 50就是5倍
        self.horizontalSlider.setSliderPosition(self.resize_scale)

    def screen_size_init(self):
        self.resize(800, 600)
        pass

    def load_img(self):
        img_dir = QFileDialog.getExistingDirectory(self, "选取文件夹")  # 起始路径
        if len(img_dir) == 0 or img_dir == self.img_dir:
            return
        else:
            self.img_dir = img_dir

        f = sorted(glob(img_dir + os.sep + "*.*"))
        self.image_files = [x.replace('/', os.sep) for x in f if os.path.splitext(x)[-1].lower() in img_formats]
        if self.image_files == []:
            QMainWindow.QMessageBox.critical(self, "Ooooops", "目录里没有支持的图片。")
            return
        self.img_num_total = len(self.image_files)

        self.logger(self.img_dir, LOAD_IMG)
        self.go_to_page(TO_PAGE)
        self.label_img_dir.setText(self.img_dir)
        self.label_num_total.setText("当前: {}/{}".format(self.page_now + 1, self.img_num_total))
        self.spinBox_page.setMaximum(self.img_num_total)

    def show_img(self, path):
        try:
            self.pixmap = QPixmap(path)
            self.item = QGraphicsPixmapItem(self.pixmap)
            self.scene = QGraphicsScene()  # 创建场景
            self.scene.addItem(self.item)
            self.graphicsView.setScene(self.scene)
            self.item.setScale(self.horizontalSlider.value() / 10)
            self.img_now = path
            return True

        except:
            QMainWindow.QMessageBox.critical(self, "错误", "载入图片目录失败。")
            return False

    def show_img_rescled(self):
        if self.img_now is None:
            return
        self.item.setScale(self.horizontalSlider.value() / 10)
        self.scene = QGraphicsScene()  # 创建场景
        self.scene.addItem(self.item)
        self.graphicsView.setScene(self.scene)

    def load_text(self):
        text_dir = QFileDialog.getExistingDirectory(self, "选取文件夹")  # 起始路径
        if len(text_dir) == 0 or text_dir == self.text_dir:
            return
        else:
            self.text_dir = text_dir

        f = sorted(glob(text_dir + os.sep + "*.*"))
        self.text_files = [x.replace('/', os.sep) for x in f if os.path.splitext(x)[-1].lower() in label_formats]
        self.label_text_dir.setText(self.text_dir)
        self.logger(self.text_dir, LOAD_LABEL)
        self.go_to_page(TO_PAGE)

    def show_text(self, path):
        if os.path.exists(path):
            f = open(path, "r", encoding="utf-8")
            self.text_now = f.readline()
            self.label_editor.setText(self.text_now)
            f.close()
        else:
            self.statusbar.showMessage("找不到相应label")
            self.label_editor.setText("")
            self.text_now = None

    def go_to_page(self, state):
        if self.img_dir is None:
            return
            # QMainWindow.QMessageBox.critical(self, "Ooooops", "先选择图像目录吧，亲。")

        if state == LAST_PAGE:
            if self.page_now > 0:
                self.page_now -= 1
            else:
                return
        if state == NEXT_PAGE:
            if self.page_now + 1 < self.img_num_total:
                self.page_now += 1
            else:
                return

        if state == TO_PAGE:
            if 0 <= self.spinBox_page.value() - 1 < self.img_num_total:
                self.page_now = self.spinBox_page.value() - 1
            else:
                QMainWindow.QMessageBox.critical(self, "Ooooops", "跳转页码超范围啦。")
                return

        if state == LAST_PAGE or state == NEXT_PAGE:
            self.save_file()  # 翻页自动保存

        img_path = self.image_files[self.page_now]

        if self.text_dir is not None:
            basename = os.path.basename(img_path).split(".")[:-1]
            basename = ".".join(basename) + label_formats[0]
            self.text_now_path = os.path.join(self.text_dir, basename)
            self.show_text(self.text_now_path)

        show_img_flag = self.show_img(img_path)
        if show_img_flag:  # 显示成功的话
            self.label_file_now.setText(img_path)
            self.label_num_total.setText("当前: {}/{}".format(self.page_now + 1, self.img_num_total))
            self.spinBox_page.setValue(self.page_now + 1)
            self.logger(self.text_now_path, JUMP_PAGE, "当前: {}/{}".format(self.page_now + 1, self.img_num_total))

    def save_file(self):
        if self.text_now is None and self.label_editor.text().rstrip().lstrip() is "" :
            return
        elif self.text_now is None and self.label_editor.text().rstrip().lstrip() is not "" :
            basename = os.path.basename(self.img_now).split(".")[:-1]
            basename = ".".join(basename) + label_formats[0]
            self.text_now_path = os.path.join(self.text_dir, basename)
            f = open(self.text_now_path, "w", encoding="utf-8")
            f.writelines(self.label_editor.text().rstrip().lstrip())
            f.close()
            self.logger(self.text_now_path, SAVE_LABEL)

        text = self.label_editor.text().rstrip().lstrip()  # 左右空格都去掉
        if text == self.text_now:
            self.statusbar.showMessage("没有改变标注哦")
        else:
            self.text_now = text
            f = open(self.text_now_path, "w", encoding="utf-8")
            f.writelines(text)
            f.close()
            self.logger(self.text_now_path, SAVE_LABEL)

    def logger(self, file_name, behavior, memo=""):
        timestamp = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime())

        if behavior == SAVE_LABEL:
            contect = "保存文件 " + file_name
        elif behavior == JUMP_PAGE:
            contect = "浏览 " + memo
        elif behavior == LOAD_IMG:
            contect = "载入图片目录 " + file_name
        elif behavior == LOAD_LABEL:
            contect = "载入标签目录 " + file_name
        else:
            contect = ""

        log = " ".join([timestamp, contect])
        self.log_window.textBrowser.append(log)
        self.statusbar.showMessage(log)

    def show_history_log(self):
        self.log_window.show()

    def keyPressEvent(self, event):
        if str(event.key()) == "65":
            self.go_to_page(LAST_PAGE)
        elif str(event.key()) == "68":
            self.go_to_page(NEXT_PAGE)
        elif str(event.key()) == "83":
            self.save_file()
        elif str(event.key()) == "72":
            self.show_history_log()

    def closeEvent(self, event):
        self.log_window.close()


class LogWindow(QMainWindow, LogBrowser.Ui_MainWindow):
    # _signal = QtCore.pyqtSignal(str)
    def __init__(self):
        QMainWindow.__init__(self)
        LabelOCR.Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.logger = None


if __name__ == '__main__':
    app = QApplication(sys.argv)

    main_window = MainCode()
    log_window = LogWindow()

    with open('qss/blue.txt') as file:
        style = file.readlines()
        style = ''.join(style).strip('\n')
        app.setStyleSheet(style)

    main_window.show()
    sys.exit(app.exec_())
