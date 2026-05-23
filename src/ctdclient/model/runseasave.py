import logging
import subprocess
from pathlib import Path

from ctdclient.definitions import config
from ctdclient.model.bottles import BottleClosingDepths
from ctdclient.model.metadataheader import MetadataHeader
from ctdclient.model.psa import SeasavePsa

logger = logging.getLogger(__name__)


class RunSeasave:
    """
    Calls the seasave.exe with the specified command line arguments.
    In preparation for this, the Seasave.psa will be configured with the paths
    to XMLCON and hex file.

    Parameters
    ----------
    current_filename: Path
        The file name of the new file
    bottles: BottleClosingDepths
        The water bottle information
    platform: str
        CTD platform descriptor
    cast: str
        CTD cast number
    operator: str
        The name of the CTD operator
    station: str
        The DSHIP station information
    downcast: bool = True
        Whether to close water bottles on downcast
    autostart: bool = True
        Whether to skip confirmations inside seasave and just run
    """

    def __call__(
        self,
        current_filename: Path,
        bottles: BottleClosingDepths,
        platform: str,
        cast: str,
        operator: str,
        station: str,
        depth: str,
        downcast: bool = True,
        autostart: bool = True,
    ) -> subprocess.Popen | None:
        self.path_to_seasave_exe = config.path_to_seasave
        self.path_to_psa = config.seasave_psa
        # check for an error inside the bottle handling
        if bottles[1] == "ERROR":
            return
        logger.debug(f"Wrote these bottle values to the psa:\n{bottles}")
        if self.update_psa(
            current_filename,
            bottles,
            platform,
            cast,
            operator,
            station,
            depth,
            autostart,
        ):
            return self.run(downcast, autostart)

    def run(self, downcast=True, autostart=True) -> subprocess.Popen:
        """
        Executes the seasave.exe with given command line arguments.

        Parameters
        ----------
        downcast :
            Whether to close water bottles on downcast
        autostart :
            Whether to skip confirmations inside seasave and just run

        Returns
        -------
        A subprocess Popen instance of the seasave process.
        """
        run_command = [
            self.path_to_seasave_exe
        ] + self.set_seasave_command_line_parameters(downcast, autostart)
        try:
            ps = subprocess.Popen(run_command)
            if ps.stdout:
                logger.debug(ps.stdout)
        except subprocess.CalledProcessError as error:
            if error.stderr:
                logger.error(error.stderr)
            raise error
        except PermissionError as error:
            logger.error(
                f"Insufficient permissions to run the command {run_command}: {error}"
            )
            raise error
        else:
            return ps

    def update_psa(
        self,
        current_filename: Path,
        bottles: BottleClosingDepths,
        platform: str,
        cast: str,
        operator: str,
        station: str,
        depth: str,
        autostart: bool = False,
    ) -> bool:
        """
        Writes custom metadata and water bottle depths to SeasavePsa.

        Parameters
        ----------
        current_filename: Path
            The file name of the new file
        bottles: BottleClosingDepths
            The water bottle information
        platform: str
            CTD platform descriptor
        cast: str
            CTD cast number
        operator: str
            The name of the CTD operator
        station: str
            The DSHIP station information
        downcast: bool = True
            Whether to close water bottles on downcast
        autostart: bool = True
            Whether to skip confirmations inside seasave and just run

        Returns
        -------
        Whether opereration has been successful.
        """
        # set psa values
        if self.path_to_psa == Path("."):
            logger.error(
                "No path to a .psa file given. Cannot run seasave without one."
            )
            return False
        psa = SeasavePsa(self.path_to_psa)
        psa.set_xmlcon_file_path(config.xmlcon)
        psa.set_hex_file_path(current_filename)
        psa.set_bottle_fire_info(
            bottle_info=bottles.data,
            number_of_bottles=bottles.number_of_bottles,
        )
        psa.adjust_plotting_axis_borders(depth)
        # write metadataheader
        MetadataHeader.build_metadata_header(
            psa=psa,
            platform=platform,
            cast=cast,
            operator=operator,
            pos_alias=station,
            autostart=autostart,
        )
        psa.to_xml()
        return True

    def set_seasave_command_line_parameters(
        self,
        downcast=True,
        autostart=False,
    ) -> list:
        """
        Builds command line argument list for usage in the run method.

        Parameters
        ----------
        downcast: bool = True
            Whether to close water bottles on downcast
        autostart: bool = True
            Whether to skip confirmations inside seasave and just run

        Returns
        -------
        A list of command line parameters.
        """
        parameters = []
        if autostart:
            parameters.append(f"-autostart={self.path_to_psa}")
        else:
            parameters.append(f"-p={self.path_to_psa}")
        if downcast:
            parameters.append("-autofireondowncast")
        return parameters
