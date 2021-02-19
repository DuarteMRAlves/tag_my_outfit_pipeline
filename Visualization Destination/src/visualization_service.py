import concurrent.futures as futures
import io
import logging
import time

import grpc
import grpc_reflection.v1alpha.reflection as grpc_reflect
import visualization_pb2 as vis
import visualization_pb2_grpc as vis_grpc
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

_MAX_WORKERS = 10
_SERVICE_NAME = 'VisualizationService'
_PORT = 8061
_ONE_DAY_IN_SECONDS = 60 * 60 * 24


class VisualizationServiceImpl(vis_grpc.VisualizationServiceServicer):
    """
    gRPC service to receive and process the received image
    It resizes the images and adds the categories and attributes
    so that they can be displayed
    """

    def __init__(self, current_image):
        self.__current_img = current_image
        self.__font = PIL.ImageFont.load_default()

    def Visualize(self, request: vis.VisualizationRequest, context):
        image_bytes = request.image.data
        original_img = PIL.Image.open(io.BytesIO(image_bytes))
        original_img = original_img.resize((300, 300))

        # Add space for text
        new_img = PIL.Image.new(original_img.mode, (500, 300), (255, 255, 255))
        new_img.paste(original_img, (0, 0))

        # Add text to image
        text = f'{self.__build("Categories", request.prediction.categories)}\n\n' \
            f'{self.__build("Attributes", request.prediction.attributes)}'
        editable_img = PIL.ImageDraw.Draw(new_img)
        editable_img.text((315, 15), text, (0, 0, 0), font=self.__font)

        # Save image to bytes
        image_bytes = io.BytesIO()
        new_img.save(image_bytes, format='jpeg')
        image_bytes = image_bytes.getvalue()
        self.__current_img.bytes = image_bytes
        return vis.Empty()

    @staticmethod
    def __build(title, correspondence_list):
        correspondence_str = '\n'.join(
            map(lambda x: f'{x.label}:{x.value}',
                correspondence_list))
        return f'{title}:\n{correspondence_str}'


def run_server(shared_img):
    """
    Runs the gRPC server that receives the requests
    and updates the shared image with the most recent request

    Args:
        shared_img: shared image that should be updated by
                    the server with the most recent request

    """
    logging.basicConfig(level=logging.DEBUG)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=_MAX_WORKERS))
    vis_grpc.add_VisualizationServiceServicer_to_server(
        VisualizationServiceImpl(shared_img), server)
    service_names = (
        vis.DESCRIPTOR.services_by_name[_SERVICE_NAME].full_name,
        grpc_reflect.SERVICE_NAME
    )
    grpc_reflect.enable_server_reflection(service_names, server)
    server.add_insecure_port(f'[::]:{_PORT}')
    server.start()
    logging.info('Server started at [::]:%s', _PORT)
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)
