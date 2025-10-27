import os
import tempfile
import time
import uuid
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import whisper
import torch
import asyncio
import concurrent.futures
from difflib import SequenceMatcher

# Hugging Face transformers integration for Persian models
try:
    from transformers import pipeline, AutoProcessor, AutoModelForSpeechSeq2Seq
    import torch
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    pipeline = None

app = FastAPI(
    title="Speech-to-Text Service",
    version="1.0.0",
    description="سرویس تبدیل گفتار به متن با پشتیبانی از مدل‌های ترکیبی فارسی و انگلیسی",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global models
whisper_model = None
hf_models = {}

def diagnose_environment():
    """Diagnose PyTorch and CUDA environment"""
    print("🔍 Environment Diagnosis:")
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"GPU count: {torch.cuda.device_count()}")
        print(f"Current device: {torch.cuda.current_device()}")
        print(f"Device name: {torch.cuda.get_device_name()}")
        print(f"Memory allocated: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
        print(f"Memory reserved: {torch.cuda.memory_reserved() / 1024**3:.2f} GB")
    
    # Check transformers version
    try:
        import transformers
        print(f"Transformers version: {transformers.__version__}")
    except ImportError:
        print("Transformers not available")
    
    # Check whisper version
    try:
        import whisper
        print(f"Whisper available: True")
    except ImportError:
        print("Whisper not available")

# Persian models configuration (Hugging Face)
PERSIAN_MODELS = {
    "whisper_fa": "vhdm/whisper-large-fa-v1",
    "whisper_large": "openai/whisper-large-v3",  # Fallback model
    # Note: vhdm/persian-voice-v1 is a dataset, not a model
    # Using only verified speech recognition models
}

class TranscriptionRequest(BaseModel):
    language: Optional[str] = None
    model_size: str = "large"

class TranscriptionResponse(BaseModel):
    text: str
    language: str
    confidence: Optional[float] = None
    model_used: Optional[str] = None
    hybrid_results: Optional[Dict[str, Any]] = None

class HybridTranscriptionRequest(BaseModel):
    language: Optional[str] = "fa"
    use_hybrid: bool = True
    model_preference: Optional[str] = None  # "persian_voice", "whisper_fa", or "auto"

def load_whisper_model(model_size: str = "base"):
    """Load Whisper model with caching and comprehensive error handling"""
    global whisper_model
    
    if whisper_model is None:
        print(f"Loading Whisper model: {model_size}")
        
        # Clear GPU cache before loading
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            print("🧹 Cleared GPU cache before Whisper model loading")
        
        # Strategy 1: Try normal loading first
        try:
            whisper_model = whisper.load_model(model_size)
            print(f"✅ Whisper model {model_size} loaded successfully (normal method)")
            return whisper_model
            
        except Exception as e:
            print(f"❌ Normal Whisper loading failed: {e}")
            
            # Strategy 2: Force CPU loading if meta tensor error
            if "meta tensor" in str(e).lower() or "to_empty" in str(e).lower():
                print("🔧 Detected meta tensor issue, trying CPU-first approach...")
                
                try:
                    # Temporarily disable CUDA
                    import os
                    original_cuda_visible = os.environ.get('CUDA_VISIBLE_DEVICES')
                    os.environ['CUDA_VISIBLE_DEVICES'] = ''
                    
                    # Force reload whisper module to reset any cached GPU settings
                    import importlib
                    import whisper
                    importlib.reload(whisper)
                    
                    # Load on CPU
                    whisper_model = whisper.load_model(model_size)
                    print(f"✅ Whisper model {model_size} loaded on CPU")
                    
                    # Restore CUDA visibility
                    if original_cuda_visible is not None:
                        os.environ['CUDA_VISIBLE_DEVICES'] = original_cuda_visible
                    elif 'CUDA_VISIBLE_DEVICES' in os.environ:
                        del os.environ['CUDA_VISIBLE_DEVICES']
                    
                    # Try to move to GPU if available and desired
                    if torch.cuda.is_available():
                        try:
                            # Clear cache again
                            torch.cuda.empty_cache()
                            whisper_model = whisper_model.cuda()
                            print(f"✅ Successfully moved Whisper model to GPU")
                        except Exception as gpu_error:
                            print(f"⚠️ Could not move to GPU, staying on CPU: {gpu_error}")
                    
                    return whisper_model
                    
                except Exception as cpu_error:
                    print(f"❌ CPU loading also failed: {cpu_error}")
                    
            # Strategy 3: Try with explicit device parameter
            try:
                print("🔧 Trying explicit device parameter...")
                whisper_model = whisper.load_model(model_size, device="cpu")
                print(f"✅ Whisper model {model_size} loaded with explicit CPU device")
                return whisper_model
                
            except Exception as device_error:
                print(f"❌ Device-explicit loading failed: {device_error}")
                
            # Strategy 4: Try smaller model as fallback
            if model_size == "large":
                print("🔧 Trying smaller model as fallback...")
                try:
                    whisper_model = whisper.load_model("medium", device="cpu")
                    print(f"⚠️ Loaded medium model instead of large due to errors")
                    return whisper_model
                except Exception as fallback_error:
                    print(f"❌ Fallback to medium model also failed: {fallback_error}")
            
            # All strategies failed
            error_msg = f"All Whisper loading strategies failed. Original error: {str(e)}"
            print(f"❌ {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
    
    return whisper_model

def load_huggingface_model(model_name: str):
    """Load Hugging Face Persian model with proper error handling"""
    global hf_models
    
    if not HF_AVAILABLE:
        print("Hugging Face transformers not available - install transformers package")
        return None
    
    if model_name not in hf_models:
        try:
            print(f"Loading Hugging Face model: {model_name}")
            
            # Only load verified speech recognition models
            verified_models = [
                "vhdm/whisper-large-fa-v1",
                "openai/whisper-large-v3",
                "openai/whisper-large-v2",
                "openai/whisper-large"
            ]
            
            if model_name in verified_models:
                # Load Whisper-based model with proper device handling
                try:
                    # First try to load without specific device mapping to avoid meta tensor issues
                    pipe = pipeline(
                        "automatic-speech-recognition",
                        model=model_name,
                        torch_dtype=torch.float32,  # Use float32 to avoid precision issues
                        device=-1  # Force CPU first, then move to GPU if available
                    )
                    
                    # If CUDA is available and we successfully loaded, try to move to GPU
                    if torch.cuda.is_available():
                        try:
                            # Move pipeline model to GPU after loading
                            pipe.model = pipe.model.to("cuda")
                            pipe.device = torch.device("cuda")
                            print(f"✅ Successfully moved {model_name} to GPU")
                        except Exception as gpu_error:
                            print(f"⚠️ Could not move {model_name} to GPU, staying on CPU: {gpu_error}")
                            
                except Exception as load_error:
                    print(f"❌ Failed to load {model_name} with pipeline method: {load_error}")
                    
                    # Clear GPU cache before fallback attempt
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                        print("🧹 Cleared GPU cache before fallback attempt")
                    
                    # Fallback: try loading with explicit model and processor
                    try:
                        from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
                        processor = AutoProcessor.from_pretrained(model_name)
                        model = AutoModelForSpeechSeq2Seq.from_pretrained(
                            model_name,
                            torch_dtype=torch.float32,
                            low_cpu_mem_usage=True,
                            use_safetensors=True,
                            device_map="auto" if torch.cuda.is_available() else None
                        )
                        
                        # If device_map didn't work, manually move to device
                        if not torch.cuda.is_available() or model.device.type == 'cpu':
                            device = "cuda" if torch.cuda.is_available() else "cpu"
                            try:
                                model = model.to(device)
                                print(f"✅ Moved {model_name} to {device}")
                            except Exception as move_error:
                                print(f"⚠️ Could not move {model_name} to {device}: {move_error}")
                        
                        pipe = pipeline(
                            "automatic-speech-recognition",
                            model=model,
                            tokenizer=processor.tokenizer,
                            feature_extractor=processor.feature_extractor,
                            device=0 if torch.cuda.is_available() else -1
                        )
                        print(f"✅ Successfully loaded {model_name} with fallback method")
                    except Exception as fallback_error:
                        print(f"❌ Fallback loading also failed for {model_name}: {fallback_error}")
                        return None
                hf_models[model_name] = pipe
                print(f"✅ Hugging Face model {model_name} loaded successfully")
            else:
                print(f"⚠️ Model {model_name} is not in verified speech recognition models list")
                print(f"   Verified models: {verified_models}")
                return None
                
        except Exception as e:
            print(f"❌ Error loading Hugging Face model {model_name}: {e}")
            return None
    
    return hf_models[model_name]

def transcribe_with_huggingface_model(audio_file_path: str, model_name: str) -> Dict[str, Any]:
    """Transcribe audio using Hugging Face Persian model"""
    pipe = load_huggingface_model(model_name)
    if not pipe:
        return {"text": "", "confidence": 0.0, "error": "Hugging Face model not available"}
    
    try:
        # Transcribe using Hugging Face pipeline
        result = pipe(audio_file_path)
        
        # Extract text and confidence
        text = result.get("text", "").strip()
        
        # Calculate confidence from logits if available
        confidence = 0.9  # Default confidence for HF models
        if "chunks" in result and result["chunks"]:
            # Try to extract confidence from chunks
            confidences = []
            for chunk in result["chunks"]:
                if "score" in chunk:
                    confidences.append(chunk["score"])
            if confidences:
                confidence = sum(confidences) / len(confidences)
        
        return {
            "text": text,
            "confidence": confidence,
            "model": model_name,
            "error": None
        }
        
    except Exception as e:
        print(f"Error transcribing with Hugging Face model {model_name}: {e}")
        return {
            "text": "",
            "confidence": 0.0,
            "model": model_name,
            "error": str(e)
        }

def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts"""
    if not text1 or not text2:
        return 0.0
    
    # Normalize texts
    text1 = text1.strip().lower()
    text2 = text2.strip().lower()
    
    if text1 == text2:
        return 1.0
    
    # Use SequenceMatcher for similarity
    similarity = SequenceMatcher(None, text1, text2).ratio()
    return similarity

def combine_transcription_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Combine multiple transcription results intelligently"""
    if not results:
        return {"text": "", "confidence": 0.0, "model_used": "none"}
    
    # Filter out failed results
    valid_results = [r for r in results if r.get("text") and not r.get("error")]
    
    if not valid_results:
        return {"text": "", "confidence": 0.0, "model_used": "none", "error": "All models failed"}
    
    if len(valid_results) == 1:
        result = valid_results[0]
        return {
            "text": result.get("text", ""),
            "confidence": result.get("confidence", 0.0),
            "model_used": result.get("model", "unknown"),
            "models_compared": 1
        }
    
    # Sort by confidence (highest first)
    valid_results.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)
    
    # Use the best result
    best_result = valid_results[0]
    best_text = best_result.get("text", "")
    best_conf = best_result.get("confidence", 0.0)
    best_model = best_result.get("model", "unknown")
    
    # If we have multiple results, calculate similarity with the second best
    if len(valid_results) > 1:
        second_best = valid_results[1]
        second_text = second_best.get("text", "")
        similarity = calculate_text_similarity(best_text, second_text)
        
        return {
            "text": best_text,
            "confidence": best_conf,
            "model_used": best_model,
            "similarity": similarity,
            "alternative": second_text,
            "models_compared": len(valid_results),
            "all_results": valid_results
        }
    else:
        return {
            "text": best_text,
            "confidence": best_conf,
            "model_used": best_model,
            "models_compared": len(valid_results),
            "all_results": valid_results
        }

async def hybrid_transcribe(audio_bytes: bytes, language: str = "fa", model_preference: str = "auto") -> Dict[str, Any]:
    """Hybrid transcription using both Persian models"""
    temp_webm_path = None
    temp_wav_path = None
    
    try:
        print(f"Starting hybrid transcription for language: {language}")
        
        # Create temporary files
        timestamp = int(time.time() * 1000)
        temp_webm_path = os.path.join(os.getcwd(), f"hybrid_audio_{timestamp}.webm")
        temp_wav_path = os.path.join(os.getcwd(), f"hybrid_audio_{timestamp}.wav")
        
        # Write WebM file
        with open(temp_webm_path, 'wb') as f:
            f.write(audio_bytes)
            f.flush()
        
        # Convert WebM to WAV
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(temp_webm_path, format="webm")
            audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            audio.export(temp_wav_path, format="wav")
        except Exception as e:
            print(f"Audio conversion failed: {e}")
            return {"text": f"خطا در تبدیل فایل صوتی: {str(e)}", "confidence": 0.0, "error": str(e)}
        
        # Prepare results list
        results = []
        
        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            
            # Add Whisper transcription
            whisper_future = executor.submit(transcribe_with_whisper, temp_wav_path, language)
            futures.append(("whisper", whisper_future))
            
            # Add Hugging Face Persian models if available
            if HF_AVAILABLE:
                for model_key, model_name in PERSIAN_MODELS.items():
                    hf_future = executor.submit(transcribe_with_huggingface_model, temp_wav_path, model_name)
                    futures.append((model_key, hf_future))
            
            # Collect results
            for model_type, future in futures:
                try:
                    result = future.result(timeout=30)  # 30 second timeout per model
                    if result and result.get("text"):
                        results.append(result)
                        print(f"✅ {model_type} transcription successful")
                    else:
                        print(f"❌ {model_type} transcription failed")
                except Exception as e:
                    print(f"❌ {model_type} transcription error: {e}")
        
        # Combine results
        if results:
            combined_result = combine_transcription_results(results)
            print(f"🎯 Combined result: {combined_result.get('text', '')[:50]}...")
            return combined_result
        else:
            return {"text": "متأسفانه هیچ مدلی نتوانست صدا را تشخیص دهد", "confidence": 0.0, "error": "All models failed"}
            
    except Exception as e:
        print(f"Hybrid transcription error: {e}")
        return {"text": f"خطا در پردازش ترکیبی: {str(e)}", "confidence": 0.0, "error": str(e)}
    finally:
        # Clean up files
        for file_path in [temp_webm_path, temp_wav_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                    print(f"Cleaned up: {file_path}")
                except:
                    pass

def transcribe_with_whisper(audio_file_path: str, language: str) -> Dict[str, Any]:
    """Transcribe using Whisper model"""
    try:
        model = load_whisper_model("large")
        result = model.transcribe(audio_file_path, language=None, fp16=False)
        text = result["text"].strip()
        detected_language = result.get("language", "unknown")
        
        # Calculate confidence from segments
        confidence = 0.9
        if "segments" in result and result["segments"]:
            confidences = [seg.get("avg_logprob", 0) for seg in result["segments"] if "avg_logprob" in seg]
            if confidences:
                confidence = min(1.0, max(0.0, (sum(confidences) / len(confidences) + 1) / 2))
        
        return {
            "text": text,
            "confidence": confidence,
            "model": "whisper-large",
            "language": detected_language,
            "error": None
        }
    except Exception as e:
        print(f"Whisper transcription error: {e}")
        return {
            "text": "",
            "confidence": 0.0,
            "model": "whisper-large",
            "error": str(e)
        }

def simple_transcribe(model, audio_bytes, language):
    """Real transcription using WebM to WAV conversion + Whisper"""
    temp_webm_path = None
    temp_wav_path = None
    try:
        print(f"Audio data size: {len(audio_bytes)} bytes")
        
        # Create WebM file
        import time
        timestamp = int(time.time() * 1000)
        temp_webm_path = os.path.join(os.getcwd(), f"audio_{timestamp}.webm")
        temp_wav_path = os.path.join(os.getcwd(), f"audio_{timestamp}.wav")
        
        # Write WebM file
        with open(temp_webm_path, 'wb') as f:
            f.write(audio_bytes)
            f.flush()
        
        print(f"WebM file created: {temp_webm_path}")
        print(f"File size: {os.path.getsize(temp_webm_path)}")
        
        # Convert WebM to WAV using pydub
        try:
            from pydub import AudioSegment
            print("Converting WebM to WAV with pydub...")
            
            # Load WebM file
            audio = AudioSegment.from_file(temp_webm_path, format="webm")
            
            # Convert to WAV format with optimal settings for Whisper
            audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            audio.export(temp_wav_path, format="wav")
            
            print(f"WAV file created: {temp_wav_path}")
            print(f"WAV file size: {os.path.getsize(temp_wav_path)}")
            
        except Exception as convert_error:
            print(f"Pydub conversion failed: {convert_error}")
            return {"text": f"خطا در تبدیل فایل صوتی: {str(convert_error)}", "language": language, "confidence": 0.0}
        
        # Use Whisper to transcribe WAV
        try:
            print("Transcribing with Whisper...")
            result = model.transcribe(temp_wav_path, language=None, fp16=False)
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
        for file_path in [temp_webm_path, temp_wav_path]:
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
            if (filename.startswith("audio_") and 
                (filename.endswith(".wav") or filename.endswith(".webm"))):
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

@app.get("/diagnose", 
         summary="تشخیص محیط سیستم",
         description="بررسی وضعیت محیط PyTorch، CUDA و مدل‌های موجود",
         tags=["System"])
def diagnose():
    """Diagnose environment and return information"""
    try:
        info = {
            "pytorch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "transformers_available": HF_AVAILABLE
        }
        
        if torch.cuda.is_available():
            info.update({
                "cuda_version": torch.version.cuda,
                "gpu_count": torch.cuda.device_count(),
                "current_device": torch.cuda.current_device(),
                "device_name": torch.cuda.get_device_name(),
                "memory_allocated_gb": torch.cuda.memory_allocated() / 1024**3,
                "memory_reserved_gb": torch.cuda.memory_reserved() / 1024**3
            })
        
        if HF_AVAILABLE:
            import transformers
            info["transformers_version"] = transformers.__version__
        
        # Run environment diagnosis in console
        diagnose_environment()
        
        return {"status": "ok", "environment": info}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/health",
         summary="بررسی سلامت سرویس",
         description="بررسی وضعیت کلی سرویس و مدل‌های موجود",
         tags=["System"])
def health_check():
    """Health check endpoint"""
    hf_status = "available" if HF_AVAILABLE else "not available"
    persian_models_status = {}
    
    if HF_AVAILABLE:
        try:
            for model_key, model_name in PERSIAN_MODELS.items():
                try:
                    # Try to load model to check availability
                    pipe = load_huggingface_model(model_name)
                    persian_models_status[model_key] = "available" if pipe else "loading_failed"
                except Exception as e:
                    persian_models_status[model_key] = f"error: {str(e)[:50]}"
        except Exception as e:
            persian_models_status = {"error": f"Hugging Face connection failed: {str(e)[:50]}"}
    else:
        persian_models_status = {"error": "Hugging Face transformers not available"}
    
    return {
        "status": "ok",
        "service": "speech-to-text",
        "whisper_available": True,
        "huggingface_available": HF_AVAILABLE,
        "hf_status": hf_status,
        "persian_models": persian_models_status,
        "model": "large",
        "supported_languages": ["en", "fa", "auto"],
        "supported_formats": ["webm", "wav", "mp3"],
        "hybrid_mode": "available" if HF_AVAILABLE else "huggingface_not_available",
        "note": "Hybrid Persian speech recognition with Whisper + Hugging Face models"
    }

@app.post("/transcribe", 
           response_model=TranscriptionResponse,
           summary="تبدیل گفتار به متن",
           description="تبدیل فایل صوتی به متن با استفاده از مدل Whisper",
           tags=["Transcription"])
async def transcribe_audio(
    audio_file: UploadFile = File(..., description="فایل صوتی برای تبدیل"),
    language: Optional[str] = Form(None, description="زبان گفتار (اختیاری)"),
    model_size: str = Form("large", description="اندازه مدل Whisper")
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

@app.post("/transcribe-chat", 
           response_model=TranscriptionResponse,
           summary="تبدیل گفتار برای چت",
           description="تبدیل بهینه شده گفتار به متن برای رابط چت",
           tags=["Transcription"])
async def transcribe_for_chat(
    audio_file: UploadFile = File(..., description="فایل صوتی برای تبدیل"),
    language: str = Form("fa", description="زبان گفتار (پیش‌فرض: فارسی)")
):
    """
    Optimized transcription endpoint for chat interface
    """
    try:
        # Validate file type
        if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Load Whisper model
        model = load_whisper_model("large")
        
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

@app.post("/transcribe-hybrid", 
           response_model=TranscriptionResponse,
           summary="تبدیل ترکیبی گفتار",
           description="تبدیل گفتار با استفاده از مدل‌های ترکیبی فارسی برای حداکثر دقت",
           tags=["Transcription"])
async def transcribe_hybrid(
    audio_file: UploadFile = File(..., description="فایل صوتی برای تبدیل"),
    language: str = Form("fa", description="زبان گفتار (پیش‌فرض: فارسی)"),
    model_preference: str = Form("auto", description="ترجیح مدل (auto, persian_voice, whisper_fa)")
):
    """
    Hybrid transcription using both Persian models for maximum accuracy
    """
    try:
        # Validate file type
        if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Read audio data
        content = await audio_file.read()
        
        print(f"Hybrid transcription - Audio data size: {len(content)} bytes")
        print(f"Language: {language}, Model preference: {model_preference}")
        
        # Perform hybrid transcription
        try:
            result = await hybrid_transcribe(content, language, model_preference)
            
            # Extract results
            transcribed_text = result.get("text", "").strip()
            confidence = result.get("confidence", 0.0)
            model_used = result.get("model_used", "unknown")
            
            # Prepare hybrid results for response
            hybrid_results = {
                "similarity": result.get("similarity"),
                "alternative": result.get("alternative"),
                "models_compared": len([r for r in result.get("all_results", []) if r.get("text")]),
                "error": result.get("error")
            }
            
            return TranscriptionResponse(
                text=transcribed_text,
                language=language,
                confidence=confidence,
                model_used=model_used,
                hybrid_results=hybrid_results
            )
            
        except Exception as e:
            print(f"Hybrid transcription error: {e}")
            raise HTTPException(status_code=500, detail=f"Hybrid transcription failed: {e}")
                
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
        print(f"Hybrid transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Hybrid transcription failed: {str(e)}")

@app.get("/test-models",
         summary="تست مدل‌ها",
         description="تست تمام مدل‌های موجود با نمونه صوتی ساده",
         tags=["Testing"])
def test_models():
    """Test all available models with a simple audio sample"""
    try:
        # Create a simple test audio (silence)
        import numpy as np
        import soundfile as sf
        
        # Generate 1 second of silence at 16kHz
        sample_rate = 16000
        duration = 1.0
        silence = np.zeros(int(sample_rate * duration))
        
        # Save to temporary file
        temp_file = "test_silence.wav"
        sf.write(temp_file, silence, sample_rate)
        
        results = {}
        
        # Test Whisper
        try:
            whisper_result = transcribe_with_whisper(temp_file, "fa")
            results["whisper"] = {
                "status": "success" if whisper_result.get("text") else "failed",
                "text": whisper_result.get("text", ""),
                "confidence": whisper_result.get("confidence", 0.0)
            }
        except Exception as e:
            results["whisper"] = {"status": "error", "error": str(e)}
        
        # Test Hugging Face models
        if HF_AVAILABLE:
            for model_key, model_name in PERSIAN_MODELS.items():
                try:
                    hf_result = transcribe_with_huggingface_model(temp_file, model_name)
                    results[model_key] = {
                        "status": "success" if hf_result.get("text") else "failed",
                        "text": hf_result.get("text", ""),
                        "confidence": hf_result.get("confidence", 0.0)
                    }
                except Exception as e:
                    results[model_key] = {"status": "error", "error": str(e)}
        
        # Clean up
        import os
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        return {
            "test_results": results,
            "note": "Tested with 1 second of silence - models should return empty or minimal text"
        }
        
    except Exception as e:
        return {"error": f"Test failed: {str(e)}"}

@app.get("/models",
         summary="لیست مدل‌های موجود",
         description="دریافت اطلاعات مدل‌های موجود و وضعیت آنها",
         tags=["Models"])
def get_available_models():
    """Get information about available models"""
    models_info = {
        "whisper": {
            "name": "whisper-large",
            "type": "local",
            "language": "multilingual",
            "status": "available"
        }
    }
    
    if HF_AVAILABLE:
        try:
            for model_key, model_name in PERSIAN_MODELS.items():
                try:
                    # Try to load model to check availability
                    pipe = load_huggingface_model(model_name)
                    models_info[model_key] = {
                        "name": model_name,
                        "type": "huggingface",
                        "language": "persian",
                        "status": "available" if pipe else "loading_failed"
                    }
                except Exception as e:
                    models_info[model_key] = {
                        "name": model_name,
                        "type": "huggingface", 
                        "language": "persian",
                        "status": f"error: {str(e)[:50]}"
                    }
        except Exception as e:
            pass
    
    # Count available models
    available_count = sum(1 for model in models_info.values() if model.get("status") == "available")
    
    return {
        "models": models_info,
        "hybrid_mode": "available" if HF_AVAILABLE and available_count > 1 else "limited",
        "recommended_for_persian": "hybrid" if HF_AVAILABLE and available_count > 1 else "whisper",
        "available_models_count": available_count,
        "note": f"Using {available_count} models for hybrid transcription"
    }

if __name__ == "__main__":
    # Diagnose environment at startup
    diagnose_environment()
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
