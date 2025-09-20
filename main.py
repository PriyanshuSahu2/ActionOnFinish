# import time
# import pyautogui
# import pytesseract
# from PIL import Image
# from plyer import notification
# from pynput import mouse
#
# # Tesseract path
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
#
# completion_keywords = ["installation complete", "finish", "done", "success"]
#
# # Global variables to store drag coordinates
# start_x = start_y = end_x = end_y = 0
# region_selected = False
#
# def on_click(x, y, button, pressed):
#     global start_x, start_y, end_x, end_y, region_selected
#
#     if pressed:
#         # Mouse button pressed → start of drag
#         start_x, start_y = x, y
#     else:
#         # Mouse button released → end of drag
#         end_x, end_y = x, y
#         region_selected = True
#         print(f"Selected region: ({start_x}, {start_y}, {end_x - start_x}, {end_y - start_y})")
#         # Stop listener after drag
#         return False
#
# # Let user drag to select region
# print("Drag to select the screen region to monitor...")
# with mouse.Listener(on_click=on_click) as listener:
#     listener.join()
#
# # Calculate width and height
# width = end_x - start_x
# height = end_y - start_y
# SCREEN_REGION = (start_x, start_y, width, height)
#
# # Optional Finish button coordinates
# # You can also drag select it separately if you want
# FINISH_BUTTON = (start_x + width//2, start_y + height - 20)  # roughly bottom center
#
# def check_installation():
#     screenshot = pyautogui.screenshot(region=SCREEN_REGION)
#     gray_screenshot = screenshot.convert('L')
#     text = pytesseract.image_to_string(gray_screenshot).lower()
#     print(text)
#     for keyword in completion_keywords:
#         if keyword in text:
#             return True
#     return False
#
# def on_success():
#     print("✅ Installation Complete!")
#     # Optional click
#     # pyautogui.click(FINISH_BUTTON[0], FINISH_BUTTON[1])
#     notification.notify(title="ActionOnFinish", message="Installation Complete!", timeout=5)
#
# def on_failure():
#     print("⏳ Still installing...")
#
# # Main loop
# while True:
#     if check_installation():
#         on_success()
#         break
#     else:
#         on_failure()
#     time.sleep(5)



import time
from pywinauto import Desktop
from plyer import notification

# Keywords indicating installation completion
completion_keywords = ["finish", "done", "installation complete", "success"]

# 1️⃣ List all visible windows
windows = Desktop(backend="uia").windows()
windows_titles = [w.window_text() for w in windows if w.window_text().strip()]

if not windows_titles:
    print("No visible windows found. Please open the installer first.")
    exit(1)

print("Select a window to monitor:")
for i, title in enumerate(windows_titles):
    print(f"{i+1}: {title}")

choice = int(input("Enter the number of the window: ")) - 1
WINDOW_TITLE = windows_titles[choice]

# Connect to the selected window
window = Desktop(backend="uia").window(title=WINDOW_TITLE)
print(f"Monitoring window: {WINDOW_TITLE}")

# Optional: specify Finish button title (if you want to click it)
FINISH_BUTTON_TITLE = "Finish"  # Adjust if your installer uses a different label

# 2️⃣ Main loop: monitor window
while True:
    try:
        window.set_focus()  # Bring window to front

        # Get text from all controls in the window
        texts = [ctrl.window_text() for ctrl in window.descendants()]

        # Check for completion keywords
        detected = False
        for t in texts:
            for keyword in completion_keywords:
                if keyword.lower() in t.lower():
                    detected = True
                    break
            if detected:
                break

        if detected:
            print("✅ Installation Complete!")

            # Optional: click Finish button
            try:
                finish_btn = window.child_window(title=FINISH_BUTTON_TITLE, control_type="Button")
                if finish_btn.exists():
                    finish_btn.click_input()
                    print("Clicked Finish button.")
            except Exception as e:
                print(f"No Finish button clicked: {e}")

            # Send desktop notification
            notification.notify(title="ActionOnFinish", message="Installation Complete!", timeout=5)

            # Log to file
            with open("installation_log.txt", "a") as f:
                f.write(f"Installation completed at {time.ctime()}\n")

            break
        else:
            print("⏳ Still installing...")

    except Exception as e:
        print(f"Error: {e}")

    time.sleep(2)  # Check every 2 seconds
