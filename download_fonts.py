import urllib.request
import os

os.makedirs("assets/fonts", exist_ok=True)
urllib.request.urlretrieve("https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf", "assets/fonts/Roboto-Bold.ttf")
urllib.request.urlretrieve("https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf", "assets/fonts/Roboto-Regular.ttf")
print("Fonts downloaded!")
