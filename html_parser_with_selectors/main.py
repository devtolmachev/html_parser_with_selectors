import asyncio
import re
from typing import Any, Optional
import bs4
from loguru import logger


# example
# {
#   "title": "Test Page",
#   "description": "This is a test page",
#   "metatags": [
#     {
#       "selector": "meta[name=\"description\"]",
#       "content": "This is a test page"
#     }
#   ],
#   "external_links": [
#     {
#       "selector": "a:nth-child(1)",
#       "content": "External Link",
#       "href": "https://example.com"
#     }
#   ],
#   "internal_links": [
#     {
#       "selector": "a:nth-child(2)",
#       "content": "Internal Link",
#       "href": "/internal-link"
#     }
#   ],
#   "images": [
#     {
#       "selector": "img:nth-child(1)",
#       "alt": "Test Image",
#       "src": "image.jpg"
#     }
#   ],
#   "content": {
#     "h1": [
#       {
#         "selector": "h1:nth-child(1)",
#         "content": "Hello World"
#       }
#     ],
#     "h2": [],
#     "h3": [],
#     "h4": [],
#     "h5": [],
#     "h6": [],
#     "p": [
#       {
#         "selector": "p:nth-child(1)",
#         "content": "This is a paragraph."
#       }
#     ],
#     "div": []
#   }
# }


class Parser:
    
    def __init__(self, html: str) -> None:
        self._html = html
        self._soup = bs4.BeautifulSoup(html, "lxml")
        
    def _parse_title(self) -> Optional[str]:
        return self._soup.select_one("title").text
    
    def _parse_description(self) -> Optional[str]:
        return self._soup.find(
            "meta", 
            attrs={"name":"description"}
        ).attrs["content"]
        
    
    def generate_unique_selector(self, element: bs4.Tag):
        path = []
        while element:
            
            if not isinstance(element, bs4.Tag):
                element = element.parent
                continue
            
            selector = element.name
            if selector == "html":
                path.append(selector)
                break
            
            if element.name in ["source"]:
                element = element.parent
                continue

            # Если у элемента есть id, используем его как уникальный селектор
            if element.get('id'):
                selector += f"#{element['id']}"
                path.append(selector)
                break

            # Если у элемента есть класс, добавляем его
            elif element.get('class'):
                selector += '.' + '.'.join(element['class'])

            siblings = element.find_previous_siblings(element.name)
            if siblings:
                selector += f":nth-of-type({len(siblings) + 1})"

            path.append(selector)
            element = element.parent

        # Объединяем путь к элементу, начиная от корневого к узлу
        return ' '.join(reversed(path))

        
    def _parse_metatags(self) -> Optional[list[dict[str, Any]]]:
        metatags: bs4.ResultSet[bs4.Tag] = self._soup.find_all("meta")
        results = []
        for tag in metatags:
            try:
                tag_selector = self.generate_unique_selector(tag)
                
                for attr_key, attr_value in tag.attrs.items():
                    try:
                        parsed_tag_data = {
                            "selector": f'{tag_selector}[{attr_key}="{attr_value}"]',
                            "content": tag["content"]
                        }
                    except Exception as e:
                        logger.exception(e)
                        continue
                    results.append(parsed_tag_data)
            except Exception as e:
                logger.exception(e)
                continue
            
        return results
    
    def _parse_links(self) -> dict[str, list[dict[str, Any]]]:
        links: bs4.ResultSet[bs4.Tag] = self._soup.find_all("a")
        results = {"internal_links": [], "external_links": []}
        for tag in links:
            try:
                tag_selector = self.generate_unique_selector(tag)
                attr_key = "href"
                attr_value = tag.attrs[attr_key]
                
                parsed_tag_data = {
                    "selector": f'{tag_selector}[{attr_key}="{attr_value}"]',
                    "content": tag.text,
                    "href": tag["href"]
                }
                if tag["href"].count("http"):
                    results["external_links"].append(parsed_tag_data)
                else:
                    results["internal_links"].append(parsed_tag_data)
            except Exception as e:
                logger.exception(e)
                continue
            
        return results
    
    def _parse_image_elements(self) -> Optional[list[dict[str, Any]]]:
        images: bs4.ResultSet[bs4.Tag] = self._soup.find_all("img")
        results = []
        for tag in images:
            try:
                tag_selector = self.generate_unique_selector(tag)
                
                alt_tag_content = tag.attrs["alt"]
                src_tag_content = tag.attrs["src"]
                
                parsed_tag_data = {
                    "selector": tag_selector,
                    "alt": alt_tag_content,
                    "src": src_tag_content
                }
                results.append(parsed_tag_data)
            except Exception as e:
                logger.exception(e)
                continue
            
        return results
    
    def _parse_contents(self) -> list[dict[str, Any]]:
        contents: bs4.ResultSet[bs4.Tag] = self._soup.find_all(string=re.compile(".*"))
        results = []
        
        for tag in contents:

            try:
                if not tag.text or tag.text == "\n":
                    continue
                selector = self.generate_unique_selector(tag)
                text = tag.get_text(strip=True)
                
                selected_el = self._soup.select_one(selector)
                if not selected_el or selected_el.get_text(strip=True) != text:
                    continue
                
                tag_data = {
                    "selector": selector,
                    "content": text
                }
                results.append(tag_data)
            except Exception as e:
                logger.exception(e)
                continue
            
        
        return results
    
    def parse_all(self):
        obj = {}
        try:
            obj["title"] = self._parse_title()
        except Exception as e:
            logger.exception(e)
            obj["title"] = None
        
        try:
            obj["description"] = self._parse_description()
        except Exception as e:
            obj["description"] = None
            logger.exception(e)
            
        try:
            obj["metatags"] = self._parse_metatags()
        except Exception as e:
            obj["metatags"] = []
            logger.exception(e)
        
        try:
            obj["images"] = self._parse_image_elements()
        except Exception as e:
            obj["images"] = []
            logger.exception(e)
        
        try:
            obj["content"] = self._parse_contents()
        except Exception as e:
            obj["content"] = []
            logger.exception(e)
            
        links = {"internal_links": [], "external_links": []}
        try:
            links = self._parse_links()
            obj.update(links)
        except Exception as e:
            logger.exception(e)
            obj.update(links)
        
        return obj


def parse(html: str) -> dict[str, Any]:
    parser = Parser(html)
    return parser.parse_all()


async def main():
    from pprint import pprint
    import json
    with open("test.html") as f:
        html = f.read()
    result = parse(html)
    with open("result1.json", 'w') as f:
        json.dump(result, f, indent=2)
    for value in result["content"]:
        print()
        print(json.dumps(value, indent=2))
    # for row in result["images"]:
    #     print()
    #     print(row)
    ...


if __name__ == "__main__":
    asyncio.run(main())
