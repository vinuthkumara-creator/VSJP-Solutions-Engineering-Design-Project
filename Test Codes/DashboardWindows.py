import tkinter as tk
from tkinter import ttk, messagebox
import csv, os, time, threading, datetime
import logging
import serial

# ---------------- GPIO SETUP ----------------
ser = serial.Serial('COM17', 115200, timeout=1)
time.sleep(2)
SCHEDULE_FILE = "schedule.csv"
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='water_cooling.log'
)


class WaterCoolingDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Water Cooling Unit Automating Project Demo")
        self.root.geometry("600x600")
        self.root.configure(bg="#d0ebff")

        self.thread_lock = threading.Lock()
        self.active_motor = None
        self.auto_mode = True
        self.stop_thread = False
        self.schedule_data = self.load_schedule_data()

        # ----- Title ----- 
        tk.Label(
            root, text="Water Cooling Unit Automating Project",
            font=("Helvetica", 16, "bold"), bg="#d0ebff", fg="#003366"
        ).pack(pady=20)

        # ----- Date & Time -----
        self.datetime_label = tk.Label(root, text="", font=("Arial", 12, "bold"),
                                       bg="#d0ebff", fg="#002244")
        self.datetime_label.pack(pady=5)
        self.update_datetime_label()

        # ----- Current Pressure Label (Top-Right Corner) -----
        self.pressure_label = tk.Label(root, text="Current Pressure: -- V",
                                       font=("Arial", 12, "bold"),
                                       bg="#d0ebff", fg="#990000")
        self.pressure_label.place(x=400, y=500)  # top-right position

        # ----- Motor Status -----
        status_frame = tk.Frame(root, bg="#d0ebff")
        status_frame.pack(pady=10)
        self.motor1_status = tk.Label(status_frame, text="Motor 1: OFF", font=("Arial", 10, "bold"), bg="#d0ebff", fg="red")
        self.motor2_status = tk.Label(status_frame, text="Motor 2: OFF", font=("Arial", 10, "bold"), bg="#d0ebff", fg="red")
        self.motor1_status.grid(row=0, column=0, padx=20)
        self.motor2_status.grid(row=0, column=1, padx=20)

        # ----- Service Status -----
        self.service_label = tk.Label(root, text="", font=("Arial", 11, "bold"), bg="#d0ebff", fg="orange")
        self.service_label.pack(pady=5)

        # ----- Mode Switch -----
        self.mode_btn = tk.Button(root, text="Mode: Automatic", bg="#0077b6", fg="white",
                                  font=("Arial", 11, "bold"), command=self.toggle_mode)
        self.mode_btn.pack(pady=10)

        # ----- Motor Selection Buttons -----
        self.motor1_btn = tk.Button(root, text="Select Motor 1", width=16, height=2,
                                    bg="red", fg="white", font=("Arial", 12, "bold"),
                                    command=lambda: self.select_motor(1))
        self.motor2_btn = tk.Button(root, text="Select Motor 2", width=16, height=2,
                                    bg="red", fg="white", font=("Arial", 12, "bold"),
                                    command=lambda: self.select_motor(2))
        self.motor1_btn.pack(pady=10)
        self.motor2_btn.pack(pady=10)

        # ----- Manual Control -----
        self.manual_frame = tk.Frame(root, bg="#d0ebff")
        self.manual_frame.pack(pady=10)
        self.manual_motor1_btn = tk.Button(self.manual_frame, text="Turn ON Motor 1", width=16,
                                           bg="#555", fg="white", font=("Arial", 11, "bold"),
                                           command=lambda: self.manual_control(1))
        self.manual_motor2_btn = tk.Button(self.manual_frame, text="Turn ON Motor 2", width=16,
                                           bg="#555", fg="white", font=("Arial", 11, "bold"),
                                           command=lambda: self.manual_control(2))
        self.manual_motor1_btn.grid(row=0, column=0, padx=10)
        self.manual_motor2_btn.grid(row=0, column=1, padx=10)

        # ----- Schedule Table Button -----
        tk.Button(root, text="Schedule Table", width=12, height=2,
                  bg="#0077b6", fg="white", font=("Arial", 11, "bold"),
                  command=self.open_table_window).pack(pady=25)

        threading.Thread(target=self.auto_control_loop, daemon=True).start()
        threading.Thread(target=self.read_voltage_loop, daemon=True).start()  # <-- voltage + serial thread
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        logging.info("Dashboard initialized")
        
        self.currentstateM1 = False
        self.currentstateM2 = False

    # ---------------- Voltage / Serial Reading ----------------
    def read_voltage_loop(self):
        while not self.stop_thread:
            try:
                if ser.in_waiting > 0:
                    line = ser.readline().decode(errors="ignore").strip()
                    # Normalize for checks
                    low_line = line.lower() if line else ""
                    # Check for the line_blocked safety message
                    if "line_blocked" in low_line or low_line == "line_blocked":
                        logging.warning("Received line_blocked signal from serial")
                        # Use root.after to ensure UI operations happen on main thread
                        try:
                            self.root.after(0, self.handle_system_failure)
                        except Exception as ui_exc:
                            logging.error(f"Failed to schedule system failure handler: {ui_exc}")
                        # continue to next read iteration
                        time.sleep(0.1)
                        continue

                    # Existing Voltage parsing behavior
                    if line.startswith("parameter:"):
                        parameter = line.split(":")[1].strip()
                        self.root.after(0, lambda v=parameter: self.pressure_label.config(text=f"Current Condition: {v} Hz"))
            except Exception as e:
                logging.error(f"Voltage/serial read error: {e}")
            time.sleep(0.5)  # read every 0.5 seconds

    # ---------------- System Failure Handler ----------------
    def handle_system_failure(self):
        """
        Called when 'line_blocked' is received from serial.
        Switches dashboard into Manual mode, turns off both motors,
        and notifies the user with a message box "System Failure".
        """
        try:
            with self.thread_lock:
                logging.info("Handling system failure: switching to manual, turning off motors.")
                # Set to Manual mode
                self.auto_mode = False
                # Update UI elements to reflect manual mode
                self.mode_btn.config(text="Mode: Manual", bg="#ff8c00")
                # Motor selection should be disabled in manual (as existing behavior)
                self.motor1_btn.config(state="disabled")
                self.motor2_btn.config(state="disabled")
                # Enable manual control buttons so operator can act (but motors will be off)
                self.manual_motor1_btn.config(state="normal", bg="#555", text="Turn ON Motor 1")
                self.manual_motor2_btn.config(state="normal", bg="#555", text="Turn ON Motor 2")
                # Ensure both motors are turned off physically and via serial
                self.currentstateM1 = False
                self.currentstateM2 = False
        
                ser.write(b"Motors_OFF\n")
                

                # Update status labels
                self.motor1_status.config(text="Motor 1: OFF", fg="red")
                self.motor2_status.config(text="Motor 2: OFF", fg="red")
                logging.warning("System moved to manual mode and motors turned OFF due to line_blocked")

            # Show messagebox to the user (must be done on main thread; we are on main thread via root.after)
            try:
                messagebox.showerror("System Failure", "System Failure")
            except Exception as mb_exc:
                logging.error(f"Failed to show messagebox for system failure: {mb_exc}")

        except Exception as e:
            logging.error(f"Error in handle_system_failure: {e}")

    # ---------------- Utility Functions ----------------
    def update_datetime_label(self):
        now = datetime.datetime.now()
        formatted = now.strftime("%A, %d %B %Y | %H:%M:%S")
        mode_text = "AUTO" if self.auto_mode else "MANUAL"
        mode_color = "green" if self.auto_mode else "orange"
        self.datetime_label.config(text=f"{formatted}   |   Mode: {mode_text}", fg=mode_color)
        self.root.after(1000, self.update_datetime_label)

    def parse_time(self, time_str):
        if not time_str or not time_str.strip():
            return None
        try:
            return datetime.datetime.strptime(time_str.strip(), "%H:%M").time()
        except ValueError:
            return None

    # ---------------- Automation Logic ----------------
    def auto_control_loop(self):
        while not self.stop_thread:
            try:
                with self.thread_lock:
                    if self.auto_mode and self.active_motor:
                        now = datetime.datetime.now()
                        now_t = now.time()
                        day_index = now.weekday()

                        if 0 <= day_index <= 6:
                            self.schedule_data = self.load_schedule_data()
                            start = self.schedule_data.get("Starting Time", [""] * 7)[day_index]
                            interval = self.schedule_data.get("Interval Time", [""] * 7)[day_index]
                            end = self.schedule_data.get("Ending Time", [""] * 7)[day_index]

                            start_t = self.parse_time(start)
                            end_t = self.parse_time(end)
                            interval_start, interval_end = None, None

                            if "-" in str(interval):
                                parts = interval.split("-")
                                if len(parts) == 2:
                                    interval_start = self.parse_time(parts[0])
                                    interval_end = self.parse_time(parts[1])

                            if start_t is not None and end_t is not None:
                                if interval_start and interval_end and interval_start <= now_t <= interval_end:
                                    self.activate_selected_motor(False)
                                    self.service_label.config(text="Currently Paused (Under Service)", fg="orange")
                                    logging.info("System paused (Under Service)")
                                elif start_t <= now_t <= end_t:
                                    self.activate_selected_motor(True)
                                    self.service_label.config(text="System Active", fg="green")
                                else:
                                    self.activate_selected_motor(False)
                                    self.service_label.config(text="System Idle", fg="red")
                            else:
                                self.activate_selected_motor(False)
                                self.service_label.config(text="No valid schedule", fg="gray")

                        else:
                            self.activate_selected_motor(False)
                            self.service_label.config(text="Weekend - System OFF", fg="gray")

                time.sleep(3)
            except Exception as e:
                logging.error(f"Automation loop error: {e}")
                time.sleep(3)

    # ---------------- Motor Control ----------------
    def activate_selected_motor(self, state):
        try:
            if self.active_motor == 1:
                self.currentstateM1 = True if state else False
                self.currentstateM2 = False
                if state:
                    ser.write(b"Motor1_ON\n")
                else:
                    ser.write(b"Motor1_OFF\n")

                ser.write(b"Motor2_OFF\n")
                self.motor1_status.config(text="Motor 1: ON" if state else "Motor 1: OFF",
                                          fg="green" if state else "red")
                self.motor2_status.config(text="Motor 2: OFF", fg="red")
            elif self.active_motor == 2:
                self.currentstateM2 = True if state else False
                self.currentstateM1 = False
                if state:
                    ser.write(b"Motor2_ON\n")
                else:
                    ser.write(b"Motor2_OFF\n")

                ser.write(b"Motor1_OFF\n")
                self.motor2_status.config(text="Motor 2: ON" if state else "Motor 2: OFF",
                                          fg="green" if state else "red")
                self.motor1_status.config(text="Motor 1: OFF", fg="red")
        except Exception as e:
            logging.error(f"Motor activation error: {e}")

    # ---------------- GUI Control and Schedule ----------------
    def toggle_mode(self):
        self.auto_mode = not self.auto_mode
        with self.thread_lock:
            if self.auto_mode:
                self.mode_btn.config(text="Mode: Automatic", bg="#0077b6")
                ser.write(b"Motor1_OFF\n")
                ser.write(b"Motor2_OFF\n")
                self.motor1_btn.config(state="normal")
                self.motor2_btn.config(state="normal")
                self.manual_motor1_btn.config(state="disabled", bg="#555", text="Turn ON Motor 1")
                self.manual_motor2_btn.config(state="disabled", bg="#555", text="Turn ON Motor 2")
            else:
                self.mode_btn.config(text="Mode: Manual", bg="#ff8c00")
                self.motor1_btn.config(state="disabled")
                self.motor2_btn.config(state="disabled")
                self.manual_motor1_btn.config(state="normal")
                self.manual_motor2_btn.config(state="normal")
            self.activate_selected_motor(False)

    def select_motor(self, motor_number):
        if not self.auto_mode:
            messagebox.showwarning("Manual Mode", "Switch to Automatic mode to select motor.")
            return
        with self.thread_lock:
            self.active_motor = motor_number
            if motor_number == 1:
                self.motor1_btn.config(bg="green", text="Motor 1 (Selected)")
                self.motor2_btn.config(bg="red", text="Select Motor 2")
            else:
                self.motor2_btn.config(bg="green", text="Motor 2 (Selected)")
                self.motor1_btn.config(bg="red", text="Select Motor 1")
            self.activate_selected_motor(False)
        messagebox.showinfo("Motor Selected", f"Motor {motor_number} selected for automatic schedule.")

    def manual_control(self, motor_number):
        if self.auto_mode:
            messagebox.showwarning("Automatic Mode", "Switch to Manual mode for manual control.")
            return
        try:
            with self.thread_lock:
                if motor_number == 1:
                    self.currentstateM1 = not self.currentstateM1
                    new_state = self.currentstateM1
                    self.currentstateM2 = False
                    if new_state:
                        ser.write(b"Motor1_ON\n")
                    else:
                        ser.write(b"Motor1_OFF\n")
                    self.manual_motor1_btn.config(
                        text="Turn OFF Motor 1" if new_state else "Turn ON Motor 1",
                        bg="green" if new_state else "#555")
                    if new_state:
                        self.manual_motor2_btn.config(state="disabled", bg="#555", text="Turn ON Motor 2")
                    else:
                        self.manual_motor2_btn.config(state="normal", bg="#555", text="Turn ON Motor 2")    
                    self.motor1_status.config(
                        text="Motor 1: ON" if new_state else "Motor 1: OFF",
                        fg="green" if new_state else "red")
                    if new_state:
                        self.motor2_status.config(
                            text="Motor 2: OFF",fg="red")
                elif motor_number == 2:
                    self.currentstateM2 = not self.currentstateM2
                    new_state = self.currentstateM2
                    self.currentstateM1 = False
                    if new_state:
                        ser.write(b"Motor2_ON\n")
                    else:
                        ser.write(b"Motor2_OFF\n")
                    self.manual_motor2_btn.config(
                        text="Turn OFF Motor 2" if new_state else "Turn ON Motor 2",
                        bg="green" if new_state else "#555")
                    if new_state:
                        self.manual_motor1_btn.config(state="disabled", bg="#555", text="Turn ON Motor 1")
                    else:
                        self.manual_motor1_btn.config(state="normal", bg="#555", text="Turn ON Motor 1")    
                    self.motor2_status.config(
                        text="Motor 2: ON" if new_state else "Motor 2: OFF",
                        fg="green" if new_state else "red")
                    if new_state:
                        self.motor1_status.config(
                            text="Motor 1: OFF", fg="red")
        except Exception as e:
            logging.error(f"Manual control error: {e}")
            messagebox.showerror("Error", f"Failed to control motor: {e}")

    # ---------------- Schedule Management ----------------
    def open_table_window(self):
        table_window = tk.Toplevel(self.root)
        table_window.title("Timing Schedule Table")
        table_window.geometry("1020x320")
        table_window.configure(bg="#e8f4fa")

        table_frame = ttk.Frame(table_window, padding=20)
        table_frame.pack(expand=True, fill="both")

        days = DAYS
        rows = ["Starting Time", "Interval Time", "Ending Time"]
        self.entries = [[None for _ in range(len(days))] for _ in range(len(rows))]

        for i, day in enumerate([""] + days):
            ttk.Label(table_frame, text=day, font=("Arial", 12, "bold")).grid(row=0, column=i, padx=10, pady=5)

        for i, row_name in enumerate(rows):
            ttk.Label(table_frame, text=row_name, font=("Arial", 11, "bold")).grid(row=i + 1, column=0, padx=10, pady=5)
            for j in range(len(days)):
                entry = ttk.Entry(table_frame, width=12)
                entry.grid(row=i + 1, column=j + 1, padx=10, pady=5)
                self.entries[i][j] = entry

        btn_frame = ttk.Frame(table_window, padding=10)
        btn_frame.pack()
        ttk.Button(btn_frame, text="Save Schedule", command=self.save_schedule).grid(row=0, column=0, padx=10)
        ttk.Button(btn_frame, text="Load Schedule", command=self.load_schedule).grid(row=0, column=1, padx=10)
        self.load_schedule()

    def save_schedule(self):
        try:
            with open(SCHEDULE_FILE, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([""] + DAYS)
                rows = ["Starting Time", "Interval Time", "Ending Time"]
                for i, row_name in enumerate(rows):
                    row = [row_name] + [self.entries[i][j].get() for j in range(7)]
                    writer.writerow(row)
            messagebox.showinfo("Saved", "Schedule saved successfully!")
            self.schedule_data = self.load_schedule_data()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_schedule(self):
        if not os.path.exists(SCHEDULE_FILE):
            return
        try:
            with open(SCHEDULE_FILE, "r") as f:
                reader = csv.reader(f)
                next(reader)
                for i, row in enumerate(reader):
                    for j, val in enumerate(row[1:]):
                        self.entries[i][j].delete(0, tk.END)
                        self.entries[i][j].insert(0, val)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_schedule_data(self):
        if not os.path.exists(SCHEDULE_FILE):
            return {}
        try:
            schedule = {}
            with open(SCHEDULE_FILE, "r", newline='', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                next(reader)
                rows = list(reader)
                for row in rows:
                    key = row[0].strip()  # 🔥 removes \r, spaces, etc.
                    values = [v.strip() for v in row[1:]]  # 🔥 clean all values
                    schedule[key] = values
            return schedule
        except Exception as e:
            logging.error(f"Schedule load error: {e}")
            return {}
    # ---------------- Exit Handler ----------------
    def on_close(self):
        self.stop_thread = True
        try:
            ser.write(b"Motor1_OFF\n")
            ser.write(b"Motor2_OFF\n")
        except:
            pass
        self.root.destroy()


# ---------------- Main ----------------
if __name__ == "__main__":
    root = tk.Tk()
    app = WaterCoolingDashboard(root)
    root.mainloop()

