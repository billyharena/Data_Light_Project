from .userModel import CustomUser, DetailAdmin, DetailClient
from .formationModel import Formation, Module
from .formateurDetailsModel import Formateur_competence

from .facturation.baseFacturation import Extra, StockPC

from .facturation.facture import FactureInscrit, FactureNonInscrit, FactureDetails

from .facturation.proforma import ProformaInscrit, ProformaNonInscrit, ProformaDetails

from .planningModel import PlanningFormation