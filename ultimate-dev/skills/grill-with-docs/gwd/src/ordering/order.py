class Order:
    def __init__(self, customer, items):
        self.customer = customer
        self.items = items
        self.fulfilment_state = None

def create_invoice(order):
    return {"order": order, "amount": 0}
