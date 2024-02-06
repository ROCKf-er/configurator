cd /D "%~dp0"
del build -Recurse -Force
pyinstaller --clean --noconfirm --add-data "../parameters.xml;./src" --add-data="./src/*.*;./src" --hidden-import=pymavlink.dialects.v20 --hidden-import=pymavlink.dialects.v20.ardupilotmega --distpath "./dist_windows" --onefile configurator.py
pause