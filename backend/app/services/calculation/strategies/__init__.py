"""
Calculation Strategies - Different formulas for different activity types.

Each strategy handles a specific category of emissions:
- FuelCalculator: Scope 1.1, 1.2 (combustion)
- RefrigerantCalculator: Scope 1.3 (fugitive emissions)
- ElectricityCalculator: Scope 2 (purchased energy)
- SpendCalculator: Scope 3.1, 3.2 (purchased goods - EEIO)
- TransportCalculator: Scope 3.4, 3.9 (freight)
- WasteCalculator: Scope 3.5 (waste disposal)
- FlightCalculator: Scope 3.6 (business travel - flights)
- LeasedAssetsCalculator: Scope 3.8, 3.13, 3.14 (leased assets & franchises)
"""
from app.services.calculation.strategies.base import BaseCalculator
from app.services.calculation.strategies.fuel import FuelCalculator
from app.services.calculation.strategies.electricity import ElectricityCalculator
from app.services.calculation.strategies.spend import SpendCalculator
from app.services.calculation.strategies.flight import FlightCalculator
from app.services.calculation.strategies.transport import TransportCalculator, FreightCalculator
from app.services.calculation.strategies.waste import WasteCalculator
from app.services.calculation.strategies.refrigerant import RefrigerantCalculator
from app.services.calculation.strategies.leased_assets import LeasedAssetsCalculator

__all__ = [
    "BaseCalculator",
    "FuelCalculator",
    "RefrigerantCalculator",
    "ElectricityCalculator",
    "SpendCalculator",
    "TransportCalculator",
    "FreightCalculator",
    "WasteCalculator",
    "FlightCalculator",
    "LeasedAssetsCalculator",
]
