import pathlib
import pipeline.core.connections.grpc.sources_pb2_grpc as sources_grpc
import pipeline.core.messages.grpc.image_pb2 as image
import time


_DELAY = 1


class PullServer(sources_grpc.ImageDataSourceServicer):

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
                    print("Directory has no images")
                    break
            if image_path:
                break
        time.sleep(1)
        return self.__get_response_from_path(image_path)

    def GetStream(self, request, context):
        directory_iter = self.__get_directory_images_iter()
        for image_path in directory_iter:
            response = self.__get_response_from_path(image_path)
            yield response
            time.sleep(0.2)

    def __get_directory_images_iter(self):
        directory_iter = filter(
            lambda x: x.is_file() and x.suffix in {'.jpg', '.png'},
            self.__image_dir.iterdir())
        return directory_iter

    @staticmethod
    def __get_response_from_path(image_path):
        with open(image_path, 'rb') as fp:
            image_bytes = fp.read()
            response = image.Image(bytes=image_bytes,
                                   format=''.join(image_path.suffixes),
                                   name=image_path.stem)
        return response


