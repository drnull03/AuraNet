# investment-dashboard/main.py
import subprocess
import httpx
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="AuraNet Wealth Management")
templates = Jinja2Templates(directory="templates")

CUSTOMER_API_URL = "http://customer-api:8000/customers"

@app.get("/", response_class=HTMLResponse)
async def serve_ui(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/customer/{customer_id}")
async def get_customer(customer_id: int):
    # The Unauthorized Path: Investment attempting to call Retail API
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{CUSTOMER_API_URL}/{customer_id}")
            if response.status_code == 200:
                return {"status": "success", "data": response.json()}
            return {"status": "error", "message": f"API returned {response.status_code}"}
    except httpx.RequestError as exc:
        return {"status": "blocked", "message": f"Datapath Error: {str(exc)}"}

@app.post("/api/cli")
async def execute_cli(command: str = Form(...)):
    # The try block must be explicitly declared here
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=5.0)
        output = result.stdout if result.returncode == 0 else result.stderr
        return {"output": output.strip() or "Command executed with no output."}
    except subprocess.TimeoutExpired:
        return {"output": "Connection Timeout: eBPF Datapath Drop. Packet did not reach destination."}
    except Exception as e:
        return {"output": f"Execution Error: {str(e)}"}