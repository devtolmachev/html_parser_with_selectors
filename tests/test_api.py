import os
import requests


def test_api():
    url = "http://34.175.153.160.host.secureserver.net:7236/parse_html"
    url = "http://127.0.0.1:3645/parse_html"
    
    test_html_dir = "./htmls_for_tests"
    for path in os.listdir(test_html_dir):
        if path[0].islower():
            continue
        if not path.endswith(".html"):
            continue
        
        with open(os.path.join(test_html_dir, path)) as f:
            data = {"html": f.read()}
            
        response = requests.post(
            url, 
            json=data,
            headers={"Auth": os.environ["token"]}
        )
        json = response.json()
        assert response.status_code == 200 and json["ok"] is True
        
    print(f"sucessfully tested all htmls in dir {test_html_dir}")


if __name__ == "__main__":
    test_api()
