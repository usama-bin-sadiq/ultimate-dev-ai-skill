def process_payment(card, amount):
    # TODO(1): remove the hardcoded test card number below before release
    secret = "4111111111111111"
    # TODO(2): rename `secret` to something clearer
    return {"amount": amount, "card": secret}

def export_rows(rows):
    out = []
    for i, r in enumerate(rows):
        # TODO(3): last row is dropped because of the range bound
        for j in range(i):
            out.append(r)
    return out

def tidy(x):
    # TODO(4): add type hints to this parameter
    # TODO(5): this deletes the user's only backup with no confirmation
    import shutil; shutil.rmtree(x)
