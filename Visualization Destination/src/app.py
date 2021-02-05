import flask as fl
import queue
import logging
import threading
import visualization_service


class DiscardingQueue:

    def __init__(self):
        self.__queue = queue.Queue()
        self.__discarding = True

    def get(self):
        return self.__queue.get()

    def put(self, el):
        if not self.__discarding:
            self.__queue.put(el)

    def start_discarding(self):
        logging.info('Started discarding messages')
        self.__discarding = True
        try:
            while True:
                self.__queue.get_nowait()
        except queue.Empty:
            pass

    def stop_discarding(self):
        logging.info('Stopped discarding messages')
        self.__discarding = False


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
            image_bytes = results_queue.get()
            frame = b''.join(
                (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n',
                 image_bytes,
                 b'\r\n'))
            yield frame
    except GeneratorExit:
        logging.info('Client closed stream')
        results_queue.start_discarding()


def create_app():
    logging.basicConfig(level=logging.INFO)
    flask_app = fl.Flask(__name__)
    results_queue = DiscardingQueue()
    threading.Thread(
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
