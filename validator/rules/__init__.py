from abc import ABC, abstractmethod
from typing import List
from validator.diagnostic import Diagnostic


CORE_BILLING_SOURCES = {
    'Account', 'CloudProvider', 'Region', 'Service',
    'UsageType', 'UsageFamily', 'Operation', 'Resource',
    'PricingTerm', 'Description', 'ProductFamily',
    'LineItemType', 'PayerAccount', 'UsageDay',
    'TransferType', 'RequestType', 'InvoiceID',
    'BillingConnectionID', 'CommittedUseSubscription',
    'PricingUnit', 'PricingUnits',
}

VALID_PREFIXES = ('CZ:Defined:', 'User:Defined:', 'Tag:', 'K8s:')

VALID_RULE_TYPES = {'Group', 'GroupBy', 'Metadata'}


class Rule(ABC):
    @abstractmethod
    def check(self, dimensions: dict, context: dict) -> List[Diagnostic]:
        """Check dimensions dict and return diagnostics.

        Args:
            dimensions: parsed YAML Dimensions dict (ruamel CommentedMap)
            context: metadata dict with keys:
                - filename: str
                - standalone: bool (suppress unresolved-user-defined)
                - raw_text: str (full file text for regex scans)
                - yaml_obj: the full parsed YAML object (for line numbers)
        """
        ...
