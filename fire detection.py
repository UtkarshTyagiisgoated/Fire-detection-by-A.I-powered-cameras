import cv2
import numpy as np
import threading
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import playsound
import time
import datetime

fire_reported = [0, 0, 0, 0, 0, 0]
alarm_status = [False, False, False, False, False, False]


def play_audio():
    playsound.playsound("Alarm.mp3")


def alarm_handler(index):
    global alarm_status
    if not alarm_status[index]:
        threading.Thread(target=play_audio).start()
        alarm_status[index] = True
        time.sleep(20)
        alarm_status[index] = False


def detect_fire(frame, index):
    blur = cv2.GaussianBlur(frame, (15, 15), 0)
    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
    lower = np.array([22, 50, 50], dtype='uint8')
    upper = np.array([35, 255, 255], dtype='uint8')
    mask = cv2.inRange(hsv, lower, upper)
    output = cv2.bitwise_and(frame, frame, mask=mask)
    number_of_total = cv2.countNonZero(mask)

    # Calculate the area of the fire
    fire_area = number_of_total / (frame.shape[0] * frame.shape[1])  # Normalize by the frame size

    if number_of_total > 2000:
        fire_reported[index] += 1
        threading.Thread(target=alarm_handler, args=(index,)).start()
        return True, output, fire_area
    else:
        return False, output, 0.0


class RegisterPage:
    def __init__(self, parent):
        self.parent = parent
        self.parent.title("Register")

        self.label_username = tk.Label(parent, text="Username:")
        self.label_password = tk.Label(parent, text="Password:")
        self.entry_username = tk.Entry(parent)
        self.entry_password = tk.Entry(parent, show="*")
        self.label_username.grid(row=0, sticky=tk.E)
        self.label_password.grid(row=1, sticky=tk.E)
        self.entry_username.grid(row=0, column=1)
        self.entry_password.grid(row=1, column=1)

        self.register_button = tk.Button(parent, text="Register", command=self.register)
        self.register_button.grid(columnspan=2)

    def register(self):
        username = self.entry_username.get()
        password = self.entry_password.get()
        if username and password:
            with open("users.txt", "a") as file:
                file.write(f"{username}:{password}\n")
            messagebox.showinfo("Registration Successful", "You have successfully registered.")
            self.parent.destroy()
            LoginPage(tk.Tk())
        else:
            messagebox.showerror("Registration Failed", "Please enter both username and password.")


class LoginPage:
    def __init__(self, parent):
        self.parent = parent
        self.parent.title("Login")

        self.label_username = tk.Label(parent, text="Username:")
        self.label_password = tk.Label(parent, text="Password:")
        self.entry_username = tk.Entry(parent)
        self.entry_password = tk.Entry(parent, show="*")
        self.label_username.grid(row=0, sticky=tk.E)
        self.label_password.grid(row=1, sticky=tk.E)
        self.entry_username.grid(row=0, column=1)
        self.entry_password.grid(row=1, column=1)

        self.login_button = tk.Button(parent, text="Login", command=self.login)
        self.login_button.grid(columnspan=2)

        self.register_button = tk.Button(parent, text="Register", command=self.register)
        self.register_button.grid(columnspan=2)

    def login(self):
        username = self.entry_username.get()
        password = self.entry_password.get()
        with open("users.txt", "r") as file:
            for line in file:
                stored_username, stored_password = line.strip().split(":")
                if username == stored_username and password == stored_password:
                    messagebox.showinfo("Login Successful", "You have successfully logged in.")
                    self.parent.destroy()
                    App(tk.Tk(), "Fire Detection System")  # Start the fire detection system
                    return
        messagebox.showerror("Login Failed", "Invalid username or password.")

    def register(self):
        self.parent.destroy()
        RegisterPage(tk.Tk())


class App:
    def __init__(self, window, window_title,
                 video_sources=['cctv cameras.mp4', 'road_fire.mp4','bone_fire.mp4', '7253660-uhd_4096_2160_30fps.mp4']):
        self.window = window
        self.window.title(window_title)
        self.video_sources = video_sources

        self.vids = [cv2.VideoCapture(src) for src in self.video_sources]
        self.canvases = []

        for i, vid in enumerate(self.vids):
            ret, frame = vid.read()
            if ret:
                if i < 2:
                    self.canvases.append(tk.Canvas(window, width=640, height=360))
                    self.canvases[-1].grid(row=0, column=i, sticky="w")
                else:
                    self.canvases.append(tk.Canvas(window, width=640, height=360))
                    self.canvases[-1].grid(row=1, column=i - 2, sticky="w")

        self.fire_status_labels = []
        for i, source in enumerate(self.video_sources):
            self.fire_status_labels.append(
                tk.Label(window, text=f"Fire Detection Status ({source}): Normal", fg="green"))
            self.fire_status_labels[-1].grid(row=i // 2, column=(i % 2) * 2, columnspan=2, sticky="w", padx=10, pady=5)

        self.log_text = tk.Text(window, height=10, width=80)
        self.log_text.grid(row=2, column=0, columnspan=4, sticky="w", padx=10, pady=5)

        self.delay = 10
        self.update()

        self.window.mainloop()

    def stop(self):
        for vid in self.vids:
            vid.release()
        self.window.destroy()

    def update(self):
        for i, vid in enumerate(self.vids):
            ret, frame = vid.read()
            if ret:
                frame = cv2.resize(frame, (640, 360))
                fire_detected, output, fire_area = detect_fire(frame, i)

                # Overlay fire detection status on the video
                if fire_detected:
                    cv2.putText(frame, "Fire Detected", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
                if i < 2:
                    self.canvases[i].create_image(0, 0, image=photo, anchor=tk.NW)
                    self.canvases[i].photo = photo
                else:
                    self.canvases[i].create_image(0, 0, image=photo, anchor=tk.NW)
                    self.canvases[i].photo = photo

                if fire_detected:
                    self.fire_status_labels[i].config(
                        text=f"Fire Detection Status ({self.video_sources[i]}): Fire Detected (Magnitude: {fire_area:.2f})",
                        fg="red")
                    self.log_text.insert(tk.END,
                                         f"Fire detected at {datetime.datetime.now()} in video source {self.video_sources[i]} with magnitude {fire_area:.2f}\n")
                else:
                    self.fire_status_labels[i].config(text=f"Fire Detection Status ({self.video_sources[i]}): Normal",
                                                      fg="green")
        self.window.after(self.delay, self.update)


def main():
    root = tk.Tk()
    LoginPage(root)
    root.mainloop()


if __name__ == '__main__':
    main()

