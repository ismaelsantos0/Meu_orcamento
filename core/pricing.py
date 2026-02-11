def apply_discount(subtotal: float, discount_type: str, discount_value: float):
    """
    Returns: (label, discount_amount, total)
    """
    desconto_valor = 0.0
    desconto_label = "—"

    if discount_type == "%":
        desconto_label = f"{discount_value:.2f}%"
        desconto_valor = subtotal * (discount_value / 100.0)
    elif discount_type == "R$":
        desconto_label = "R$"
        desconto_valor = min(discount_value, subtotal)

    total = max(0.0, subtotal - desconto_valor)
    return desconto_label, float(desconto_valor), float(total)
