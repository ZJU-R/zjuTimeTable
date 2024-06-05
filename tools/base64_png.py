from PIL import Image
import base64
from io import BytesIO

def compress_image(image, reduction_factor, quality=10):
    # Calculate new dimensions
    width, height = image.size
    new_width = int(width * reduction_factor)
    new_height = int(height * reduction_factor)

    # Resize and compress the image
    resized_image = image.resize((new_width, new_height), Image.LANCZOS)
    compressed_image = BytesIO()
    resized_image.save(compressed_image, format='JPEG', optimize=True, quality=quality)
    compressed_image.seek(0)

    return compressed_image

def binary_search_compression(image, target_size_kb):
    low, high = 0.01, 1.0
    best_compressed_image = None
    eps = 1e-6
    while low <= high:
        mid = (low + high) / 2
        compressed_image = compress_image(image, mid)
        size_kb = len(compressed_image.getvalue()) / 1024
        print(f"Size: {size_kb:.2f} KB, Reduction factor: {mid:.2f}")
        if size_kb >= target_size_kb:
            best_compressed_image = compressed_image
            high = mid - eps
        else:
            low = mid + eps

    # If the smallest reduction factor still results in a size > 1KB,
    # try lowering the quality of the image further
    if best_compressed_image is None:
        for quality in range(80, 20, -10):
            compressed_image = compress_image(image, low, quality)
            size_kb = len(compressed_image.getvalue()) / 1024
            if size_kb <= target_size_kb:
                return compressed_image

        raise ValueError("Could not compress the image to the target size")

    return best_compressed_image

# Target size in KB
target_size_kb = 5

# Path to the original image
image_path = "assets/Snipaste_2024-06-05_22-46-58.png"

# Load the image
image = Image.open(image_path)

# Compress the image using binary search
compressed_image = binary_search_compression(image, target_size_kb)

# Convert image to base64
base64_encoded_image = base64.b64encode(compressed_image.getvalue()).decode('utf-8')
base64_image_tag = f'src="data:image/jpeg;base64,{base64_encoded_image}"'

# Save the base64 image tag to a file
with open("base64_image_tag.txt", "w") as f:
    f.write(base64_image_tag)

print("Image compressed and saved as base64 successfully.")
