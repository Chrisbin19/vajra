#!/bin/bash
# Test Phase 1 — Run after: uvicorn main:app --reload

echo "=== TEST 1: Health Check ==="
curl -s http://localhost:8000/health | python3 -m json.tool

echo ""
echo "=== TEST 2: Text Input (English) ==="
curl -s -X POST "http://localhost:8000/api/v1/analyze/text" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "banking_client_01",
    "transcript": "Agent: Good morning, how can I help you today?\nCustomer: I have an unauthorized transaction of Rs.4200 on my account.",
    "metadata": {"channel": "phone", "call_date": "2024-01-15"}
  }' | python3 -m json.tool

echo ""
echo "=== TEST 3: Text Input (Hindi) ==="
curl -s -X POST "http://localhost:8000/api/v1/analyze/text" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "banking_client_01",
    "transcript": "एजेंट: नमस्ते, मैं आपकी कैसे मदद कर सकता हूं? ग्राहक: मेरे खाते से 4200 रुपये कट गए।"
  }' | python3 -m json.tool

echo ""
echo "=== TEST 4: Audio Input ==="
curl -s -X POST "http://localhost:8000/api/v1/analyze/audio" \
  -F "audio_file=@sample_call.mp3" \
  -F "client_id=banking_client_01" | python3 -m json.tool

echo ""
echo "=== TEST 5: Reject Invalid File Type ==="
curl -s -X POST "http://localhost:8000/api/v1/analyze/audio" \
  -F "audio_file=@document.pdf" \
  -F "client_id=banking_client_01" | python3 -m json.tool

echo ""
echo "=== TEST 6: Reject Empty Transcript ==="
curl -s -X POST "http://localhost:8000/api/v1/analyze/text" \
  -H "Content-Type: application/json" \
  -d '{"client_id": "banking_client_01", "transcript": "hi"}' | python3 -m json.tool
