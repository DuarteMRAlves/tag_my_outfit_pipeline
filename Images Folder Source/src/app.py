import argparse
import concurrent.futures as futures
import grpc
import grpc_reflection.v1alpha.reflection as grpc_reflect
import pathlib
import source_pb2 as source
import source_pb2_grpc as source_grpc

import pull_server


_SEND_FILES_INTERVAL = 10
_PULL_MODE = '--pull'
_PUSH_MODE = '--push'
_SERVICE_NAME = 'ImageSourceService'


def parse_argv():
    main_parser = argparse.ArgumentParser()
    main_parser.add_argument(
        'image_dir',
        help='source directory of the images to send'
    )
    main_parser.add_argument(
        '--port',
        type=int,
        default=50051,
        help='Port where the server should listen (defaults to 50051)'
    )
    return main_parser.parse_args()


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
    port = args.port
    print(f'Recovering images from {image_dir}')
    run_pull_mode(image_dir, port)


if __name__ == '__main__':
    main()
