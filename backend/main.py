from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, RedirectResponse
from pydantic import BaseModel
import shutil, os, json
from backend.agent.graph import build_graph
from backend.config import settings
from backend.rag.ingest import ingest_document
from backend.db.database import init_db
from langchain_core.messages import HumanMessage

app = FastAPI(title="Voice RAG Agent")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Root redirect → no need to type /static/index.html ever again
@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")

app.mount("/static", StaticFiles(directory="frontend"), name="static")

init_db()
agent = build_graph()

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

@app.post("/chat")
async def chat(req: ChatRequest):
    state = {"messages": [HumanMessage(content=req.message)], "documents": [], "next_action": ""}
    result = agent.invoke(state)
    reply = result["messages"][-1].content
    return {"reply": reply}

@app.get("/chat/stream")
async def chat_stream(message: str):
    async def generate():
        state = {"messages": [HumanMessage(content=message)], "documents": [], "next_action": ""}
        result = agent.invoke(state)
        reply = result["messages"][-1].content
        for word in reply.split():
            yield f"data: {json.dumps({'token': word + ' '})}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/upload")
async def upload_doc(file: UploadFile = File(...)):
    try:
        upload_dir = settings.UPLOAD_DIR
        os.makedirs(upload_dir, exist_ok=True)
        path = os.path.join(upload_dir, file.filename)
        with open(path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        count = ingest_document(path)
        return {"message": f"Done! Ingested {count} chunks from '{file.filename}'. Now ask me anything about it!"}
    except Exception as e:
        return {"message": f"Upload failed: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
