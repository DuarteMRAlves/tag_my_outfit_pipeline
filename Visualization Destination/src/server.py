import concurrent.futures as futures
import grpc
import grpc_reflection.v1alpha.reflection as grpc_reflect
import io
import logging
import multiprocessing as mult_proc
import sys
import tkinter as tk
import threading
import visualization_pb2 as vis
import visualization_pb2_grpc as vis_grpc
import PIL.Image as PIT_img
import PIL.ImageTk as PIL_img_tk

_MAX_WORKERS = 10
_SERVICE_NAME = 'VisualizationService'


class VisualizationServiceImpl(vis_grpc.VisualizationServiceServicer):

    def __init__(self, results_queue: mult_proc.Queue):
        self.__results_queue = results_queue

    def Visualize(self, request: vis.VisualizationRequest, context):
        self.__results_queue.put(request)
        return vis.Empty()


class ResultsVisualizationHandler:

    __LABEL_FONT = ("Helvetica", 20)
    __TEXT_FONT = ("Helvetica", 16)

    def __init__(self, results_queue: 'mult_proc.Queue'):
        window = tk.Tk()

        window.title('Results Visualization')

        # Display input image
        image_frame = tk.Frame(master=window, width=800)
        output_frame = tk.Frame(master=window, width=200, bg='blue')

        lbl_image = tk.Label(master=image_frame, text='Input Image', height=2, font=self.__LABEL_FONT)
        lbl_image.pack()
        image_canvas = tk.Canvas(master=image_frame, width=400, height=600)
        image_canvas.pack(fill=tk.BOTH, expand=True)
        image_canvas.bind("<Configure>", self.__resize_canvas)

        # Display model output
        lbl_category = tk.Label(master=output_frame, text='Predicted Category', height=2, font=self.__LABEL_FONT)
        lbl_category.pack(fill=tk.X)

        txt_category = tk.Text(master=output_frame, width=20, height=2, font=self.__TEXT_FONT)
        txt_category.bind("<Key>", lambda a: "break")
        txt_category.pack(fill=tk.X)

        lbl_attributes = tk.Label(master=output_frame, text='Predicted Attributes', height=2, width=20, font=self.__LABEL_FONT)
        lbl_attributes.pack(fill=tk.X)

        txt_attributes = tk.Text(master=output_frame, width=20, height=5, font=self.__TEXT_FONT)
        txt_category.bind("<Key>", lambda a: "break")
        txt_attributes.pack(fill=tk.X)

        empty_frame = tk.Frame(master=output_frame)
        empty_frame.pack(fill=tk.BOTH, expand=True)

        image_frame.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)
        output_frame.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

        self.__window = window
        self.__image_canvas = image_canvas
        self.__txt_category = txt_category
        self.__txt_attributes = txt_attributes
        self.__pil_image = None
        self.__tk_image = None
        self.__results_queue = results_queue

    def __update_image(self):
        canvas_size = (self.__image_canvas.winfo_width(), self.__image_canvas.winfo_height())
        image_size = self.__pil_image.size
        canvas_ratio = canvas_size[0] / canvas_size[1]
        image_ratio = image_size[0] / image_size[1]
        if canvas_ratio > image_ratio:
            # Resize by height
            final_height = canvas_size[1]
            final_width = int(final_height * image_ratio)
        else:
            # Resize by width
            final_width = canvas_size[0]
            final_height = int(final_width / image_ratio)

        resized_image = self.__pil_image.resize((final_width, final_height), PIT_img.ANTIALIAS)
        self.__tk_image = PIL_img_tk.PhotoImage(resized_image)
        self.__image_canvas.create_image(canvas_size[0] // 2,  # Center in canvas
                                         final_height // 2,  # Image always touches top
                                         anchor=tk.CENTER,
                                         image=self.__tk_image)

    def __update_canvas(self):
        while True:
            result = self.__results_queue.get()
            if not result:
                break

            predict_response = result.predict_response
            self.__txt_category.delete('1.0', tk.END)
            self.__txt_category.insert('1.0', '\n'.join(
                [f'{cat.label}, {"{:.3f}".format(cat.value)}'
                 for cat in predict_response.categories]))

            self.__txt_attributes.delete('1.0', tk.END)
            self.__txt_attributes.insert('1.0', '\n'.join(
                [f'{attr.label}, {"{:.3f}".format(attr.value)}'
                 for attr in predict_response.attributes]))

            predict_request = result.predict_request
            self.__pil_image = PIT_img.open(io.BytesIO(predict_request.image_data))
            self.__update_image()

    def __resize_canvas(self, event):
        if self.__pil_image:
            self.__update_image()

    def run(self):
        update_canvas_thread = threading.Thread(target=self.__update_canvas)
        update_canvas_thread.start()

        self.__window.mainloop()
        self.__results_queue.put(None)
        update_canvas_thread.join()


def visualize_results(results_queue: mult_proc.Queue):
    """
    Function to display received results using tkinter
    :param results_queue: queue with the received images and classifications
    :return:
    """
    ResultsVisualizationHandler(results_queue).run()


def parse_argv():
    argv = sys.argv
    if len(argv) != 2:
        print(f'Invalid number of arguments: 1 expected but received {len(argv) - 1}')
        exit(1)
    return int(argv[1])


def main():
    port = parse_argv()
    results_queue = mult_proc.Queue()
    visualization_process = mult_proc.Process(target=visualize_results, args=(results_queue,))
    visualization_process.start()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=_MAX_WORKERS))
    vis_grpc.add_VisualizationServiceServicer_to_server(
        VisualizationServiceImpl(results_queue), server)
    SERVICE_NAME = (
        vis.DESCRIPTOR.services_by_name[_SERVICE_NAME].full_name,
        grpc_reflect.SERVICE_NAME
    )
    grpc_reflect.enable_server_reflection(SERVICE_NAME, server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    visualization_process.join()


if __name__ == '__main__':
    logging.basicConfig()
    main()
