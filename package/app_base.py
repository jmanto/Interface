from PyQt5 import QtWidgets, QtCore, QtGui
from time import sleep

# Apps specific
APP_NAME = "Data Wrangling"
APP_ICON = "assets/data.png"

CSS_FILE = "assets/style.css"
template = "template"

defaultLibrary = "Bibliothèques.xlsx"

# Generic
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

width = 600
height = 400

width_info_box = 600
height_info_box = 400


def window_corner(width, height):
    x = round((SCREEN_WIDTH - width) / 2)
    y = round((SCREEN_HEIGHT - height) / 2)
    return x, y

def apply_style():
    with open(CSS_FILE, "r") as f:
        style = f.read()

    return style