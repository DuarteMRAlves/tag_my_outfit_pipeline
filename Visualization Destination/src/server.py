import grpc
import io
import matplotlib.pyplot as plt
import logging
import sys


from concurrent import futures
from PIL import Image as PILImage
from pipeline.core.connections.grpc.service_pb2 import DataTransferResponse
from pipeline.core.connections.grpc import service_pb2_grpc
from pipeline.core.messages.grpc.image_pb2 import Image
from outfit_tagging.interface.service_pb2 import PredictResponse


_MAX_WORKERS = 10


class ServerImpl(service_pb2_grpc.DataTransferServiceServicer):

    def Transfer(self, request_iterator, context):
        print("Received Transfer Request")
        for request in request_iterator:
            print(request.request_id)
            request_metadata = request.metadata
            request_image = Image()
            request_metadata.Unpack(request_image)
            image_bytes = request_image.bytes
            image = PILImage.open(io.BytesIO(image_bytes))
            image.show()
            request_payload = request.payload
            predict_response = PredictResponse()
            request_payload.Unpack(predict_response)
            print(predict_response)
        return [DataTransferResponse()]


def parse_argv():
    argv = sys.argv
    if len(argv) != 2:
        print(f'Invalid number of arguments: 1 expected but received {len(argv) - 1}')
        exit(1)
    return int(argv[1])


def main():
    port = parse_argv()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=_MAX_WORKERS))
    service_pb2_grpc.add_DataTransferServiceServicer_to_server(
        ServerImpl(), server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    main()
