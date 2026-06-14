# investment-dashboard/main.py
import os
import pty
import asyncio
import httpx
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
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
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{CUSTOMER_API_URL}/{customer_id}")
            if response.status_code == 200:
                return {"status": "success", "data": response.json()}
            return {"status": "error", "message": f"API returned {response.status_code}"}
    except httpx.RequestError as exc:
        return {"status": "blocked", "message": f"Datapath Error: {str(exc)}"}

@app.websocket("/ws/terminal/{user_type}")
async def terminal_ws(websocket: WebSocket, user_type: str):
    await websocket.accept()
    
    # Fork a new Linux Pseudo-Terminal (PTY)
    master_fd, slave_fd = pty.openpty()
    
    pid = os.fork()
    if pid == 0:
        # Child Process: Attach to the slave terminal and launch the shell
        os.setsid()
        os.dup2(slave_fd, 0)
        os.dup2(slave_fd, 1)
        os.dup2(slave_fd, 2)
        os.close(slave_fd)
        os.close(master_fd)

        # Set terminal environment variable
        env = os.environ.copy()
        env["TERM"] = "xterm-256color"

        # Spawn as 'diaa' or default 'root'
        if user_type == "diaa":
            os.execvpe("su", ["su", "-", "diaa"], env)
        else:
            os.execvpe("bash", ["bash"], env)
    
    # Parent Process: Bridge the WebSocket and the PTY Master
    os.close(slave_fd)
    
    async def read_from_pty():
        loop = asyncio.get_running_loop()
        try:
            while True:
                # Run the blocking PTY read in a thread executor
                data = await loop.run_in_executor(None, os.read, master_fd, 1024)
                if not data:
                    break
                await websocket.send_text(data.decode('utf-8', errors='replace'))
        except Exception:
            pass

    async def write_to_pty():
        try:
            while True:
                data = await websocket.receive_text()
                os.write(master_fd, data.encode('utf-8'))
        except WebSocketDisconnect:
            pass

    # Run the read and write bridges concurrently
    task1 = asyncio.create_task(read_from_pty())
    task2 = asyncio.create_task(write_to_pty())
    
    await asyncio.gather(task1, task2)