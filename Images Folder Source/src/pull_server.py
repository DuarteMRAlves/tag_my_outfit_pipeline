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
            directory_iter = filter(
                    lambda x: x.is_file() and x.suffix in {'.jpg', '.png'},
                    self.__image_dir.iterdir())
            while not image_path:
                try:
                    image_path = next(directory_iter, None)
                except StopIteration:
                    print("Directory has no images")
                    break
            if image_path:
                break
        time.sleep(1)
        with open(image_path, 'rb') as fp:
            image_bytes = fp.read()
            response = image.Image(bytes=image_bytes,
                                   format=''.join(image_path.suffixes),
                                   name=image_path.stem)

        return response
