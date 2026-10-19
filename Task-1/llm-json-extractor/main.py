#Entry point: python main.py samples/invoice_1.txt --type invoice
import sys

from src.cli import main

if __name__ == "__main__":
    sys.exit(main())
