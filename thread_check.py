import time
import threading
import main  # or whatever starts your app

time.sleep(2)

print("Active threads:")
for t in threading.enumerate():
    print(t.name)
