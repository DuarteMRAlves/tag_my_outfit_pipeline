import argparse
import grpc
import pathlib
import visualization_pb2 as vis
import visualization_pb2_grpc as vis_grpc
import time


def parse_args():
    parser = argparse.ArgumentParser(
        description='Test for Web Visualization Service '
                    'for the Tag My Outfit Pipeline')
    parser.add_argument(
        '--target',
        default='localhost:50051',
        help='Location where the server to test is listening')
    parser.add_argument(
        '--delay',
        type=int,
        default=1,
        help='Delay between images in seconds')
    parser.add_argument(
        'images',
        help='Path to the images folder to use')
    return parser.parse_args()


def images_paths_generator(images_dir):
    return filter(
        lambda x: x.is_file() and x.suffix in {'.jpg', '.png'},
        images_dir.iterdir())


def build_category(img_idx):
    return vis.Correspondence(
        label=f'Category-{img_idx}',
        value=img_idx)


def build_attribute(img_idx):
    return vis.Correspondence(
        label=f'Attribute-{img_idx}',
        value=img_idx)


def send_image(stub, img_idx, img_path):
    with open(img_path, 'rb') as fp:
        image_bytes = fp.read()
    predict_request = vis.PredictRequest(image_data=image_bytes)
    predict_response = vis.PredictResponse(
        categories=[build_category(img_idx)],
        attributes=[build_attribute(img_idx), build_attribute(img_idx + 10)]
    )
    request = vis.VisualizationRequest(
        predict_request=predict_request,
        predict_response=predict_response
    )
    stub.Visualize(request)


def send_images(channel, images_dir, delay):
    stub = vis_grpc.VisualizationServiceStub(channel)
    path = pathlib.Path(images_dir)
    for img_idx, img_path in enumerate(images_paths_generator(path)):
        send_image(stub, img_idx, img_path)
        time.sleep(delay)


def main():
    args = parse_args()
    target = args.target
    images_dir = args.images
    delay = args.delay
    with grpc.insecure_channel(target) as channel:
        send_images(channel, images_dir, delay)


if __name__ == '__main__':
    main()
