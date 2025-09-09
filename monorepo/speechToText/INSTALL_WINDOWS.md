# Windows Installation Guide for Speech-to-Text Service

## Prerequisites

1. **Python 3.8+** (recommended: Python 3.11)
2. **FFmpeg** - Required for audio processing

## Step 1: Install FFmpeg

### Option A: Using Chocolatey (Recommended)
```powershell
# Install Chocolatey if you don't have it
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install FFmpeg
choco install ffmpeg
```

### Option B: Manual Installation
1. Download FFmpeg from https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to your PATH environment variable

## Step 2: Install Python Dependencies

### Method 1: Using the installation script (Recommended)
```powershell
cd monorepo\speechToText
python install_whisper.py
```

### Method 2: Manual installation
```powershell
# Install basic dependencies first
pip install -r requirements-simple.txt

# Install PyTorch (CPU version for better compatibility)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install Whisper
pip install openai-whisper
```

### Method 3: If the above fails, try this order
```powershell
# Upgrade pip and setuptools
python -m pip install --upgrade pip setuptools wheel

# Install PyTorch first
pip install torch torchaudio

# Install other dependencies
pip install fastapi uvicorn[standard] python-multipart pydantic numpy ffmpeg-python

# Install Whisper last
pip install openai-whisper
```

## Step 3: Verify Installation

```powershell
python -c "import whisper; import torch; print('✅ Installation successful!')"
```

## Step 4: Run the Service

```powershell
python app.py
```

The service should start on http://localhost:8001

## Troubleshooting

### Common Issues

1. **"ffmpeg not found"**
   - Make sure FFmpeg is installed and in your PATH
   - Restart your terminal after adding FFmpeg to PATH

2. **"No module named 'whisper'"**
   - Try: `pip install --upgrade openai-whisper`
   - Or: `pip install git+https://github.com/openai/whisper.git`

3. **PyTorch installation fails**
   - Try the CPU-only version: `pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu`

4. **"Microsoft Visual C++ 14.0 is required"**
   - Install Visual Studio Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Or install Visual Studio Community

5. **Permission errors**
   - Run PowerShell as Administrator
   - Or use: `pip install --user -r requirements.txt`

### Alternative: Use Conda

If pip continues to fail, try using conda:

```powershell
# Install conda if you don't have it
# Download from https://docs.conda.io/en/latest/miniconda.html

# Create a new environment
conda create -n speech-to-text python=3.11
conda activate speech-to-text

# Install dependencies
conda install pytorch torchaudio cpuonly -c pytorch
pip install fastapi uvicorn[standard] python-multipart pydantic numpy ffmpeg-python openai-whisper
```

## Testing

Run the test script to verify everything works:

```powershell
cd ..\..\  # Go back to project root
python test_speech_to_text.py
```

## Performance Notes

- The first time you run the service, Whisper will download the model (about 150MB for 'base' model)
- CPU-only PyTorch is slower but more compatible
- For better performance, consider installing CUDA version of PyTorch if you have an NVIDIA GPU
