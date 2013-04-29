def get_coord_box(centre_x, centre_y, distance):
    """Get the square boundary coordinates for a given centre and distance"""
    """Todo: return coordinates inside a circle, rather than a square"""
    return {
        'top_left': (centre_x - distance, centre_y + distance),
        'top_right': (centre_x + distance, centre_y + distance),
        'bottom_left': (centre_x - distance, centre_y - distance),
        'bottom_right': (centre_x + distance, centre_y - distance),
    }


UNIT_SCOUT = 1
UNIT_DESTROYER = 2
UNIT_BOMBER = 3
UNIT_CRUISER = 4
UNIT_STARBASE = 5


def fleet_ttb(unit_type, quantity, factories, is_techno=False, is_dict=False, stasis_enabled=False):
    """
    Calculate the time taken to construct a given fleet

    """

    unit_weights = {
        UNIT_SCOUT: 1,
        UNIT_DESTROYER: 13,
        UNIT_BOMBER: 10,
        UNIT_CRUISER: 85,
        UNIT_STARBASE: 1,
    }

    govt_weight = 80 if is_dict else 100
    prod_weight = 85 if is_techno else 100

    weighted_qty = unit_weights[unit_type] * quantity
    ttb = (weighted_qty * govt_weight * prod_weight) * (2 * factories)

    # TTB is 66% longer with stasis enabled
    return ttb + (ttb * 0.66) if stasis_enabled else ttb