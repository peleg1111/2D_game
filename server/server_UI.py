__author__ = 'Peleg Etzioni'
import tkinter as tk

class Server_ui(tk.Tk):
    def __init__(self, server):
        self.server = server
        super().__init__()
        self.title("Server")
        self.geometry("800x600")
        self.configure(bg="#1e1e1e")

        tk.Label(self, text="Server Dashboard", font=("Arial", 18, "bold"),
                 bg="#2a2a2a", fg="white").pack(fill=tk.X, pady=12)

        scrollbar = tk.Scrollbar(self)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_box = tk.Text(
            self,
            font=(None, 20),
            bg="#2a2a2a", fg="#d4d4d4",
            relief=tk.FLAT, state=tk.DISABLED,
            padx=12, pady=10,
            yscrollcommand= scrollbar.set
        )
        self.text_box.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text_box.yview)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.after(100, self.update)

    def update(self):
        if not self.server.active:
            self.on_close()

        current_scroll_pos = self.text_box.yview()

        self.text_box.config(state=tk.NORMAL)
        self.text_box.delete("1.0", tk.END)
        self.text_box.insert(tk.END, self.server.State())

        self.text_box.yview_moveto(current_scroll_pos[0])

        self.text_box.config(state=tk.DISABLED)
        self.after(100, self.update)


    def on_close(self):
        self.server.active = False
        self.destroy()