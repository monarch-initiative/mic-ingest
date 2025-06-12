import pytest
import requests
from bs4 import BeautifulSoup
import re
from unittest.mock import patch

@patch('requests.get')
def test_mock_reference_tag_parsing_structure(mock_get):
    mock_get.return_value.content = """
                                        <html>
                                            <body>
                                                <a name="reference1">Reference 1</a>
                                                <a name="reference2">Reference 2</a>
                                            </body>
                                        </body>
                                        </html>
                                    """
    response = requests.get("https://lpi.oregonstate.edu/mic/vitamins/biotin")
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    reference_anchors = soup.find_all("a", attrs={"name": re.compile(r"^reference\d+$")})
    assert len(reference_anchors) != 0

def test_html_structure():
    try:
        response = requests.get("https://lpi.oregonstate.edu/mic/vitamins/biotin")
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise e

    soup = BeautifulSoup(response.content, 'html.parser')
    reference_anchors = soup.find_all("a", attrs={"name": re.compile(r"^reference\d+$")})
    assert len(reference_anchors) != 0