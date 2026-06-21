from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
import os

app = FastAPI()

class ReportRequest(BaseModel):
    patient_name: str

@app.post("/api/reports/generate", response_class=PlainTextResponse)
def generate_report(req: ReportRequest):
    name = req.patient_name
    if not name:
        raise HTTPException(status_code=400, detail="Missing patient name")

    print(f"[Records Service] Shell executing report generation for: {name}")

    # 🚨 INTENTIONAL VULNERABILITY: Command Injection (RCE) 🚨
    # The application passes user input directly into a shell execution.
    # An attacker can append malicious shell commands like: "John_Doe; cat /etc/passwd"
    command = f"echo 'Report generated successfully for patient: {name}'"
    
    try:
        # os.popen executes the string directly in the underlying Linux shell
        output = os.popen(command).read()
        return output
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Shell execution failed: {str(e)}")

@app.get("/health")
def health_check():
    return {"status": "Records Service Online", "secure": True}

# To run locally without Docker for testing: uvicorn app:app --host 0.0.0.0 --port 5000
