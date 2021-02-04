import concurrent.futures as futures
import grpc
import grpc_reflection.v1alpha.reflection as grpc_reflect
import logging
import multiprocessing
import visualization_pb2 as vis
import visualization_pb2_grpc as vis_grpc
import time

_MAX_WORKERS = 10
_SERVICE_NAME = 'VisualizationService'
_PORT = 50051
_ONE_DAY_IN_SECONDS = 60 * 60 * 24


class VisualizationServiceImpl(vis_grpc.VisualizationServiceServicer):

    def __init__(self, results_queue: multiprocessing.Queue):
        self.__results_queue = results_queue

    def Visualize(self, request: vis.VisualizationRequest, context):
        self.__results_queue.put(request)
        return vis.Empty()


def run_server(results_queue):
    logging.basicConfig(level=logging.DEBUG)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=_MAX_WORKERS))
    vis_grpc.add_VisualizationServiceServicer_to_server(
        VisualizationServiceImpl(results_queue), server)
    SERVICE_NAME = (
        vis.DESCRIPTOR.services_by_name[_SERVICE_NAME].full_name,
        grpc_reflect.SERVICE_NAME
    )
    grpc_reflect.enable_server_reflection(SERVICE_NAME, server)
    server.add_insecure_port(f'[::]:{_PORT}')
    server.start()
    logging.info('Server started at [::]:%s', _PORT)
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)
