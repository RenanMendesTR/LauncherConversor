pyinstaller --noconsole --onefile --icon=favicon.ico --name Launcher launcher_main.py ^
    --add-data "launcher_ui.py;." ^
    --add-data "login_ui.py;." ^
    --add-data "login_main.py;."
pause