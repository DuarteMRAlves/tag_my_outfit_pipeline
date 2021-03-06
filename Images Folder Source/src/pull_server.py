import logging
import pathlib
import time

import source_pb2 as source
import source_pb2_grpc as source_grpc


_DELAY = 2


class PullServer(source_grpc.ImageSourceServiceServicer):

    def __init__(self, image_dir: pathlib.Path):
        self.__image_dir = image_dir

    def Get(self, request, context):
        image_path = None
        while True:
            directory_iter = self.__get_directory_images_iter()
            while not image_path:
                try:
                    image_path = next(directory_iter, None)
                except StopIteration:
                    logging.error(
                        "Directory '%s' has no images",
                        self.__image_dir)
                    break
            if image_path:
                break
        time.sleep(_DELAY)
        return self.__get_response_from_path(image_path)

    def GetStream(self, request, context):
        directory_iter = self.__get_directory_images_iter()
        for image_path in directory_iter:
            response = self.__get_response_from_path(image_path)
            yield response
            time.sleep(_DELAY)

    def __get_directory_images_iter(self):
        directory_iter = filter(
            lambda x: x.is_file() and x.suffix in {'.jpg', '.png'},
            self.__image_dir.iterdir())
        return directory_iter

    @staticmethod
    def __get_response_from_path(image_path):
        with open(image_path, 'rb') as fp:
            image_bytes = fp.read()
            response = source.Image(data=image_bytes)
        return response
