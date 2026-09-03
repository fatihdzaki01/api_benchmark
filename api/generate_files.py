import os

FILES_DIR = os.path.join(os.path.dirname(__file__), "..", "files")

SIZES = {
    "file_1kb.bin": 1 * 1024,
    "file_10kb.bin": 10 * 1024,
    "file_1mb.bin": 1 * 1024 * 1024,
    "file_10mb.bin": 10 * 1024 * 1024,
    "file_100mb.bin": 100 * 1024 * 1024,
}


def generate_files():
    os.makedirs(FILES_DIR, exist_ok=True)

    for filename, size in SIZES.items():
        filepath = os.path.join(FILES_DIR, filename)
        if os.path.exists(filepath):
            print(f"[SKIP] {filename} already exists ({size} bytes)")
            continue
        print(f"[GENERATE] {filename} ({size} bytes)...")
        with open(filepath, "wb") as f:
            f.write(os.urandom(size))
        print(f"[DONE] {filename}")

    print("\nAll files generated successfully!")


if __name__ == "__main__":
    generate_files()
