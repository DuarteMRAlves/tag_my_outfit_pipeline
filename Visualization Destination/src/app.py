import flask as fl
import logging
import multiprocessing
import visualization_service
import queue


class DiscardingQueue:

    def __init__(self):
        self.__queue = multiprocessing.Queue()
        self.__discarding = multiprocessing.Value('b', True)

    def get(self):
        return self.__queue.get()

    def put(self, el):
        logging.info('Discarding: %s', self.__discarding.value)
        if not self.__discarding.value:
            self.__queue.put(el)

    def start_discarding(self):
        logging.info('Started discarding messages')
        self.__discarding.value = True
        try:
            while True:
                self.__queue.get_nowait()
        except queue.Empty:
            pass

    def stop_discarding(self):
        logging.info('Stopped discarding messages')
        self.__discarding.value = False


def run_grpc_server(results_queue):
    """Start the gRPC Visualization Service and blocks"""
    visualization_service.run_server(results_queue)


def generate_feed(results_queue):
    """
    Generates a feed of frames that
    results in the multipart message

    Yields:
        byte stream with the frames
    """
    try:
        logging.info('Received connection')
        results_queue.stop_discarding()
        while True:
            request = results_queue.get()
            image = request.predict_request.image_data
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + image + b'\r\n')
    except GeneratorExit:
        logging.info('Client closed stream')
        results_queue.start_discarding()


def create_app():
    logging.basicConfig(level=logging.INFO)
    flask_app = fl.Flask(__name__)
    results_queue = DiscardingQueue()
    multiprocessing.Process(
        target=run_grpc_server,
        args=(results_queue,)).start()

    @flask_app.route('/')
    def index():
        """Video Streaming home page

        :return: the html to render the homepage
        """
        return fl.render_template('index.html')

    @flask_app.route('/video_feed')
    def video_feed():
        """ Route for the video feed

        :return: Http multipart response with generator
                 creating frames as they arrive
        """
        logging.info('Received video feed')
        return fl.Response(
            generate_feed(results_queue),
            mimetype='multipart/x-mixed-replace; boundary=frame')

    return flask_app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', threaded=True)
