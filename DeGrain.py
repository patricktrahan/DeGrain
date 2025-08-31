import os
os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
import cv2
import tkinter as tk
from tkinter import filedialog, messagebox
from threading import Thread
def run_processing(input_path, output_path, h, hColor, fmt):
	# Accept fmt argument for image output format
	if os.path.isdir(input_path):
		process_images(input_path, output_path, h, hColor, fmt)
	elif os.path.isfile(input_path):
		if is_video_file(input_path):
			process_video(input_path, output_path, h, hColor)
		else:
			process_single_image(input_path, output_path, h, hColor, fmt)
	else:
		messagebox.showerror("Error", "Input must be a video file, a folder of images, or a single image file.")
def process_single_image(img_path, output_path, h, hColor, fmt):
	img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
	if img is None:
		print(f"Skipping {img_path}, not an image.")
		return
	denoised = denoise_image(img, h, hColor)
	base, _ = os.path.splitext(os.path.basename(img_path))
	if os.path.isdir(output_path):
		out_path = os.path.join(output_path, f"{base}.{fmt}")
	else:
		out_path = output_path
	if fmt == "exr":
		cv2.imwrite(out_path, denoised, [cv2.IMWRITE_EXR_TYPE, cv2.IMWRITE_EXR_TYPE_HALF])
	else:
		cv2.imwrite(out_path, denoised)
	print(f"Processed {img_path} -> {out_path}")

def launch_ui():
	root = tk.Tk()
	format_var = tk.StringVar(value="png")
	root.title("DeGrain Batch Processor")
	root.geometry("600x600")

	input_path = tk.StringVar()
	output_path = tk.StringVar()
	h_value = tk.IntVar(value=10)
	hColor_value = tk.IntVar(value=10)

	def select_input():
		path = filedialog.askopenfilename(title="Select Video File")
		if not path:
			path = filedialog.askdirectory(title="Select Image Folder")
		if path:
			input_path.set(path)

	def select_output():
		if os.path.isdir(input_path.get()):
			path = filedialog.askdirectory(title="Select Output Folder")
		else:
			path = filedialog.asksaveasfilename(title="Select Output Video File", defaultextension=".mp4", filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")])
		if path:
			output_path.set(path)

	def start_process():
		if not input_path.get() or not output_path.get():
			messagebox.showerror("Error", "Please select both input and output paths.")
			return
		btn_process.config(state=tk.DISABLED)
		def worker():
			try:
				run_processing(input_path.get(), output_path.get(), h_value.get(), hColor_value.get(), format_var.get())
				messagebox.showinfo("Done", "Processing complete!")
			except Exception as e:
				messagebox.showerror("Error", str(e))
			btn_process.config(state=tk.NORMAL)
		Thread(target=worker).start()

	tk.Label(root, text="Input (video file or image folder):").pack(pady=5)
	tk.Entry(root, textvariable=input_path, width=40).pack()
	tk.Button(root, text="Browse", command=select_input).pack(pady=2)

	tk.Label(root, text="Output (video file or folder):").pack(pady=5)
	tk.Entry(root, textvariable=output_path, width=40).pack()
	tk.Button(root, text="Browse", command=select_output).pack(pady=2)

	tk.Label(root, text="Denoising Strength (Luminance)").pack(pady=5)
	tk.Scale(root, from_=1, to=30, orient=tk.HORIZONTAL, variable=h_value).pack()

	tk.Label(root, text="Denoising Strength (Color)").pack(pady=5)
	tk.Scale(root, from_=1, to=30, orient=tk.HORIZONTAL, variable=hColor_value).pack()

	tk.Label(root, text="Output Format (images only):").pack(pady=5)
	format_frame = tk.Frame(root)
	format_frame.pack()
	for fmt in ["jpg", "png", "exr"]:
		tk.Radiobutton(format_frame, text=fmt.upper(), variable=format_var, value=fmt).pack(side=tk.LEFT)

	preview_frame = tk.Frame(root)
	preview_frame.pack(pady=10)

	preview_label = tk.Label(preview_frame, text="Preview (first image)")
	preview_label.pack()

	canvas = tk.Canvas(preview_frame, width=512, height=256)
	canvas.pack()

	def show_preview():
		import PIL.Image, PIL.ImageTk
		img_path = None
		if os.path.isdir(input_path.get()):
			files = sorted(glob(os.path.join(input_path.get(), '*.*')))
			if files:
				img_path = files[0]
		elif os.path.isfile(input_path.get()) and not is_video_file(input_path.get()):
			img_path = input_path.get()
		if img_path:
			img = cv2.imread(img_path)
			if img is not None:
				denoised = denoise_image(img, h_value.get(), hColor_value.get())
				img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
				den_rgb = cv2.cvtColor(denoised, cv2.COLOR_BGR2RGB)
				pil_img = PIL.Image.fromarray(img_rgb).resize((256,256))
				pil_den = PIL.Image.fromarray(den_rgb).resize((256,256))
				tk_img = PIL.ImageTk.PhotoImage(pil_img)
				tk_den = PIL.ImageTk.PhotoImage(pil_den)
				canvas.config(width=512, height=256)
				canvas.delete("all")
				canvas.create_image(0,0,anchor=tk.NW,image=tk_img)
				canvas.create_image(256,0,anchor=tk.NW,image=tk_den)
				canvas.image1 = tk_img
				canvas.image2 = tk_den
				preview_label.config(text="Preview: Before (left) / After (right)")
			else:
				preview_label.config(text="Preview: Unable to load image.")
		else:
			preview_label.config(text="Preview: No image found.")

	btn_preview = tk.Button(root, text="Preview Before/After", command=show_preview)
	btn_preview.pack(pady=2)

	btn_process = tk.Button(root, text="Process Files", command=start_process)
	btn_process.pack(pady=10)

	root.mainloop()
import os
import cv2
import argparse
from glob import glob

def denoise_image(img, h=10, hColor=10, templateWindowSize=7, searchWindowSize=21):
	# If image is not 8-bit, convert to 8-bit for denoising
	if img.dtype != 'uint8':
		# Scale to 0-255
		img_8bit = cv2.convertScaleAbs(img, alpha=(255.0/img.max() if img.max() > 0 else 1.0))
		denoised_8bit = cv2.fastNlMeansDenoisingColored(img_8bit, None, h, hColor, templateWindowSize, searchWindowSize)
		# Convert back to original bit depth
		denoised = denoised_8bit.astype(img.dtype)
		return denoised
	else:
		return cv2.fastNlMeansDenoisingColored(img, None, h, hColor, templateWindowSize, searchWindowSize)

def process_images(input_folder, output_folder, h, hColor, fmt):
	os.makedirs(output_folder, exist_ok=True)
	image_files = sorted(glob(os.path.join(input_folder, '*.*')))
	for img_path in image_files:
		img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
		if img is None:
			print(f"Skipping {img_path}, not an image.")
			continue
		denoised = denoise_image(img, h, hColor)
		base, _ = os.path.splitext(os.path.basename(img_path))
		out_path = os.path.join(output_folder, f"{base}.{fmt}")
		if fmt == "exr":
			cv2.imwrite(out_path, denoised, [cv2.IMWRITE_EXR_TYPE, cv2.IMWRITE_EXR_TYPE_HALF])
		else:
			cv2.imwrite(out_path, denoised)
		print(f"Processed {img_path} -> {out_path}")

def process_video(input_path, output_path, h, hColor):
	cap = cv2.VideoCapture(input_path)
	fourcc = cv2.VideoWriter_fourcc(*'mp4v')
	fps = cap.get(cv2.CAP_PROP_FPS)
	width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
	height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
	out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
	frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
	idx = 0
	while True:
		ret, frame = cap.read()
		if not ret:
			break
		denoised = denoise_image(frame, h, hColor)
		out.write(denoised)
		idx += 1
		print(f"Processed frame {idx}/{frame_count}")
	cap.release()
	out.release()
	print(f"Processed video saved to {output_path}")

def is_video_file(path):
	ext = os.path.splitext(path)[1].lower()
	return ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']

def main():
	parser = argparse.ArgumentParser(description="Batch DeGrain: Remove grain from videos or image sequences.")
	parser.add_argument('--input', required=True, help='Input file/folder (video file or image folder)')
	parser.add_argument('--output', required=True, help='Output file/folder')
	parser.add_argument('--h', type=int, default=10, help='Denoising strength for luminance (default: 10)')
	parser.add_argument('--hColor', type=int, default=10, help='Denoising strength for color (default: 10)')
	args = parser.parse_args()

	if os.path.isdir(args.input):
		print(f"Processing image sequence in {args.input}")
		process_images(args.input, args.output, args.h, args.hColor)
	elif os.path.isfile(args.input) and is_video_file(args.input):
		print(f"Processing video file {args.input}")
		process_video(args.input, args.output, args.h, args.hColor)
	else:
		print("Input must be a video file or a folder of images.")

if __name__ == "__main__":
	import sys
	if len(sys.argv) > 1:
		main()
	else:
		launch_ui()
