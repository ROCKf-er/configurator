# pyinstaller --clean --noconfirm --onefile --distpath "./" make_exe_for_win.py
import os
import datetime

#check_output("dir C:", shell=True)
print("Remove folder \"build\"")
#ret = check_output("rmdir /s build", shell=True)
os.system('rmdir /s /q build')

print("Make exe")
#os.system('python -m PyInstaller --clean --noconfirm --add-data "./../parameters.xml;./src" --add-data="./src/*.*;./src" --hidden-import=pymavlink.dialects.v20 --hidden-import=pymavlink.dialects.v20.ardupilotmega --distpath "./dist_windows" --onefile configurator.py')
os.system('pyinstaller --clean --noconfirm --add-data "./../parameters.xml;./src" --add-data="./src/*.*;./src" --hidden-import=pymavlink.dialects.v20 --hidden-import=pymavlink.dialects.v20.ardupilotmega --distpath "./dist_windows" --onefile configurator.py')
print("Make Exe done.")

t = datetime.datetime.now()
ymd_str = t.strftime('%Y%m%d')

print('Change dir to "dist_windows"')
os.chdir('dist_windows')
comm = f'ren configurator.exe configurator_{ymd_str}.exe'
print(comm)
os.system(comm)
