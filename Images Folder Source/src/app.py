import os
import grpc
import sys

from google.protobuf.any_pb2 import Any
from pathlib import Path
from time import sleep

from pipeline.core.connections.grpc.service_pb2 import DataTransferRequest
from pipeline.core.connections.grpc.service_pb2_grpc import DataTransferServiceStub
from pipeline.core.messages.grpc.image_pb2 import Image
from outfit_tagging.interface.service_pb2 import PredictRequest


from transfer.streams import RequestsStream


_SEND_FILES_INTERVAL = 10


def parse_argv():
    argv = sys.argv
    if not argv or len(argv) != 4:
        print("Invalid command line arguments. 3 argument expected")
        exit(1)
    path = argv[1]
    if not os.path.exists(path):
        os.mkdir(path)
    elif not os.path.isdir(path):
        print("Invalid command line arguments. Directory expected")
        exit(1)
    return path, argv[2], int(argv[3])


def main():
    image_dir, next_node_host, next_node_port = parse_argv()
    print(f'Recovering images from {image_dir}')
    print(f'Connecting to next node at {next_node_host}:{next_node_port}')
    with grpc.insecure_channel(f'{next_node_host}:{next_node_port}') as channel:
        stub = DataTransferServiceStub(channel)

        while True:
            print('Sending files')
            requests = RequestsStream()
            responses = stub.Transfer(requests)
            for file in os.listdir(image_dir):
                path = Path(f'{image_dir}/{file}')
                print(path.stem)
                with open(path, 'rb') as fp:
                    image_bytes = fp.read()
                    message_metadata = Image(bytes=image_bytes,
                                             format=''.join(path.suffixes),
                                             name=path.stem)
                    message_payload = PredictRequest(image_data=image_bytes,
                                                     all_categories=False,
                                                     all_attributes=False)
                    metadata_any = Any()
                    metadata_any.Pack(message_metadata)
                    payload_any = Any()
                    payload_any.Pack(message_payload)
                    request = DataTransferRequest(payload=payload_any,
                                                  metadata=metadata_any)
                    requests.next(request)
            requests.complete()
            gather_responses = [r for r in responses]
            print(f'Confirmed {len(gather_responses)} requests')
            sleep(_SEND_FILES_INTERVAL)


if __name__ == '__main__':
    main()
