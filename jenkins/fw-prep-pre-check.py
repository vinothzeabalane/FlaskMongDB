import os;
from datetime import datetime
d1 = datetime.today().strftime('%Y-%m-%d')
os.chdir("/mnt/udrive/ozeabalx/ps-bootprofile")
print("Current directory - {}").format(os.getcwd())
text_file = open("last_updated.txt", "r")
d2 = text_file.readlines()
if d1 in d2[0].strip():
  print("Firmware is ready")
else:
  assert 1 == 2, "Firmware is not ready"