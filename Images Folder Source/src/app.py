import argparse
import concurrent.futures as futures
import grpc
import grpc_reflection.v1alpha.reflection as grpc_reflect
import pathlib
import source_pb2 as source
import source_pb2_grpc as source_grpc

import pull_server

from google.protobuf.any_pb2 import Any
from time import sleep

from pipeline.core.connections.grpc.service_pb2 import DataTransferRequest
from pipeline.core.connections.grpc.service_pb2_grpc import DataTransferServiceStub


from transfer.streams import RequestsStream


_SEND_FILES_INTERVAL = 10
_PULL_MODE = '--pull'
_PUSH_MODE = '--push'
_SERVICE_NAME = 'ImageSourceService'


def parse_argv():
    main_parser = argparse.ArgumentParser()
    main_parser.add_argument('image_dir', help='source directory of the images to send')
    subparsers = main_parser.add_subparsers(help='sub-command help', dest='sub_command')
    push_parser = subparsers.add_parser('push', help='Starts sending the data to the next node')
    push_parser.add_argument('next_node_host')
    push_parser.add_argument('next_node_port', type=int)
    pull_parser = subparsers.add_parser('pull', help='Creates a server that waits for request')
    pull_parser.add_argument('port', type=int)
    return main_parser.parse_args()


def run_push_mode(image_dir, next_node_host, next_node_port):
    print(f'Connecting to next node at {next_node_host}:{next_node_port}')
    with grpc.insecure_channel(f'{next_node_host}:{next_node_port}') as channel:
        stub = DataTransferServiceStub(channel)

        while True:
            print('Sending files')
            requests = RequestsStream()
            _ = stub.Transfer(requests)
            for path in filter(lambda x: x.is_file() and x.suffix in {'.jpg', '.png'}, image_dir.iterdir()):
                with open(path, 'rb') as fp:
                    image_bytes = fp.read()
                    message_metadata = source.Image(bytes=image_bytes,
                                                    format=''.join(path.suffixes),
                                                    name=path.stem)
                    message_payload = source.PredictRequest(image_data=image_bytes,
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
            sleep(_SEND_FILES_INTERVAL)


def run_pull_mode(image_dir, port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    source_grpc.add_ImageSourceServiceServicer_to_server(
        pull_server.PullServer(pathlib.Path(image_dir)),
        server)
    SERVICE_NAME = (
        source.DESCRIPTOR.services_by_name[_SERVICE_NAME].full_name,
        grpc_reflect.SERVICE_NAME
    )
    grpc_reflect.enable_server_reflection(SERVICE_NAME, server)
    server.add_insecure_port(f'[::]:{port}')
    print(f'Starting Pull Server at [::]:{port}')
    server.start()
    server.wait_for_termination()


def main():
    args = parse_argv()
    image_dir = args.image_dir
    print(f'Recovering images from {image_dir}')
    if args.sub_command == 'push':
        run_push_mode(image_dir, args.next_node_host, args.next_node_port)
    elif args.sub_command == 'pull':
        run_pull_mode(image_dir, args.port)


if __name__ == '__main__':
    main()
