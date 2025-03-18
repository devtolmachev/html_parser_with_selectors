import asyncio
import traceback
from concurrent.futures import ThreadPoolExecutor

import uvicorn
from fastapi import FastAPI, Request
from loguru import logger
from pydantic import BaseModel

from html_parser_with_selectors.main import Parser
from html_parser_with_selectors.secure import get_token

app = FastAPI(debug=True)
thread_pool = ThreadPoolExecutor(max_workers=30)


class HtmlReqBody(BaseModel):
    html: str


@app.post(
    "/parse_html", 
    description="In this endpoint you should but only html content of the interested page"
)
async def parse_html(request: Request, req_body: HtmlReqBody):
    if request.headers.get('auth') != get_token():
        return {"ok": False, "message": "authentification required"}
    
    message = "error when parsing html. give me a valid html string"
    loop = asyncio.get_running_loop()
    try:
        html = req_body.html
        
        parser = Parser(html)
        message = "parser error. html is valid"
        result = await loop.run_in_executor(
            thread_pool, 
            parser.parse_all
        )
        return {
            "ok": True,
            "result": result,
            "message": "html parsing completed successfully"
        }
        
    except Exception as e:
        msg = f"error parsing html: {e}. stack: {traceback.format_exc()}"
        logger.error(msg)
        return {
            "ok": False, 
            "message": message
        }
        

if __name__ == "__main__":
    import sys
    
    logger.remove(0)
    logger.add(sys.stderr, level="INFO", diagnose=True, backtrace=True)
    logger.add(
        "logs/log_{time}.log",
        rotation="1 week",
        level="DEBUG",
        backtrace=True,
        diagnose=True,
        enqueue=True,
        compression="bz2"
    )
    uvicorn.run(app, host="0.0.0.0", port=3645)
