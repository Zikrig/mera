#calculations.py

def calculate_total(data):
    total = 0
    
    # Расчет базовой стоимости
    apartment_type = data["apartment_type"]
    area = data["area"]
    
    if apartment_type in ["с ремонтом", "вайт бокс"]:
        if area <= 40:
            total += 6000
        else:
            total += 6000 + (area - 40) * 150
    elif apartment_type == "в бетоне":
        if area <= 40:
            total += 6000
        else:
            total += 6000 + (area - 40) * 130
    
    # Дополнительные услуги
    if data["em_screening"]:
        total += 250
    
    if data["radiation_check"]:
        total += 250
    
    measurement_type = data["measurement_type"]
    if measurement_type == "regular":
        total += data["area"] * 25
    elif measurement_type == "archicad":
        total += data["area"] * 100
    
    if data["valuation"]:
        total += 4000
    
    return total