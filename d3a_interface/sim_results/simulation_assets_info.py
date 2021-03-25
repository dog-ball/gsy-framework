from typing import Dict, List

from d3a_interface.sim_results import is_finite_power_plant_node_type, is_prosumer_node_type
from d3a_interface.sim_results.results_abc import ResultsBaseClass
from d3a_interface.utils import scenario_representation_traversal


class SimulationAssetsInfo(ResultsBaseClass):
    FIELDS = ['number_of_house_type', 'avg_assets_per_house', 'number_of_load_type',
              'total_energy_demand_kwh', 'number_of_pv_type', 'total_energy_generated_kwh',
              'number_of_storage_type', 'total_energy_capacity_kwh', 'number_of_power_plant_type',
              'max_power_plant_power_kw']

    def __init__(self):
        self.assets_info = {field: 0 for field in SimulationAssetsInfo.FIELDS}

    @staticmethod
    def merge_results_to_global(market_results: Dict, global_results: Dict, slot_list: List):
        pass

    def update(self, area_result_dict, core_stats, current_market_slot):
        updated_results_dict = {
            'number_of_load_type': 0,
            'total_energy_demand_kwh': 0,
            'number_of_pv_type': 0,
            'total_energy_generated_kwh': 0
        }
        for area_uuid, area_result in core_stats.items():
            if 'total_energy_demanded_wh' in area_result:
                updated_results_dict['number_of_load_type'] += 1
                updated_results_dict['total_energy_demand_kwh'] += \
                    area_result['total_energy_demanded_wh'] / 1000.0
            elif 'pv_production_kWh' in area_result:
                updated_results_dict['number_of_pv_type'] += 1
                updated_results_dict['total_energy_generated_kwh'] += \
                    area_result['pv_production_kWh']

            self.assets_info.update(updated_results_dict)

    def update_from_repr(self, area_representation: Dict):
        updated_results_dict = {
            'number_of_storage_type': 0,
            'total_energy_capacity_kwh': 0,
            'number_of_power_plant_type': 0,
            'max_power_plant_power_kw': 0
        }
        for area_dict, _ in scenario_representation_traversal(area_representation):
            if is_prosumer_node_type(area_dict):
                updated_results_dict['number_of_storage_type'] += 1
                updated_results_dict['total_energy_capacity_kwh'] +=\
                    area_dict.get('battery_capacity_kWh', 0)
            elif is_finite_power_plant_node_type(area_dict):
                updated_results_dict['number_of_power_plant_type'] += 1
                updated_results_dict['max_power_plant_power_kw'] +=\
                    area_dict.get('max_available_power_kW', 0)
            elif 'House':  # WIP
                pass
            self.assets_info.update(updated_results_dict)

    def restore_area_results_state(self, area_dict: Dict, last_known_state_data: Dict):
        pass

    @property
    def raw_results(self):
        return self.assets_info

    def memory_allocation_size_kb(self):
        return 0
