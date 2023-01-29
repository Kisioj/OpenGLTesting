import sys

from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtWidgets import QApplication

from common import initialize_gl, paint_gl, screen_width, screen_height


class OpenGLWidget(QOpenGLWidget):
    def initializeGL(self):
        initialize_gl()

    def paintGL(self):
        paint_gl()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = OpenGLWidget()
    widget.resize(screen_width, screen_height)
    widget.show()
    app.exec()
