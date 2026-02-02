FROM runpod/pytorch:2.4.0-py3.11-cuda12.1.0-devel-ubuntu22.04

WORKDIR /workspace

# MamayLM model dependencies
RUN pip install --no-cache-dir \
    vllm \
    transformers \
    accelerate \
    bitsandbytes

# Download MamayLM model
RUN python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('lang-uk/MamayLM-Gemma-2-9B')"

EXPOSE 8000

CMD ["python", "-m", "vllm.entrypoints.openai.api_server", \
     "--model", "lang-uk/MamayLM-Gemma-2-9B", \
     "--host", "0.0.0.0", \
     "--port", "8000"]
