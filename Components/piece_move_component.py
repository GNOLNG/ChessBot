from PyQt6.QtTest import QTest
import pyautogui as auto
from PyQt6.QtWidgets import QApplication
import time


##simulate mouse click and move to make piece move on web view
def widgetDragDrop(targetWidget, destWidget):
    QTest.mouseMove(targetWidget)
    time.sleep(0.3)
    auto.leftClick()
    time.sleep(0.3)
    QTest.mouseMove(destWidget)
    time.sleep(0.3)
    auto.leftClick()
    return True


##simulate mouse click to select promotion
def widgetClick(targetWidget):
    QTest.mouseMove(targetWidget)
    QApplication.processEvents()
    auto.leftClick()
    QApplication.processEvents()
    return True
