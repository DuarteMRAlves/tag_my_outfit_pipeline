import grpc
import io
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import logging
import sys


from concurrent import futures
from multiprocessing import Process, Queue
from PIL import Image as PILImage
from pipeline.core.connections.grpc.service_pb2 import DataTransferResponse
from pipeline.core.connections.grpc import service_pb2_grpc
from pipeline.core.messages.grpc.image_pb2 import Image
from outfit_tagging.interface.service_pb2 import PredictResponse


_MAX_WORKERS = 10


class ServerImpl(service_pb2_grpc.DataTransferServiceServicer):

    def __init__(self, results_queue: 'Queue'):
        self.__results_queue = results_queue

    def Transfer(self, request_iterator, context):
        print("Received Transfer Request")
        for result in request_iterator:
            self.__results_queue.put(result)
        return [DataTransferResponse()]


def parse_argv():
    argv = sys.argv
    if len(argv) != 2:
        print(f'Invalid number of arguments: 1 expected but received {len(argv) - 1}')
        exit(1)
    return int(argv[1])


def format_predict_response(predict_response: 'PredictResponse'):
    return '\n'.join([f'Categories: {cat.label}, Value: {"{:.3f}".format(cat.value)}' for cat in predict_response.categories]) + \
            '\n' + \
            '\n'.join([f'Attribute: {attr.label}, Value: {"{:.3f}".format(attr.value)}' for attr in predict_response.attributes])


def visualize_results(results_queue: 'Queue'):
    """
    Function to display the received results using matplotlib
    :return:
    """

    fig, (ax1, ax2) = plt.subplots(ncols=2)

    last_image = np.zeros((100, 100))

    im = ax1.imshow(last_image)
    text = ax2.text(0, 0, 'Initial Text')
    while True:
        result = results_queue.get()
        if not result:
            break

        predict_response = PredictResponse()
        result.payload.Unpack(predict_response)
        text.set_text(format_predict_response(predict_response))

        result_image = Image()
        result.metadata.Unpack(result_image)
        im.set_data(PILImage.open(io.BytesIO(result_image.bytes)))
        plt.draw()
        plt.pause(1e-3)


def main():
    port = parse_argv()
    results_queue = Queue()
    visualization_process = Process(target=visualize_results, args=(results_queue,))
    visualization_process.start()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=_MAX_WORKERS))
    service_pb2_grpc.add_DataTransferServiceServicer_to_server(
        ServerImpl(results_queue), server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    server.wait_for_termination()
    visualization_process.join()


if __name__ == '__main__':
    logging.basicConfig()
    main()
