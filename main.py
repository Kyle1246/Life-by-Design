import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import shutil
from datetime import datetime
from PIL import Image, ImageTk

class DataManager:
    def __init__(self, data_file='data.json', image_dir='vision_boards'):
        self.data_file = data_file
        self.image_dir = image_dir
        self.data = {
            "journals": [],
            "vision_boards": [{"name": "My Vision Board", "images": []}]
        }
        
        os.makedirs(self.image_dir, exist_ok=True)
        self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.data = json.load(f)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load data: {str(e)}")

    def save_data(self):
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save data: {str(e)}")

    def add_journal_entry(self, entry):
        self.data['journals'].append(entry)
        self.save_data()

    def add_image_to_board(self, board_name, image_path):
        for board in self.data['vision_boards']:
            if board['name'] == board_name:
                board['images'].append(image_path)
                self.save_data()
                return True
        return False

class JournalFrame(ttk.Frame):
    def __init__(self, parent, data_manager):
        super().__init__(parent)
        self.data_manager = data_manager
        self.current_entry = None
        self.create_widgets()

    def create_widgets(self):
        # Title
        ttk.Label(self, text="Title:").grid(row=0, column=0, sticky=tk.W)
        self.title_entry = ttk.Entry(self, width=50)
        self.title_entry.grid(row=0, column=1, sticky=tk.EW)

        # Date
        ttk.Label(self, text="Date:").grid(row=1, column=0, sticky=tk.W)
        self.date_label = ttk.Label(self, text=datetime.now().strftime("%Y-%m-%d"))
        self.date_label.grid(row=1, column=1, sticky=tk.W)

        # Content
        self.content_text = tk.Text(self, wrap=tk.WORD, width=60, height=20)
        self.content_text.grid(row=2, column=0, columnspan=2, sticky=tk.NSEW)

        # Formatting Toolbar
        toolbar = ttk.Frame(self)
        toolbar.grid(row=3, column=0, columnspan=2, sticky=tk.W)
        self.bold_btn = ttk.Button(toolbar, text="Bold", command=lambda: self.apply_formatting('bold'))
        self.bold_btn.pack(side=tk.LEFT)
        self.italic_btn = ttk.Button(toolbar, text="Italic", command=lambda: self.apply_formatting('italic'))
        self.italic_btn.pack(side=tk.LEFT)

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=5)
        ttk.Button(btn_frame, text="Save Entry", command=self.save_entry).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Load Entries", command=self.load_entries).pack(side=tk.LEFT)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

    def apply_formatting(self, format_type):
        try:
            start = self.content_text.index(tk.SEL_FIRST)
            end = self.content_text.index(tk.SEL_LAST)
            self.content_text.tag_add(format_type, start, end)
            self.content_text.tag_config(format_type, 
                font=('TkDefaultFont', 10, 'bold' if format_type == 'bold' else 'italic'))
        except tk.TclError:
            pass

    def save_entry(self):
        entry = {
            "title": self.title_entry.get(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "content": self.content_text.get("1.0", tk.END),
            "formatted_text": self.get_formatted_ranges()
        }
        self.data_manager.add_journal_entry(entry)
        messagebox.showinfo("Success", "Entry saved successfully!")

    def get_formatted_ranges(self):
        formatted = {"bold_ranges": [], "italic_ranges": []}
        for tag in ["bold", "italic"]:
            ranges = []
            start = "1.0"
            while True:
                pos = self.content_text.tag_nextrange(tag, start)
                if not pos:
                    break
                ranges.append([self.content_text.index(pos[0]), self.content_text.index(pos[1])])
                start = pos[1]
            if tag == "bold":
                formatted["bold_ranges"] = ranges
            else:
                formatted["italic_ranges"] = ranges
        return formatted

    def load_entries(self):
        entries = self.data_manager.data['journals']
        if not entries:
            messagebox.showinfo("Info", "No entries found!")
            return
        
        win = tk.Toplevel(self)
        win.title("Load Entries")
        listbox = tk.Listbox(win, width=60)
        listbox.pack(padx=10, pady=10)
        
        for entry in entries:
            listbox.insert(tk.END, f"{entry['date']} - {entry['title']}")
        
        def load_selected():
            index = listbox.curselection()
            if index:
                self.show_entry(entries[index[0]])
                win.destroy()
        
        ttk.Button(win, text="Load Selected", command=load_selected).pack(pady=5)

    def show_entry(self, entry):
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, entry['title'])
        self.date_label.config(text=entry['date'])
        self.content_text.delete("1.0", tk.END)
        self.content_text.insert("1.0", entry['content'])
        
        # Apply formatting
        for tag in self.content_text.tag_names():
            self.content_text.tag_remove(tag, "1.0", tk.END)
        
        for start, end in entry['formatted_text']['bold_ranges']:
            self.content_text.tag_add('bold', start, end)
        for start, end in entry['formatted_text']['italic_ranges']:
            self.content_text.tag_add('italic', start, end)

class VisionBoardFrame(ttk.Frame):
    def __init__(self, parent, data_manager):
        super().__init__(parent)
        self.data_manager = data_manager
        self.current_board = self.data_manager.data['vision_boards'][0]
        self.images = []
        self.create_widgets()
        self.load_images()

    def create_widgets(self):
        # Image Display
        self.canvas = tk.Canvas(self, bg='white')
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.grid(row=0, column=0, sticky=tk.NSEW)
        self.scrollbar.grid(row=0, column=1, sticky=tk.NS)
        
        # Controls
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=5)
        ttk.Button(btn_frame, text="Add Image", command=self.add_image).pack(side=tk.LEFT)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def add_image(self):
        filetypes = (("Image files", "*.jpg *.jpeg *.png"), ("All files", "*.*"))
        filepath = filedialog.askopenfilename(title="Select Image", filetypes=filetypes)
        if filepath:
            filename = os.path.basename(filepath)
            dest = os.path.join(self.data_manager.image_dir, filename)
            shutil.copy(filepath, dest)
            self.data_manager.add_image_to_board(self.current_board['name'], dest)
            self.load_images()

    def load_images(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        row, col = 0, 0
        for img_path in self.current_board['images']:
            try:
                img = Image.open(img_path)
                img.thumbnail((200, 200))
                photo = ImageTk.PhotoImage(img)
                label = ttk.Label(self.scrollable_frame, image=photo)
                label.image = photo  # Keep reference
                label.grid(row=row, column=col, padx=5, pady=5)
                col += 1
                if col > 2:
                    col = 0
                    row += 1
            except Exception as e:
                print(f"Error loading image {img_path}: {str(e)}")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("My Journal & Vision Board")
        self.geometry("1000x600")
        self.data_manager = DataManager()
        
        self.create_sidebar()
        self.create_main_content()
        
        self.show_journal()

    def create_sidebar(self):
        sidebar = ttk.Frame(self, width=150, relief=tk.RAISED, borderwidth=1)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        
        ttk.Button(sidebar, text="Journal", command=self.show_journal).pack(pady=10, padx=5, fill=tk.X)
        ttk.Button(sidebar, text="Vision Board", command=self.show_vision_board).pack(pady=10, padx=5, fill=tk.X)

    def create_main_content(self):
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.journal_frame = JournalFrame(self.main_frame, self.data_manager)
        self.vision_board_frame = VisionBoardFrame(self.main_frame, self.data_manager)
        
        self.journal_frame.pack(fill=tk.BOTH, expand=True)
        self.vision_board_frame.pack_forget()

    def show_journal(self):
        self.vision_board_frame.pack_forget()
        self.journal_frame.pack(fill=tk.BOTH, expand=True)

    def show_vision_board(self):
        self.journal_frame.pack_forget()
        self.vision_board_frame.pack(fill=tk.BOTH, expand=True)
        self.vision_board_frame.load_images()

if __name__ == "__main__":
    app = App()
    app.mainloop()