# 🧹 DeGrain Batch Processor

A simple Python tool for removing film grain and noise from images and videos using **OpenCV’s fastNlMeansDenoisingColored**.  
Supports batch processing of image folders, single images, and video files.  

---

## ✨ Features
- **Batch Processing** – Process entire folders of images or full video files  
- **Multiple Output Formats** – Save denoised images as **JPG, PNG, or EXR** (16-bit half precision for EXR)  
- **GUI & CLI** – Run with a user-friendly **Tkinter interface** or through the **command line**  
- **Preview Mode** – Quickly compare before/after results in the GUI  
- **Customizable Denoising Strength** – Adjust luminance (`h`) and color (`hColor`) separately  

---

## 🖥️ Usage

### GUI Mode
Run the script without arguments:
```bash
python degrain.py


Select input/output paths
Adjust sliders
Preview results
Process files

Command-Line Mode
python degrain.py --input INPUT_PATH --output OUTPUT_PATH --h 10 --hColor 10

Arguments:

--input : Input file or folder (video file or image sequence)
--output : Output file or folder
--h : Denoising strength for luminance (default: 10)
--hColor : Denoising strength for color (default: 10)

📂 Supported Input
Single images (.jpg, .png, .exr, etc.)
Folders of images
Video files (.mp4, .avi, .mov, .mkv, .webm)

📦 Requirements
Python 3.8+
OpenCV (cv2) with EXR enabled
Tkinter (for GUI)
Pillow (PIL)

Install dependencies:
pip install opencv-python pillow
