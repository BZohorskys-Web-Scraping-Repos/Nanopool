import asyncio
import src.nanopool
import sys
import os

def main():
    asyncio.run(src.nanopool.search())

def get_resource_path(relative_path):
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

if __name__ == '__main__':
    sys.exit(main())