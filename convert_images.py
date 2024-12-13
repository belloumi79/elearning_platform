from PIL import Image
import os
import cairosvg

def convert_png_to_jpeg(png_path, jpeg_path):
    try:
        img = Image.open(png_path)
        img = img.convert("RGB")
        img.save(jpeg_path, "JPEG")
        print(f"Successfully converted {png_path} to {jpeg_path}")
    except Exception as e:
        print(f"Error converting {png_path}: {e}")

def convert_svg_to_jpeg(svg_path, jpeg_path):
    try:
        cairosvg.svg2png(url=svg_path, write_to=jpeg_path)
        print(f"Successfully converted {svg_path} to {jpeg_path}")
    except Exception as e:
        print(f"Error converting {svg_path}: {e}")

if __name__ == "__main__":
    if os.path.exists("classes_elearning.png"):
        convert_png_to_jpeg("classes_elearning.png", "classes_elearning.jpeg")
    elif os.path.exists("diagralle_classes.svg"):
        convert_svg_to_jpeg("diagralle_classes.svg", "classes_elearning.jpeg")
    if os.path.exists("packages_elearning.png"):
        convert_png_to_jpeg("packages_elearning.png", "packages_elearning.jpeg")
