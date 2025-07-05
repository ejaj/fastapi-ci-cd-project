# test_split.py
import os
import sys


def get_test_files():
    all_files = []
    for root, _, files in os.walk("tests"):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                all_files.append(os.path.join(root, file))
    return sorted(all_files)


def main():
    shard = int(sys.argv[1])
    total_shards = int(sys.argv[2])
    files = get_test_files()
    selected = [f for i, f in enumerate(files) if i % total_shards == (shard - 1)]
    if not selected:
        print(f"No tests in shard {shard}")
        return
    print(f"Running tests in shard {shard}: {selected}")
    os.system("pytest " + " ".join(selected))


if __name__ == "__main__":
    main()
