import pytest

if __name__ == '__main__':
    pytest.main([
        "-n", "4",
        "--html=report.html",
        "tests/"
    ])
