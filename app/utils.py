def check_screening_to_long(data):
    if data["apartment_type"] in ["в бетоне", "вайт бокс"]:
        return False
    
    if data["measurement_type"] == "archicad":
        return False
    return True

def continuety(data):
    if check_screening_to_long(data):
        return 4
    return 3
