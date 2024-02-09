import server.orchestrator.use_situations as use_situations_module
from server.common import ServerBoxException, ErrorCode
from datetime import datetime
import threading
import logging

logger = logging.getLogger(__name__)

ENERGY_LIMITATIONS = ["100%", "25%", "0%"]


class OrchestratorEnergyLimitations:
    """OrchestratorEnergyLimitations service"""

    # Attributes
    current_energy_limitations: str
    zone: str
    energy_supplier: str
    energy_contract_class: str

    def init_energy_limitations_module(
        self, zone: str, energy_supplier: str, energy_contract_class: str
    ):
        """Initialize the energy limitations module"""
        logger.info("initializing Orchestrator energy limitations module")
        self.current_energy_limitations = "100%"
        self.zone = zone
        self.energy_supplier = energy_supplier
        self.energy_contract_class = energy_contract_class

    def get_current_energy_limitations(self):
        """Return the current energy limitations"""
        return self.current_energy_limitations

    def set_energy_limitations(self, energy_limitation: str):
        """Set energy limitations"""
        if energy_limitation not in ENERGY_LIMITATIONS:
            logger.error("Invalid energy limitation")
            return None
        self.current_energy_limitations = energy_limitation

        # Update ressources with new energy limitiation
        current_use_situation = (
            use_situations_module.orchestrator_use_situations_service.get_current_use_situation()
        )
        use_situations_module.orchestrator_use_situations_service.set_use_situation(
            use_situation=current_use_situation
        )
        return self.current_energy_limitations

    def manage_energy_recommendation(
        self,
        recomendation_datetime: datetime,
        sender: str,
        msg_id: str,
        msg_title: str,
        id_zone: str,
        id_energy_supplier: str,
        recommendation_class: str,
        power: str,
        start_datetime: datetime = None,
        end_datetime: datetime = None,
    ):
        """Set energy limitations"""

        # Validate dates
        _set_recommendation_end = False
        if recomendation_datetime is None:
            raise ServerBoxException(ErrorCode.INVALID_ENERGY_RECOMMENDATION_DATETIME)

        # Get current time
        now = datetime.now()

        if start_datetime is not None and end_datetime is not None:
            if start_datetime >= end_datetime or end_datetime < now:
                raise ServerBoxException(
                    ErrorCode.INVALID_ENERGY_RECOMMENDATION_DATETIME
                )
            _set_recommendation_end = True

        # Validate recommendation and contract
        if (
            self.zone != id_zone
            or self.energy_supplier != id_energy_supplier
            or self.energy_contract_class != recommendation_class
        ):
            raise ServerBoxException(ErrorCode.INVALID_ENERGY_RECOMMENDATION_ARGS)

        energy_limitation = f"{power}%"

        # Program energy recommendation start
        # TODO: test
        if start_datetime is not None:
            if start_datetime > now:
                _start_recomendation_in_secs = (start_datetime - now).seconds

                logger.info(
                    f"Schedule start of the energy limitation in {_start_recomendation_in_secs} secs"
                )
                recommendation_start_timer = threading.Timer(
                    _start_recomendation_in_secs,
                    orchestrator_energy_limitations_service.set_energy_limitations(
                        energy_limitation=energy_limitation
                    ),
                )
                recommendation_start_timer.start()

        # Set energy recommendation start now
        else:
            orchestrator_energy_limitations_service.set_energy_limitations(
                energy_limitation=energy_limitation
            )

        # Schedule energy recommendation end
        if _set_recommendation_end:
            _end_in_secs = (end_datetime - now).seconds

            logger.info(f"Schedule end of the energy limitation in {_end_in_secs} secs")
            recommendation_end_timer = threading.Timer(
                _end_in_secs, self.set_end_of_energy_recommendation_end
            )
            recommendation_end_timer.start()

    def set_end_of_energy_recommendation_end(self):
        """Set energy recommendation end"""
        logger.info(f"Setting end of energy recommendation")

        # Set energy recommendation
        orchestrator_energy_limitations_service.set_energy_limitations(
            energy_limitation="100%"
        )

        # Update ressources
        current_use_situation = (
            use_situations_module.orchestrator_use_situations_service.get_current_use_situation()
        )
        use_situations_module.orchestrator_use_situations_service.set_use_situation(
            use_situation=current_use_situation
        )


orchestrator_energy_limitations_service: OrchestratorEnergyLimitations = (
    OrchestratorEnergyLimitations()
)
""" OrchestratorCommands service singleton"""
