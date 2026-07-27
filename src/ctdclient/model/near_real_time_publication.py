from __future__ import annotations

import logging
import mimetypes
import multiprocessing as mp
import os
import platform
import re
import shutil
import smtplib
import subprocess
import time
from abc import abstractmethod
from collections import UserList
from datetime import date, datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Callable

from ctdam.parser import DataFile
from platformdirs import user_log_dir
from tomlkit.toml_file import TOMLFile

from ctdclient.definitions import (
    CONFIG_PATH,
    TEMPLATE_PATH,
    config,
    cruise_head,
    cruise_name,
    event_manager,
)

logger = logging.getLogger(__name__)


def instantiate_near_real_time_target(
    *args,
    frequency_of_action: str = "23:59:00",
    **kwargs,
) -> NearRealTimeTarget:
    """
    Differentiate the two NRT modes and instantiates respecive classes.

    Parameters
    ----------
    *args :
        Are given to NRT classes
    frequency_of_action: str
        The information to distinguish the two NRT modes
    **kwargs :
        Are given to NRT classes

    Returns
    -------
    A fresh NearRealTimeTarget instance.
    """
    if ":" in frequency_of_action:
        class_to_instantiate = DailyPublication
        kwargs["time_to_run_at"] = frequency_of_action
    elif frequency_of_action == "each_processing":
        class_to_instantiate = EachProcessingPublication
    else:
        raise AttributeError(
            f"Unknown frequency for near-real-time publication: {frequency_of_action}"
        )
    return class_to_instantiate(*args, **kwargs)


class NRTList(UserList):
    """A collection of NearRealTimeTargets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = []

    def update_nrt_data(self, clear_data: bool = True):
        """
        Fills collection with NRT instances.

        Parameters
        ----------
        clear_data: bool :
            Whether to reset previous data when updating
        """
        if clear_data:
            self.kill_processes()
            self.data = []
        for path in CONFIG_PATH.glob("nrt_*.toml"):
            try:
                self.data.append(self.create_nrt_instance(path))
            except Exception as error:
                logger.error(
                    f"Could not instantiate nrt, using {path}: {error}"
                )
                continue

    def create_nrt_instance(self, path: Path):
        """
        Get new instance of NearRealTimeTarget.

        Parameters
        ----------
        path: Path
            File path to toml config file

        Returns
        -------
        NearRealTimeTarget instance.
        """
        toml_file = TOMLFile(path).read()
        name = path.stem[4:]
        active = (
            config.near_real_time[name]
            if name in config.near_real_time
            else False
        )
        return instantiate_near_real_time_target(
            **toml_file,
            file_path=path,
            active=active,
        )

    def get_template(
        self, template_path: Path = TEMPLATE_PATH.joinpath("nrt_template.toml")
    ):
        """
        Create template NearRealTimeTarget instance.

        Parameters
        ----------
        template_path: Path :
            File path to template file config

        Returns
        -------
        NearRealTimeTarget instance.
        """
        if not template_path.exists():
            return None
        template = self.create_nrt_instance(template_path)
        self.data.append(template)
        return template

    def toggle_activity(self, nrt: NearRealTimeTarget):
        """
        Toggle whether a particluar NearRealTimeTarget is active or not.

        Parameters
        ----------
        nrt: NearRealTimeTarget
            The target instance to toggle
        """
        if nrt in self.data:
            nrt.toggle_activity()

    def kill_processes(self):
        """Kills a running NearRealTimeTarget action."""
        for nrt in self.data:
            nrt.stop()

    def delete_nrt(self, nrt: NearRealTimeTarget):
        """
        Removes a NearRealTimeTarget from the collection.

        Parameters
        ----------
        nrt: NearRealTimeTarget
            The instance to remove
        """
        self.data.remove(nrt)
        if isinstance(nrt, DailyPublication):
            nrt.stop()
        if nrt.file_path.exists():
            nrt.file_path.unlink()
        try:
            config.near_real_time.pop(nrt.name)
        except KeyError:
            pass
        else:
            config.write()


class NearRealTimeTarget:
    """
    Stores information for near-real-time distribution of latest CTD data files.
    Can work in two modes: email or rsync/copy. Will distinguish between these
    by checking 'recipient_adress' for an '@'.

    Parameters
    ----------
    recipient_address: str
        Target of the action, email address or file path
    target_file_suffix: str
        File suffix to select target files with
    target_file_directory: Path | str
        The directory to look for target files
    geo_filter: str
        A geographic location to filter target files with
    email_info: dict
        Collection of email information
    file_path: Path | str
        File path to config file
    active: bool
        Whether the NRT job is active
    """

    def __init__(
        self,
        recipient_address: str,
        target_file_suffix: str,
        target_file_directory: Path | str = "",
        geo_filter: str = "",
        email_info: dict = {},
        file_path: Path | str = "",
        active: bool = False,
        **kwargs,
    ):
        self.address = recipient_address
        self.dir = Path(target_file_directory)
        self.suffix = target_file_suffix
        self.geo_filter = geo_filter
        self.email_info = email_info
        self.file_path = Path(file_path)
        self.name = self.file_path.stem[4:]
        self.files_already_sent = []
        self.active = active

    @abstractmethod
    def toggle_activity(self):
        """Toggles the NRT activity."""
        pass

    def _is_email(self, target: str = "") -> bool:
        """
        Basic check, whether we are dealing with email or not.

        Parameters
        ----------
        target: str
            The target info to distinguish

        Returns
        -------
        Whether sending email or copying files.
        """
        target = str(self.address) if len(target) == 0 else target
        return "@" in target

    @abstractmethod
    def run(self):
        """Will move the recent files to the target location."""

    def create_email_message(
        self,
        target_files: list[Path],
        to_address: str = "",
        from_address: str = "",
        subject: str = "",
        body: str = "",
    ):
        """
        Creates an email with target files attached.

        Parameters
        ----------
        target_files: list[Path]
            Target files to attach
        to_address: str
            Email address to send to
        from_address: str
            Email address to send from
        subject: str :
            Email subject line
        body: str :
            Email text

        Returns
        -------
        Assembled email message.
        """
        to_address = self.address if to_address == "" else to_address
        smtp_email = self.email_info["smtp_email"]
        if smtp_email.startswith("$"):
            smtp_email = os.getenv(smtp_email[1:])
        if not smtp_email:
            smtp_email = "Anonymous"
        from_address = smtp_email if from_address == "" else from_address
        subject = self.email_info["subject"] if subject == "" else subject
        body = self.email_info["body"] if body == "" else body
        timestamp = datetime.now(tz=timezone.utc).strftime("%y-%m-%d %H:%M:%S")
        msg = EmailMessage()
        msg.set_content(
            body.format(
                cruise_name=cruise_name,
                date=timestamp,
                cruise_head=cruise_head,
            )
        )

        msg["Subject"] = subject.format(
            cruise_name=cruise_name,
            date=timestamp,
        )
        msg["From"] = from_address
        msg["To"] = to_address

        for file in target_files:
            # for some reason, one cannot attach files without specifying a
            # mime type
            mime_type, _ = mimetypes.guess_type(file)
            if mime_type is None:
                mime_type = "application/octet-stream"
            main_type, sub_type = mime_type.split("/", 1)
            with open(file, "rb") as data:
                msg.add_attachment(
                    data.read(),
                    maintype=main_type,
                    subtype=sub_type,
                    filename=file.name,
                )
        return msg

    def create_email_draft(
        self,
        msg: EmailMessage,
        file_path: Path | str = "",
    ) -> Path:
        """
        Creates an email .eml draft file, that can be opened by common email
        programs.

        Parameters
        ----------
        msg: EmailMessage
            Assembled email message ready for sending
        file_path: Path | str
            File path to save .eml draft file to

        Returns
        -------
        File path .eml draft has been saved to.
        """
        draft_dir = Path(user_log_dir("ctdclient")).parent.joinpath("emails")
        if not draft_dir.exists():
            draft_dir.mkdir(parents=True, exist_ok=True)
        msg.add_header("X-Unsent", "1")
        file_path = (
            draft_dir.joinpath(rf"{str(datetime.now()).replace(' ', 'T')}.eml")
            if file_path == ""
            else Path(file_path)
        )
        with open(file_path, "w") as f:
            f.write(msg.as_string())
        return file_path

    def open_draft_msg(self, file_path: Path | str):
        """
        Open an .eml file using the default email program.

        Parameters
        ----------
        file_path: Path | str
            File path to .eml file
        """
        if platform.system() == "Windows":
            os.startfile(file_path)
        elif platform.system() == "Darwin":
            subprocess.run(["open", file_path])
        elif platform.system() == "Linux":
            subprocess.run(["xdg-open", file_path])
        else:
            raise OSError("Unsupported operating system")

    def run_email_logic(
        self,
        files_to_attach: list,
        run_manually: bool = False,
    ):
        """
        Master method to coordinate email assembly and sending.

        Parameters
        ----------
        files_to_attach: list
            List of target files to attach to email
        run_manually: bool
            Whether to automatically send email or open draft message for editing
        """
        if not run_manually and len(files_to_attach) == 0:
            logger.info(
                "Automatic email not sent because no files are available."
            )
            return
        email_message = self.create_email_message(files_to_attach)
        open_draft = True if self.email_info["open_draft"] == "true" else False
        draft_path = self.create_email_draft(email_message)
        if run_manually or open_draft:
            self.open_draft_msg(draft_path)
        else:
            self.send_email(email_message)

    def send_email(self, msg: EmailMessage):
        """
        Sends the email message using the given smtp server configuration.

        Parameters
        ----------
        msg: EmailMessage
            Assembled email message to send
        """
        try:
            smtp_server = self.email_info["smtp_server"]
            smtp_port = self.email_info["smtp_port"]
            assert len(smtp_server) and len(str(smtp_port))
        except (KeyError, AssertionError):
            logger.error(
                "Could not send email, because of missing smtp server and/or port information."
            )
            return
        assert isinstance(msg, EmailMessage)
        with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
            server.starttls()
            try:
                server.send_message(msg)
            except smtplib.SMTPRecipientsRefused as error:
                logger.error(f"Credentials needed to send email: {error}")
            else:
                logger.info(f"Email sent to {msg['To']}")

    def copy_files(self, target_file: Path):
        """
        Copies target files to given location.

        Parameters
        ----------
        target_file: Path
            The target file to copy
        """
        target_dir = Path(self.address)
        if not target_dir.exists():
            target_dir.mkdir(parents=True)
        source_dir = target_file.parent
        file_name = target_file.stem
        for file in source_dir.glob(f"{file_name}{self.suffix}*"):
            shutil.copy(file, target_dir)
            logger.info(f"Copied {file} to {target_dir}")

    def get_target_files(self, target_file: Path = Path(".")) -> list[Path]:
        """
        Creates a list of paths to files that are meant to be published.

        Parameters
        ----------
        target_file: Path
            File path to target file

        Returns
        -------
        List of target files that passed geo and time filter and have not been published previously.
        """
        file_name = "" if target_file == Path(".") else str(target_file.stem)
        target_files = []
        for file in self.dir.glob(f"*{file_name}{self.suffix}*"):
            # check, whether file already sent
            if (
                (file in self.files_already_sent)
                or (file.is_dir())
                or (file.name.startswith("."))
            ):
                continue
            if len(self.geo_filter) > 0:
                try:
                    file_metadata = DataFile(
                        path_to_file=file,
                        only_header=True,
                    )
                except PermissionError as error:
                    message = (
                        f"Insufficient permissions to read {file}: {error}"
                    )
                    logger.error(message)
                else:
                    try:
                        coordinates = file_metadata.start_position
                    except (KeyError, ValueError):
                        coordinates = (0, 0)
                    if not self.geographic_filter(coordinates):
                        logger.debug(
                            f"File {file} failed geographic filter with coordinates: {coordinates}"
                        )
                        continue

            target_files.append(file)
        self.files_already_sent = [*self.files_already_sent, *target_files]
        return target_files

    def deg_min_to_deg_decimal(self, value: str) -> float:
        """
        Converts coordinates from deg minutes to decimal degrees.

        Parameters
        ----------
        value: str
            Coordinate information

        Returns
        -------
        Decimal degree float.
        """
        deg, minutes, direction = re.split(r"\s+", value)
        return (float(deg) + float(minutes) / 60) * (
            -1 if direction in ["W", "S"] else 1
        )

    def geographic_filter(self, coordinate_pair: tuple) -> bool:
        """
        Checks, whether we are inside of a certain polygon.

        The polygon will usually be the EEZ of a certain country. Does support
        all data formats that geopandas can handle.

        Parameters
        ----------
        coordinate_pair: tuple
            Coordinates of the target file

        Returns
        -------
        Whether inside target area or not.
        """
        available_filters = {
            "germany": [
                (54.0, 10.3),
                (54.0, 14.4),
                (55.1, 14.4),
                (55.1, 10.3),
                (54.0, 10.3),
            ]
        }
        try:
            polygon = available_filters[self.geo_filter]
        except KeyError:
            return False
        # if no polygon is given, no geo filter can be applied and thus, we
        # just return true and skip the rest of the method
        if len(polygon) == 0:
            return True
        return self.point_in_polygon(coordinate_pair, polygon)

    def point_in_polygon(self, point, polygon):
        """
        Check if a point is inside a polygon using the Ray Casting Algorithm.

        Parameters
        ----------
        point :
            Tuple (x, y) representing the point to check.
        polygon :
            List of tuples [(x1, y1), (x2, y2), ...] representing the polygon vertices.

        Returns
        -------
        True if the point is inside the polygon, False otherwise.
        """
        x, y = point
        n = len(polygon)
        inside = False

        p1x, p1y = polygon[0]
        for i in range(n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (
                                p2y - p1y
                            ) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = True
            p1x, p1y = p2x, p2y

        return inside


class DailyPublication(NearRealTimeTarget):
    """
    Automatic publication once a day.

    Parameters
    ----------
    time_to_run_at: str
        The time point to publish
    single_run: bool
        Whether to run once or infinitely
    """

    def __init__(
        self,
        *args,
        time_to_run_at: str = "23:59:30",
        single_run: bool = False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.single_run = single_run
        try:
            self.time_to_run_at = datetime.strptime(time_to_run_at, "%H:%M:%S")
        except ValueError:
            logger.error(f"Could not parse the given time: {time_to_run_at}")
        if self.active:
            self.start()

    def time_filter(self, file: Path) -> bool:
        """
        Ensure, that file has been modified in the last 24 hours.

        Parameters
        ----------
        file: Path
            Target file to check

        Returns
        -------
        Whether recently modified or not.
        """
        last_twenty_four_hours = datetime.now() + timedelta(days=-1)
        file_modification_time = datetime.fromtimestamp(file.stat().st_mtime)
        return datetime.now() > file_modification_time > last_twenty_four_hours

    def action(self):
        """Multiprocessing target method that run publication logic."""
        list_to_process = [
            f for f in self.get_target_files() if self.time_filter(f)
        ]
        if self._is_email():
            self.run_email_logic(list_to_process)
        else:
            for file in list_to_process:
                self.copy_files(file)

    def start(self):
        """Activates multiprocessing process to repeatedly publish."""
        self.process = mp.Process(
            target=timer,
            args=[self.time_to_run_at, self.action, self.single_run],
        )
        self.process.start()

    def stop(self):
        """Stops multiprocessing process."""
        try:
            self.process.terminate()
            self.process.join(timeout=2)
        except AttributeError:
            pass

    def toggle_activity(self):
        """Sets activity on or off."""
        self.active = not self.active
        if self.active:
            self.start()
        else:
            self.stop()


def timer(time_to_run_at: datetime, function: Callable, single_run: bool):
    """
    Timer to next publication moment.

    Parameters
    ----------
    time_to_run_at: datetime
        Next target time
    function: Callable
        Action to perform on publication time
    single_run: bool
        Whether to run only once
    """

    def calculate_delay():
        """ """
        now = datetime.now()
        target_time = datetime.combine(date.today(), time_to_run_at.time())
        if now > target_time:
            # move target time to the next day
            target_time += timedelta(days=1)
        delay = (target_time - now).total_seconds()
        return delay

    time_left = calculate_delay()
    while True:
        time.sleep(1)
        time_left -= 1
        if time_left <= 0:
            function()
            if single_run:
                break
            time_left = calculate_delay()


class EachProcessingPublication(NearRealTimeTarget):
    """Automatic publication every processing."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.active:
            event_manager.subscribe("processing_successful", self.run)
        self.address = Path(self.address)

    def toggle_activity(self):
        """Sets activity on or off."""
        self.active = not self.active
        if self.active:
            event_manager.subscribe("processing_successful", self.run)
        else:
            event_manager.unsubscribe("processing_successful", self.run)

    def run(self, target: Path = Path(".")):
        """
        The action to perform after processing.

        Parameters
        ----------
        target: Path
            The file path to retrieve target files from
        """
        target_files = self.get_target_files(target)
        if self._is_email():
            self.run_email_logic(target_files)
        else:
            self.copy_files(target)

    def stop(self):
        """Stops automatic publication."""
        try:
            event_manager.unsubscribe("processing_successful", self.run)
        except (NameError, AttributeError):
            pass
