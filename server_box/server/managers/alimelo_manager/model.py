class AlimeloRessources:
    """Alimelo ressources model"""

    busvoltage: float
    shuntvoltage: float
    loadvoltage: float
    current_mA: float
    power_mW: float
    batLevel: float
    electricSocketIsPowerSupplied: bool
    isPowredByBattery: bool
    isChargingBattery: bool

    def __init__(
        self,
        busvoltage: float,
        shuntvoltage: float,
        loadvoltage: float,
        current_mA: float,
        power_mW: float,
        batLevel: float,
        electricSocketIsPowerSupplied: bool,
        isPowredByBattery: bool,
        isChargingBattery: bool,
    ):
        self.busvoltage = busvoltage
        self.shuntvoltage = shuntvoltage
        self.loadvoltage = loadvoltage
        self.current_mA = current_mA
        self.power_mW = power_mW
        self.batLevel = batLevel
        self.electricSocketIsPowerSupplied = electricSocketIsPowerSupplied
        self.isPowredByBattery = isPowredByBattery
        self.isChargingBattery = isChargingBattery
