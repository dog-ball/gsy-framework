from enum import Enum


class BidOfferMatchAlgoEnum(Enum):
    PAY_AS_BID = 1
    PAY_AS_CLEAR = 2
    EXTERNAL = 3
    BEST_PAB = 4
    BEST_PAC = 5
    BEST = 6


class SpotMarketTypeEnum(Enum):
    ONE_SIDED = 1
    TWO_SIDED = 2
