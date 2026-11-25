import os,time,subprocess
from pathlib import Path
from google import genai
from google.genai import types

def _one(client,model,prompt,seconds,path):
    op=client.models.generate_videos(model=model,source=types.GenerateVideosSource(prompt=prompt),
        config=types.GenerateVideosConfig(number_of_videos=1,duration_seconds=seconds,aspect_ratio="16:9"))
    while not op.done:
        time.sleep(15); op=client.operations.get(op)
    generated=getattr(op.response,"generated_videos",None) if op.response else None
    if not generated: raise RuntimeError("No video returned. Check Veo access, billing and quota.")
    file=generated[0].video
    client.files.download(file=file)
    file.save(str(path))

def generate_video(api_key,model,prompt,duration_seconds,output_dir):
    if not 1<=duration_seconds<=180: raise ValueError("Duration must be 1–180 seconds.")
    os.makedirs(output_dir,exist_ok=True); client=genai.Client(api_key=api_key); clips=[]
    try:
        remaining=duration_seconds; idx=1
        while remaining:
            seconds=min(8,remaining)
            p=prompt if idx==1 else ("Continue the same scene smoothly; keep characters, clothing, setting, lighting and camera consistent. "+prompt)
            path=Path(output_dir)/f"clip_{int(time.time())}_{idx}.mp4"
            _one(client,model,p,seconds,path); clips.append(path); remaining-=seconds; idx+=1
        final=Path(output_dir)/f"video_{int(time.time())}.mp4"
        if len(clips)==1: clips[0].replace(final); return str(final)
        listing=Path(output_dir)/f"concat_{int(time.time())}.txt"
        listing.write_text("".join(f"file '{p.resolve()}'\n" for p in clips),encoding="utf-8")
        subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(listing),"-c","copy",str(final)],check=True,capture_output=True)
        listing.unlink(missing_ok=True)
        for p in clips: p.unlink(missing_ok=True)
        return str(final)
    finally: client.close()
