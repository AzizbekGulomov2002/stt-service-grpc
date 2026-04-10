from celery import shared_task

from main.grpc_client import transcribe_via_grpc


@shared_task
def transcribe_audio(audio_path):
    return transcribe_via_grpc(audio_path)