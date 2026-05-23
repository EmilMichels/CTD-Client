import tkinter as tk
from multiprocessing import Queue

import customtkinter as ctk

from ctdclient.view.ctkframe import CtkFrame
from ctdclient.view.View import ViewMixin


class DshipFrame(ViewMixin, CtkFrame):
    """
    Frame that displays our metadata header information with live-fetched
    DSHIP data. Additionally features a selection field for the current
    operators name, as this is the only header information that can not be
    retrieved from DSHIP.

    Parameters
    ----------
    window :


    Returns
    -------

    """

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.set_border()

    def initialize(self, dship_values: dict, queue: Queue):
        self.queue = queue
        self.dship_vars = {
            key: tk.StringVar(value=value)
            for key, value in dship_values.items()
        }
        self.dship_values = {}
        self.dship_label = ctk.CTkLabel(self, text="waiting for connection...")
        self.dship_label.grid(row=0, column=1)
        self.debug = self.configuration.debugging

        hidden_elements = ("Cruise", "Device") if not self.debug else ()
        for index, (key, value) in enumerate(self.dship_vars.items()):
            if key not in hidden_elements:
                ctk.CTkLabel(self, text=key.replace("_", " ")).grid(
                    row=index + 1,
                    column=0,
                    sticky="w",
                    padx=self.padx,
                )
                ctk.CTkLabel(self, textvariable=value).grid(
                    row=index + 1,
                    column=1,
                    sticky="w",
                    padx=self.padx,
                )
        self.update_dship_values()

    def update_dship_values(self):
        """

        Parameters
        ----------
        list_of_values :


        Returns
        -------

        """

        try:
            while not self.queue.empty():
                data = self.queue.get()
                # TODO: handle reconnecting and error display
                if "error" in data:
                    self.set_dship_status_bad()
                else:
                    self.set_dship_status_good()
                    for (key, var), value in zip(
                        self.dship_vars.items(), data.values()
                    ):
                        self.dship_values[key] = value
                        var.set(value)
        except Exception as error:
            self.set_dship_status_bad(str(error))
        self.after(1000, self.update_dship_values)

    def set_dship_status_good(self):
        """"""
        self.dship_label.configure(text_color="green", text="DSHIP live")

    def set_dship_status_bad(self, text: str = "not connected"):
        """"""
        self.dship_label.configure(text_color="red", text=text)
