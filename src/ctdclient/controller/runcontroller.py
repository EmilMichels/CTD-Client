from pathlib import Path

from ctdclient.controller.Controller import Controller
from ctdclient.model.bottles import BottleClosingDepths
from ctdclient.model.dshipcaller import retrieve_station_and_event_info
from ctdclient.model.fileupdater import UpdateFiles
from ctdclient.model.processing import ProcessingList
from ctdclient.model.runseasave import RunSeasave
from ctdclient.view.measurement import MeasurementView
from ctdclient.view.runframe import RunFrame


class RunController(Controller):
    def __init__(
        self,
        *args,
        bottles: BottleClosingDepths,
        processing: ProcessingList,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.view: RunFrame
        self.variables: MeasurementView = self.view.master  # pyright: ignore
        self.bottles = bottles
        self.processing = processing
        # set exe path in view
        self.view.path_to_seasave = self.configuration.path_to_seasave
        # define variables
        self.output_dir = self.configuration.output_directory
        self.last_filename = self.variables.last_filename
        self.current_filename: Path
        self.cast_number = self.variables.cast_number
        self.platform = self.variables.platform
        self.operator = self.variables.operator
        self.station = self.variables.station
        self.dship_values = self.variables.dship_frame.dship_values
        self.bottle_values = self.variables.bottle_frame.bottle_values
        # set callback methods
        self.view.add_callback("runseasave", self.run_seasave)
        self.view.add_callback("postruncheck", self.check_correct_filename)
        self.view.add_callback("runprocessing", self.run_processing)
        self.view.add_callback("cancelprocessing", self.cancel_processing)
        self.view.add_callback("checksamename", self.check_last_filename)

    def check_last_filename(self, current_filename: str):
        return (
            current_filename == self.configuration.last_filename.name
        ) and Path(self.configuration.last_filename).exists()

    def run_seasave(
        self,
        file_name: str,
        downcast: bool = True,
        autostart: bool = False,
    ):
        self.current_filename = self.output_dir.joinpath(file_name)
        self.output_dir = self.configuration.output_directory
        self.bottles.check_bottle_data(
            {key: value.get() for key, value in self.bottle_values.items()}
        )
        return RunSeasave()(
            self.current_filename,
            self.bottles,
            self.platform,
            self.cast_number.get(),
            self.operator.get(),
            self.station.get(),
            self.dship_values["Water_Depth"],
            downcast,
            autostart,
        )

    def update_variables_post_run(self):
        self.configuration.last_platform = self.platform
        if self.current_filename.exists():
            self.last_filename.set(str(self.current_filename.name))
            self.configuration.last_cast = int(self.cast_number.get())
            self.cast_number.set(str(int(self.cast_number.get()) + 1))
            self.configuration.last_filename = Path(self.current_filename)
            self.configuration.operators["last"] = self.operator.get()
            self.configuration.write()

    def check_correct_filename(self):
        self.update_variables_post_run()
        if self.configuration.processing["auto_process"]:
            self.processing.run(self.configuration.last_filename)
        if str(self.current_filename).split("-")[0].endswith("000"):
            self.update_file_information()

    def update_file_information(self):
        station_and_event_info = retrieve_station_and_event_info()
        if station_and_event_info:
            UpdateFiles(
                self.last_filename.get(),
                self.output_dir,
                station_and_event_info,
            )

    def run_processing(self, target_file: str):
        self.processing.run(target_file)

    def cancel_processing(self):
        self.processing.cancel()
