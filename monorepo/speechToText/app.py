import os
import tempfile
import time
import uuid
from typing import Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import whisper
import torch

app = FastAPI(title="Speech-to-Text Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global whisper model
whisper_model = None

class TranscriptionRequest(BaseModel):
    language: Optional[str] = None
    model_size: str = "base"

class TranscriptionResponse(BaseModel):
    text: str
    language: str
    confidence: Optional[float] = None

def load_whisper_model(model_size: str = "base"):
    """Load Whisper model with caching"""
    global whisper_model
    
    if whisper_model is None:
        print(f"Loading Whisper model: {model_size}")
        try:
            whisper_model = whisper.load_model(model_size)
            print(f"Whisper model {model_size} loaded successfully")
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to load Whisper model: {str(e)}")
    
    return whisper_model

def simple_transcribe(model, audio_bytes, language):
    """Real transcription using WebA to MP3 conversion + Whisper"""
    temp_weba_path = None
    temp_mp3_path = None
    try:
        print(f"Audio data size: {len(audio_bytes)} bytes")
        
        # Create WebA file
        import time
        timestamp = int(time.time() * 1000)
        temp_weba_path = os.path.join(os.getcwd(), f"audio_{timestamp}.weba")
        temp_mp3_path = os.path.join(os.getcwd(), f"audio_{timestamp}.mp3")
        
        # Write WebA file
        with open(temp_weba_path, 'wb') as f:
            f.write(audio_bytes)
            f.flush()
        
        print(f"WebA file created: {temp_weba_path}")
        print(f"File size: {os.path.getsize(temp_weba_path)}")
        
        # Convert WebA to MP3 using pydub
        try:
            from pydub import AudioSegment
            print("Converting WebA to MP3 with pydub...")
            
            # Load WebA file
            audio = AudioSegment.from_file(temp_weba_path, format="weba")
            
            # Convert to MP3 format
            audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            audio.export(temp_mp3_path, format="mp3")
            
            print(f"MP3 file created: {temp_mp3_path}")
            print(f"MP3 file size: {os.path.getsize(temp_mp3_path)}")
            
        except Exception as convert_error:
            print(f"Pydub conversion failed: {convert_error}")
            return {"text": f"خطا در تبدیل فایل صوتی: {str(convert_error)}", "language": language, "confidence": 0.0}
        
        # Use Whisper to transcribe MP3
        try:
            print("Transcribing with Whisper...")
            result = model.transcribe(temp_mp3_path, language=None, fp16=False)
            text = result["text"].strip()
            detected_language = result.get("language", "unknown")
            
            if text:
                print(f"Transcription successful: {text}")
                return {"text": text, "language": detected_language, "confidence": 0.9}
            else:
                return {"text": "متأسفانه نتوانستم صدا را تشخیص دهم", "language": language, "confidence": 0.0}
                
        except Exception as transcribe_error:
            print(f"Whisper transcription failed: {transcribe_error}")
            return {"text": f"خطا در transcription: {str(transcribe_error)}", "language": language, "confidence": 0.0}
                
    except Exception as e:
        print(f"Transcription error: {e}")
        return {"text": f"خطا در پردازش صدا: {str(e)}", "language": language, "confidence": 0.0}
    finally:
        # Clean up files
        for file_path in [temp_weba_path, temp_mp3_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                    print(f"Cleaned up: {file_path}")
                except:
                    pass

def cleanup_old_temp_files():
    """Clean up old temporary audio files"""
    try:
        current_dir = os.getcwd()
        for filename in os.listdir(current_dir):
            if filename.startswith("temp_audio_") and filename.endswith(".wav"):
                file_path = os.path.join(current_dir, filename)
                try:
                    # Check if file is older than 1 hour
                    if os.path.getmtime(file_path) < time.time() - 3600:
                        os.unlink(file_path)
                        print(f"Cleaned up old temp file: {filename}")
                except Exception as e:
                    print(f"Could not clean up old temp file {filename}: {e}")
    except Exception as e:
        print(f"Error during cleanup: {e}")

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "speech-to-text",
        "whisper_available": True,
        "supported_languages": ["en", "fa", "auto"],
        "note": "Using Whisper for high-quality speech recognition"
    }

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    model_size: str = Form("base")
):
    """
    Transcribe audio file to text using Whisper
    """
    try:
        # Validate file type
        if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Load Whisper model
        model = load_whisper_model(model_size)
        
        # Read audio data directly
        content = await audio_file.read()
        
        print(f"Audio data size: {len(content)} bytes")
        
        # Transcribe using Whisper
        try:
            result = simple_transcribe(model, content, language)
            
            # Extract text and language
            transcribed_text = result["text"].strip()
            detected_language = result.get("language", language or "unknown")
            
            # Calculate confidence (average of segment confidences if available)
            confidence = None
            if "segments" in result and result["segments"]:
                confidences = [seg.get("avg_logprob", 0) for seg in result["segments"] if "avg_logprob" in seg]
                if confidences:
                    # Convert log probability to confidence score (0-1)
                    confidence = min(1.0, max(0.0, (sum(confidences) / len(confidences) + 1) / 2))
            
            return TranscriptionResponse(
                text=transcribed_text,
                language=detected_language,
                confidence=confidence
            )
            
        except Exception as e:
            print(f"Transcription error: {e}")
            raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")
                
    except FileNotFoundError as e:
        if "ffmpeg" in str(e).lower():
            print(f"FFmpeg not found: {e}")
            raise HTTPException(
                status_code=500, 
                detail="FFmpeg is not installed or not in PATH. Please install FFmpeg and add it to your PATH environment variable."
            )
        else:
            print(f"File not found error: {e}")
            raise HTTPException(status_code=500, detail=f"File not found: {str(e)}")
    except ValueError as e:
        print(f"File validation error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid audio file: {str(e)}")
    except Exception as e:
        print(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.post("/transcribe-chat", response_model=TranscriptionResponse)
async def transcribe_for_chat(
    audio_file: UploadFile = File(...),
    language: str = Form("fa")  # Default to Persian for chat
):
    """
    Optimized transcription endpoint for chat interface
    """
    try:
        # Validate file type
        if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Load Whisper model
        model = load_whisper_model("base")
        
        # Read audio data
        content = await audio_file.read()
        
        print(f"Chat transcription - Audio data size: {len(content)} bytes")
        
        # Transcribe using Whisper
        try:
            result = simple_transcribe(model, content, language)
            
            # Extract text and language
            transcribed_text = result["text"].strip()
            detected_language = result.get("language", language or "unknown")
            
            # Calculate confidence (average of segment confidences if available)
            confidence = None
            if "segments" in result and result["segments"]:
                confidences = [seg.get("avg_logprob", 0) for seg in result["segments"] if "avg_logprob" in seg]
                if confidences:
                    # Convert log probability to confidence score (0-1)
                    confidence = min(1.0, max(0.0, (sum(confidences) / len(confidences) + 1) / 2))
            
            return TranscriptionResponse(
                text=transcribed_text,
                language=detected_language,
                confidence=confidence
            )
            
        except Exception as e:
            print(f"Chat transcription error: {e}")
            raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")
                
    except FileNotFoundError as e:
        if "ffmpeg" in str(e).lower():
            print(f"FFmpeg not found: {e}")
            raise HTTPException(
                status_code=500, 
                detail="FFmpeg is not installed or not in PATH. Please install FFmpeg and add it to your PATH environment variable."
            )
        else:
            print(f"File not found error: {e}")
            raise HTTPException(status_code=500, detail=f"File not found: {str(e)}")
    except ValueError as e:
        print(f"File validation error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid audio file: {str(e)}")
    except Exception as e:
        print(f"Chat transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
