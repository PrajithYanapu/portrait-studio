import os, json, uuid, base64
from datetime import datetime, timedelta, timezone
from io import BytesIO
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
app = FastAPI(title="Portrait Studio API")
origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://127.0.0.1:8001,http://localhost:8001,http://127.0.0.1:8002,http://localhost:8002").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
security = HTTPBasic()

def client():
    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key: raise HTTPException(503, "Cloud storage is not configured")
    return create_client(url, key)

def admin(credentials: HTTPBasicCredentials = Depends(security)):
    import secrets

    username = os.getenv("ADMIN_USERNAME")
    password = os.getenv("ADMIN_PASSWORD")

    if not username or not password:
        raise HTTPException(
            503,
            "Admin authentication is not configured"
        )

    if (
        not secrets.compare_digest(credentials.username, username)
        or not secrets.compare_digest(credentials.password, password)
    ):
        raise HTTPException(
            401,
            "Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"}
        )

    return True

@app.get('/api/health')
def health(): return {"status":"ok"}

@app.post('/api/portraits')
async def save_portrait(customer_name: str = Form(...), style: str = Form(...), settings_json: str = Form("{}"), original_photo: UploadFile = File(...), generated_portrait: UploadFile = File(...)):
    max_bytes = int(os.getenv("MAX_FILE_BYTES", "25000000"))
    original = await original_photo.read(); generated = await generated_portrait.read()
    if not original or not generated or len(original) > max_bytes or len(generated) > max_bytes: raise HTTPException(413, "Image missing or too large")
    sb = client(); bucket = os.getenv("SUPABASE_BUCKET", "portrait-uploads"); pid = str(uuid.uuid4())
    ext = (original_photo.filename or "photo.jpg").rsplit('.',1)[-1].lower()
    op, gp = f"{pid}/original.{ext}", f"{pid}/portrait.png"
    try:
        sb.storage.from_(bucket).upload(op, original, {"content-type": original_photo.content_type or "image/jpeg"})
        sb.storage.from_(bucket).upload(gp, generated, {"content-type":"image/png"})
        row = {"id":pid,"customer_name":customer_name[:120],"style":style[:80],"settings":json.loads(settings_json),"original_path":op,"generated_path":gp,"download_count":0}
        sb.table('portraits').insert(row).execute()
        return {"id":pid}
    except Exception as e:
        raise HTTPException(500, f"Could not save portrait: {str(e)}")

@app.post('/api/portraits/{portrait_id}/download')
def download_event(portrait_id: str):
    sb=client(); found=sb.table('portraits').select('download_count').eq('id',portrait_id).single().execute()
    count=int(found.data.get('download_count') or 0)+1
    sb.table('portraits').update({'download_count':count}).eq('id',portrait_id).execute()
    return {'download_count':count}

@app.get('/api/admin/portraits')
def list_portraits(_=Depends(admin)):
    sb=client(); rows=sb.table('portraits').select('*').order('created_at',desc=True).limit(500).execute().data
    bucket=os.getenv('SUPABASE_BUCKET','portrait-uploads')
    for row in rows:
        for key in ('original_path','generated_path'):
            row[key.replace('_path','_url')]=sb.storage.from_(bucket).create_signed_url(row[key],3600).get('signedURL')
    return rows
@app.delete('/api/admin/portraits/{portrait_id}')
def delete_portrait(portrait_id: str, _=Depends(admin)):
    try:
        sb = client()
        bucket = os.getenv('SUPABASE_BUCKET', 'portrait-uploads')

        # Find the portrait and its Storage file paths
        result = (
            sb.table('portraits')
            .select('id, original_path, generated_path')
            .eq('id', portrait_id)
            .limit(1)
            .execute()
        )

        if not result.data:
            raise HTTPException(404, "Portrait not found")

        row = result.data[0]

        # Delete both images from Supabase Storage
        storage_result = sb.storage.from_(bucket).remove([
            row['original_path'],
            row['generated_path']
        ])

        if getattr(storage_result, 'error', None):
            raise HTTPException(500, "Could not delete portrait images")

        # Delete the database record
        sb.table('portraits').delete().eq('id', portrait_id).execute()

        return {
            "message": "Portrait deleted successfully",
            "id": portrait_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Delete failed: {str(e)}")
