@echo off
pyinstaller gui.spec
rmdir /s /q build
exit