import os
from pathlib import Path
import grpc

from main.grpc import stt_pb2, stt_pb2_grpc


def transcribe_via_grpc(audio_path):
    target = os.getenv("STT_GRPC_TARGET", "grpc-server:50051")
    timeout = int(os.getenv("STT_GRPC_TIMEOUT_SECONDS", "600"))

    file_name = Path(audio_path).name
    with open(audio_path, "rb") as audio_file:
        request = stt_pb2.TranscribeRequest(
            audio=audio_file.read(),
            filename=file_name,
        )

    with grpc.insecure_channel(target) as channel:
        stub = stt_pb2_grpc.STTServiceStub(channel)
        response = stub.Transcribe(request, timeout=timeout)
        return response.text
