from simply import market, market_2pac, market_fair
from simply import power_network
from simply.actor import Order
from simply.config import Config

from gsy_framework.matching_algorithms import BaseMatchingAlgorithm

from abc import ABC, abstractmethod
from argparse import ArgumentParser
import json


# default config
Config('')


ENERGY_UNIT_CONVERSION_FACTOR = 1000  # simply: kW, D3A: MW


def accept_orders(market, time, orders):
    # generate simply Order, put it into market including predefined order IDs
    # apply conversion factor except for market maker orders
    for bid in orders["bids"]:
        energy = min(bid["energy"] * ENERGY_UNIT_CONVERSION_FACTOR, 2 ** 63 - 1)
        cluster = (bid.get("attributes") or {}).get("cluster")
        order = Order(-1, time, bid["buyer"], cluster, energy, bid["energy_rate"])
        market.accept_order(order, order_id=bid["id"])
    for ask in orders["offers"]:
        energy = min(ask["energy"] * ENERGY_UNIT_CONVERSION_FACTOR, 2 ** 63 - 1)
        cluster = (ask.get("attributes") or {}).get("cluster")
        order = Order(1, time, ask["seller"], cluster, energy, ask["energy_rate"])
        market.accept_order(order, order_id=ask["id"])


def generate_recommendations(market_id, time, bids, asks, matches):
    recommendations = []

    for match in matches:
        recommendations.append({
            "market_id": market_id,
            "time_slot": time,
            'matching_requirements': None,
            "bid": bids[match["bid_id"]],
            "offer": asks[match["ask_id"]],
            "selected_energy": match["energy"] / ENERGY_UNIT_CONVERSION_FACTOR,
            "trade_rate": match["price"],
        })

    return recommendations


class MatchingAlgorithm(ABC):
    @staticmethod
    def get_market_matches(matching_data, market):
        """
        Unpacks order dictionary per market and time slot
        and match the orders using the given market.

        :param matching_data: hierarchical dictionary with market name and time slot each containing
        a dict with bids and offers in lists {'bids': []], 'offers': []}
        :param market: Market object that implements the matching algorithm
        :return: list of dictionaries with matches in all given markets and time slots
        """
        recommendations = []

        for market_id, market_name in matching_data.items():
            for time, orders in market_name.items():
                m = market(time=time)
                bids = {bid["id"]: bid for bid in orders["bids"]}
                asks = {ask["id"]: ask for ask in orders["offers"]}

                accept_orders(m, time, orders)
                matches = m.match()

                recommendations += generate_recommendations(market_id, time, bids, asks, matches)

        return recommendations

    @abstractmethod
    def get_matches_recommendations(cls, matching_data):
        pass


class BestPayAsBidMatchingAlgorithm(MatchingAlgorithm):
    """
    Wrapper class for the pay as bid matching algorithm
    """

    @classmethod
    def get_matches_recommendations(cls, matching_data):
        return super().get_market_matches(matching_data, market.Market)


class BestPayAsClearMatchingAlgorithm(MatchingAlgorithm):
    """
    Wrapper class for the pay as clear matching algorithm
    """

    @classmethod
    def get_matches_recommendations(cls, matching_data):
        return super().get_market_matches(matching_data, market_2pac.TwoSidedPayAsClear)


class BestClusterPayAsClearMatchingAlgorithm(MatchingAlgorithm):
    """
    Wrapper class of the cluster-based market fair matching algorithm
    """

    @classmethod
    def get_matches_recommendations(cls, matching_data):
        pn = power_network.create_random(1)
        recommendations = []

        for market_id, market_name in matching_data.items():
            for time, orders in market_name.items():
                actors = [bid["id"] for bid in orders["bids"]] + \
                         [ask["id"] for ask in orders["offers"]]
                # Give actors a position in the network
                # Currently at a single node with id 0
                actor_nodes = [0 for i in actors]
                map_actors = {actor: node_id for actor, node_id in zip(actors, actor_nodes)}
                pn.add_actors_map(map_actors)

                m = market_fair.BestMarket(time=time, network=pn)
                bids = {bid["id"]: bid for bid in orders["bids"]}
                asks = {ask["id"]: ask for ask in orders["offers"]}

                accept_orders(m, time, orders)
                matches = m.match()

                recommendations += generate_recommendations(market_id, time, bids, asks,
                                                            matches)

        return recommendations
