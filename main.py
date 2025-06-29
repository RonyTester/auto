from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from playwright.sync_api import sync_playwright
import base64
import time
import os

app = FastAPI()

# Liberar CORS para testes externos
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "API funcionando"}

@app.post("/gerar-imagem")
async def gerar_imagem(request: Request):
    body = await request.json()
    prompt = body.get("prompt")
    if not prompt:
        return JSONResponse(content={"erro": "Prompt não encontrado"}, status_code=400)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://gemini.google.com/app")

        time.sleep(10)  # espera o site carregar
        page.fill("textarea", prompt)
        page.keyboard.press("Enter")
        time.sleep(15)  # espera imagem ser gerada

        img_element = page.locator("img").first
        img_src = img_element.get_attribute("src")

        if "base64" in img_src:
            base64_data = img_src.split(",")[1]
            filename = f"{int(time.time())}.png"
            with open(filename, "wb") as f:
                f.write(base64.b64decode(base64_data))
            browser.close()
            return {"imagem": f"https://{request.client.host}/{filename}"}

        browser.close()
        return JSONResponse(content={"erro": "Imagem não encontrada"}, status_code=500)

@app.get("/{filename}")
async def serve_image(filename: str):
    return FileResponse(filename)

# Iniciar o servidor no Render (usa variável PORT)
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
