from pathlib import Path

def find_bad_bytes(path: str):
    p = Path(path)

    with p.open('rb') as f:
        for line_no, raw_line in enumerate(f, start=1):
            try:
                raw_line.decode('utf-8', errors='strict')
            except UnicodeDecodeError as e:
                print(f"⚠️  Problem in file: {p}")
                print(f"   Line number: {line_no}")
                print(f"   Error      : {e}")  # shows byte positions

                # Show the raw bytes around the error
                start = max(e.start - 10, 0)
                end = e.end + 10
                context = raw_line[start:end]

                print("\n   Raw bytes around error (hex):")
                print("   ", context.hex(" "))

                try:
                    # Replace bad bytes with � to show rest of the text
                    safe = raw_line.decode('utf-8', errors='replace')
                    print("\n   Line (with � for bad chars):")
                    print("   ", repr(safe))
                except Exception:
                    pass

                break  # stop at first error

    print("Scan done.")

if __name__ == "__main__":
    # change these paths as needed
    find_bad_bytes("your_text_file_here.txt")
