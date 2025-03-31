""""" ZipNarc - File Compression and Extraction Tool

Copyright (c) 2024 Katoshi Nakamoto

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE. """

import os
import zipfile
import hashlib
from io import BytesIO
from PIL import Image, ImageTk
import wave
import zlib
import lzma
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import requests

# -------------------------------
# توابع مربوط به فشرده‌سازی و استخراج فایل‌ها (کد اصلی شما)
# -------------------------------

def calculate_hash(data):
    return hashlib.sha256(data).hexdigest()

def analyze_file(file_path):
    if file_path.endswith('.txt'):
        return 'text'
    elif file_path.endswith(('.png', '.jpg', '.jpeg', '.webp')):
        return 'image'
    elif file_path.endswith('.wav'):
        return 'audio'
    else:
        return 'unknown'

def compress_text(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    compressed_data = zlib.compress(text.encode('utf-8'), level=9)
    return compressed_data

def compress_image(file_path):
    img = Image.open(file_path)
    buffer = BytesIO()
    img.save(buffer, format='WEBP', quality=95, method=6)
    return buffer.getvalue()

def compress_audio(file_path):
    with wave.open(file_path, 'rb') as audio_file:
        frames = audio_file.readframes(-1)
        params = audio_file.getparams()
    compressed_frames = lzma.compress(frames)
    buffer = BytesIO()
    with wave.open(buffer, 'wb') as compressed_audio:
        compressed_audio.setparams(params)
        compressed_audio.writeframes(compressed_frames)
    return buffer.getvalue()

def create_narc(files_to_zip, output_narc_path):
    with zipfile.ZipFile(output_narc_path, 'w', compression=zipfile.ZIP_LZMA) as zipf:
        for file in files_to_zip:
            if os.path.exists(file):
                file_type = analyze_file(file)
                if file_type == 'text':
                    compressed_data = compress_text(file)
                elif file_type == 'image':
                    compressed_data = compress_image(file)
                elif file_type == 'audio':
                    compressed_data = compress_audio(file)
                else:
                    with open(file, 'rb') as f:
                        compressed_data = f.read()
                metadata = f"filename:{os.path.basename(file)};type:{file_type};hash:{calculate_hash(compressed_data)}"
                zipf.writestr(f'metadata_{os.path.basename(file)}.txt', metadata)
                zipf.writestr(f'compressed_{os.path.basename(file)}', compressed_data)
                print(f'File {file} successfully compressed and added to NARC.')
            else:
                print(f'File {file} does not exist and was not added.')

    messagebox.showinfo("Success", f'NARC file successfully created at {output_narc_path}.')

def extract_narc(narc_path, output_dir):
    if not os.path.exists(narc_path):
        messagebox.showerror("Error", f'File {narc_path} does not exist.')
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        with zipfile.ZipFile(narc_path, 'r') as zipf:
            zipf.extractall(output_dir)
            for file_info in zipf.infolist():
                if file_info.filename.startswith('compressed_'):
                    original_filename = file_info.filename.replace('compressed_', '')
                    folder_name = os.path.splitext(original_filename)[0]
                    folder_path = os.path.join(output_dir, folder_name)
                    if not os.path.exists(folder_path):
                        os.makedirs(folder_path)
                    extracted_file_path = os.path.join(output_dir, file_info.filename)
                    os.rename(extracted_file_path, os.path.join(folder_path, original_filename))
                    metadata_filename = f'metadata_{original_filename}.txt'
                    if metadata_filename in zipf.namelist():
                        extracted_metadata_path = os.path.join(output_dir, metadata_filename)
                        os.rename(extracted_metadata_path, os.path.join(folder_path, metadata_filename))
            messagebox.showinfo("Success", f'NARC files successfully extracted to {output_dir}.')
    except zipfile.BadZipFile:
        messagebox.showerror("Error", f'File {narc_path} is not a valid NARC file.')
    except Exception as e:
        messagebox.showerror("Error", f'Error extracting files: {e}')

def select_files():
    files = filedialog.askopenfilenames(
        title="Select Files", 
        filetypes=[("All Files", "*.*"), 
                   ("Text Files", "*.txt"), 
                   ("Image Files", "*.png;*.jpg;*.jpeg;*.webp"), 
                   ("Audio Files", "*.wav")]
    )
    if files:
        return files

def select_output_narc():
    output_path = filedialog.asksaveasfilename(
        defaultextension=".narc", 
        filetypes=[("NARC Files", "*.narc")], 
        title="Save NARC File"
    )
    if output_path:
        return output_path

# -------------------------------
# تابع دانلود تصویر از URL
# -------------------------------
def download_image(url):
    response = requests.get(url)
    response.raise_for_status()  # در صورت بروز خطا Exception تولید می‌کند
    return Image.open(BytesIO(response.content))

# -------------------------------
# کلاس SplashScreen بدون انیمیشن (بدون چرخش) و نمایش تمام صفحه
# -------------------------------
class SplashScreen(tk.Toplevel):
    def __init__(self, master, image_url, display_time=3000):
        super().__init__(master)
        self.master = master

        # دانلود تصویر از URL
        self.image_orig = download_image(image_url)

        # حذف نوار عنوان
        self.overrideredirect(True)

        # تنظیم به حالت تمام صفحه (fullscreen)
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"{screen_width}x{screen_height}+0+0")
        
        # تغییر اندازه تصویر به اندازه صفحه نمایش
        resized_image = self.image_orig.resize((screen_width, screen_height), Image.LANCZOS)
        self.image_tk = ImageTk.PhotoImage(resized_image)
        
        # ایجاد canvas و قرار دادن تصویر
        self.canvas = tk.Canvas(self, width=screen_width, height=screen_height, highlightthickness=0)
        self.canvas.pack()
        self.canvas.create_image(screen_width // 2, screen_height // 2, image=self.image_tk)

        # پس از display_time میلی‌ثانیه، اسپلش اسکرین بسته شده و پنجره اصلی نمایش داده می‌شود
        self.after(display_time, self.close)

    def close(self):
        self.destroy()
        self.master.deiconify()

# -------------------------------
# تابع اصلی برنامه
# -------------------------------
def main_app():
    # ایجاد پنجره اصلی و مخفی کردن آن تا بعد از نمایش اسپلش اسکرین
    root = tk.Tk()
    root.withdraw()  # پنجره اصلی در ابتدا مخفی است

    root.title("File Compression and Extraction")
    root.geometry("600x600")

    style = ttk.Style()
    style.configure('TButton', background='lightgray', foreground='black')
    style.map('TButton', background=[('active', 'black')])

    frame_compress = ttk.LabelFrame(root, text="Compress Files")
    frame_compress.pack(pady=10, padx=10, fill="x")
    
    button_compress = ttk.Button(frame_compress, text="Compress", 
                                 command=lambda: create_narc(select_files(), select_output_narc()), width=20)
    button_compress.grid(row=0, column=0, pady=10)

    frame_extract = ttk.LabelFrame(root, text="Extract Files")
    frame_extract.pack(pady=10, padx=10, fill="x")

    button_extract = ttk.Button(frame_extract, text="Extract NARC", 
                                command=lambda: extract_narc(
                                    filedialog.askopenfilename(filetypes=[("NARC Files", "*.narc")], title="Select NARC File"),
                                    filedialog.askdirectory(title="Select Extraction Path")
                                ), width=20)
    button_extract.grid(row=0, column=0, padx=5, pady=5)

    button_exit = ttk.Button(frame_extract, text="Exit", command=root.quit, width=20)
    button_exit.grid(row=1, column=0, padx=5, pady=5)

    # آدرس تصویر مورد نظر (تصویر به صورت full screen نمایش داده می‌شود)
    image_url = "https://i.ibb.co/LdgSPQTF/Untitled48-20250314013119.png"
    splash = SplashScreen(root, image_url, display_time=3000)  # نمایش به مدت 3 ثانیه

    root.mainloop()

if __name__ == "__main__":
    main_app()


