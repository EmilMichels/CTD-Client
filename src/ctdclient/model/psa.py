import logging
import math
from pathlib import Path

from ctdam.parser import PsaFile

logger = logging.getLogger(__name__)


class SeasavePsa(PsaFile):
    """
    Python-internal representation of the Seasave.psa that allows targeted
    modifications of individual xml parts inside the file.

    Specifically, this class has methods to edit:
    - the custom metadata header, that SeaBird has given the ** prefix
    - the pre-set depths at which specific bottles are meant to be closed
    - the xmlcon and new hex paths

    Parameters
    ----------
    path_to_file: Path | file
        File path to seasave psa
    """

    def __init__(self, path_to_file: Path | str):
        super().__init__(path_to_file)
        self.settings_part = self.data["SeasaveProgramSetup"]["Settings"]

    def set_metadata_header(self, metadata_list, header_prompt: bool = False):
        """
        Creates metadata entries from a list of pre-formated metadata points.

        The list is expected to look like this:
        ['key0 = value0', 'key1 = value1', ...]
        and will produce header entries that SeaSave understands and will
        prefix with '** '.

        Additionally, the 'HeaderChoice' can be configured by usage of the
        'header_prompt' parameter. It supports two values, 1, which will prompt
        the user the currently set metadata header for confirmation. And 2,
        which is calles 'autostart' in this software, as it will start data
        aquisition upon opening SeaSave. The value 2 skips any confirmation
        concerning the metadata header and will just use it to produce .hex
        and .hdr files.

        Parameters
        ----------
        metadata_list : str
            A list of metadata points to include in the header.
        header_prompt : bool
            Whether to prompt for confirmation on the metadata header.
        """
        headerform = self.settings_part["HeaderForm"]
        header_dict = {}
        if header_prompt:
            header_choice = "2"
        else:
            header_choice = "1"
        header_dict["@HeaderChoice"] = header_choice
        prompt = []
        for index, value in enumerate(metadata_list):
            prompt_element = {}
            prompt_element["@index"] = str(index)
            prompt_element["@value"] = self.map_umlauts_for_seasave(value)
            prompt.append(prompt_element)
        header_dict["Prompt"] = prompt
        headerform = header_dict
        self.data["SeasaveProgramSetup"]["Settings"]["HeaderForm"] = headerform

    def map_umlauts_for_seasave(self, header_line: str) -> str:
        """
        Basic mapping of all german umlauts to ascii compatible replacements.
        SeaSave can not handle non-ascii symbols inside of the .psa files.

        Parameters
        ----------
        header_line : str
            The metadata header line to 'sanitize'.

        Returns
        -------
        A umlaut-free string.
        """
        return (
            header_line.replace("ä", "ae")
            .replace("ö", "oe")
            .replace("ü", "ue")
            .replace("ß", "ss")
            .replace("Ä", "Ae")
            .replace("Ö", "Oe")
            .replace("Ü", "Ue")
        )

    def set_bottle_fire_info(
        self,
        bottle_info: dict = {},
        number_of_bottles: int = 13,
    ):
        """
        Handles automatic bottle firing using pre-set depths.

        Takes a dictionary that maps bottle numbers to their specific depth
        values and uses these to produce the format needed inside the .psa so
        that the individual bottle closes at the respective depth. All positive
        numbers are taken as they are, other values (including strings) are
        mapped to 0, which for SeaSave means no autofiring, but will save the
        bottle as 'want to close'. In the bottle firing tab of SeaSave, this
        results in offering the lowest of these bottle numbers as next to close,
        when all autofiring bottles are already closed.

        Sets all other parameters that are needed for this procedure to work to
        the needed values.

        Parameters
        ----------
        bottle_info: dict
            Water bottle information
        number_of_bottles: int
            The number of bottles
        """
        watersampler = self.settings_part["WaterSamplerConfiguration"]
        for row in watersampler["AutoFireData"]["DataTable"]["Row"]:
            # ensure correct/complete mapping of bottle_numbers to indices
            index = int(row["@index"])
            bottle_number = index + 1
            row["@BottleNumber"] = bottle_number
            if bottle_number <= number_of_bottles:
                user_input = bottle_info[bottle_number].replace(",", ".")
                try:
                    row["@FireAt"] = str(float(user_input))
                    assert not row["@FireAt"].startswith("-")
                except (KeyError, ValueError, AssertionError):
                    row["@FireAt"] = "0.0"
                except TypeError:
                    row["@FireAt"] = str(user_input)
        if len(bottle_info) == 0:
            watersampler["AutoFireData"]["@MaxPressureOrDepth"] = "0.000000"
        else:
            watersampler["AutoFireData"]["@MaxPressureOrDepth"] = "1000.000000"
        watersampler["@NumberOfWaterBottles"] = str(number_of_bottles)
        watersampler["@EnableRemoteFiring"] = "0"
        watersampler["AutoFireData"]["@AllowManualFiring"] = "1"
        watersampler["@FiringSequence"] = "3"
        self.data["SeasaveProgramSetup"]["Settings"][
            "WaterSamplerConfiguration"
        ] = watersampler

    def set_xmlcon_file_path(self, xmlcon_path: Path | str):
        """
        Sets the correct XMLCON path.

        Parameters
        ----------
        xmlcon_path: Path | str
            File path to .xmlcon
        """
        self.settings_part["ConfigurationFilePath"]["@value"] = str(
            xmlcon_path
        )

    def set_hex_file_path(self, hex_path: Path | str):
        """
        Sets the correct path to the newly created hex file.

        Parameters
        ----------
        hex_path: Path | str
            File path to .hex
        """
        self.settings_part["DataFilePath"]["@value"] = str(hex_path)

    def adjust_plotting_axis_borders(self, depth_str: str):
        depth = float(depth_str[:-1].strip())
        target_depth = math.ceil(depth / 10) * 10
        logger.debug(f"Depth to set plot axis to: {target_depth}")
        clients = self.data["SeasaveProgramSetup"]["Clients"][
            "DisplaySettings"
        ]["Display"]
        for display in clients:
            if display["@Type"] == "4":
                if display["XYPlotData"]["PlotType"]["@value"] == "0":
                    y_axis = display["XYPlotData"]["Axes"]["Axis"][0]
                    if y_axis["Calc"]["@UnitID"] == "3":
                        y_axis["MaximumValue"]["@value"] = target_depth
                        y_axis["MajorDivisions"]["@value"] = target_depth // 10
