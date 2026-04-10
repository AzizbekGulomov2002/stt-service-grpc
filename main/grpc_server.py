import os
from concurrent import futures

import grpc

from main.grpc import stt_pb2, stt_pb2_grpc
from main.transcription_backend import transcribe_via_http


class STTService(stt_pb2_grpc.STTServiceServicer):
    def Transcribe(self, request, context):
        try:
            text = transcribe_via_http(request.audio, request.filename or "audio.wav")
            return stt_pb2.TranscribeResponse(text=text)
        except Exception as exc:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return stt_pb2.TranscribeResponse(text="")


def serve():
    host = os.getenv("STT_GRPC_HOST", "0.0.0.0")
    port = os.getenv("STT_GRPC_PORT", "50051")
    workers = int(os.getenv("STT_GRPC_WORKERS", "8"))

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=workers))
    stt_pb2_grpc.add_STTServiceServicer_to_server(STTService(), server)
    server.add_insecure_port(f"{host}:{port}")
    server.start()
    print(f"gRPC STT server started on {host}:{port}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
