cd /D "%~dp0"
#del build -Recurse -Force
pyinstaller --clean --noconfirm --add-data "../parameters.xml;./src" --add-data="./src/*.*;./src" --hidden-import=pymavlink.dialects.v20 --hidden-import=pymavlink.dialects.v20.ardupilotmega --distpath "./dist_windows" --onefile configurator.py
ren dist_windows/configurator.exe dist_windows/configurator_%time:~0,2%%time:~3,2%-%date:~-10,2%%date:~3,2%%date:~-4,4%.exe
pause