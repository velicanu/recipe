import os
from tempfile import TemporaryDirectory

from app import main


def test_main():
    expected = "done"
    with TemporaryDirectory() as temp_dir:
        os.mkdir(os.path.join(temp_dir, "Nutrition"))
        actual = main(temp_dir)
    assert actual == expected
